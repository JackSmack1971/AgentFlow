"""Security middleware using fastapi-guard for comprehensive threat protection."""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi_guard import FastAPIGuard
from ipaddress import ip_address, ip_network
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.settings import Settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware with penetration detection and rate limiting."""

    def __init__(self, app, settings: Settings):
        """Initialize security middleware with configuration."""
        super().__init__(app)
        self.settings = settings
        self.logger = self._setup_security_logger()

        # Initialize Redis for distributed security state
        self.redis = Redis.from_url(settings.redis_url)

        # Initialize FastAPI Guard with security configuration
        self.guard = FastAPIGuard(
            redis_url=settings.redis_url,
            rate_limit_per_minute=settings.security_rate_limit_per_minute,
            ban_after_attempts=settings.security_penetration_attempts_threshold,
            ban_duration_minutes=settings.security_ban_duration_minutes,
            enable_penetration_detection=True,
            enable_rate_limiting=True,
            enable_ip_filtering=self._is_production(),
        )

        # Parse development IP whitelist
        self.dev_ip_networks = self._parse_ip_whitelist()

        self.logger.info(
            f"Security middleware initialized - Environment: {settings.environment}, "
            f"Rate limit: {settings.security_rate_limit_per_minute}/min, "
            f"Ban threshold: {settings.security_penetration_attempts_threshold} attempts"
        )

    def _setup_security_logger(self) -> logging.Logger:
        """Set up dedicated security logger."""
        logger = logging.getLogger("security")
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(self.settings.security_log_file), exist_ok=True)

        # File handler for security events
        file_handler = logging.FileHandler(self.settings.security_log_file)
        file_handler.setLevel(logging.INFO)

        # Formatter with security-specific format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - IP: %(ip)s - User-Agent: %(user_agent)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _is_production(self) -> bool:
        """Check if running in production environment."""
        return self.settings.environment.lower() == "prod"

    def _parse_ip_whitelist(self) -> List[Any]:
        """Parse IP whitelist for development environment."""
        networks = []
        for ip_range in self.settings.security_dev_ip_whitelist:
            try:
                if '/' in ip_range:
                    networks.append(ip_network(ip_range))
                else:
                    networks.append(ip_address(ip_range))
            except ValueError as e:
                self.logger.error(f"Invalid IP range in whitelist: {ip_range} - {e}")
        return networks

    def _is_ip_whitelisted(self, client_ip: str) -> bool:
        """Check if client IP is in development whitelist."""
        if self._is_production():
            return False

        try:
            client_addr = ip_address(client_ip)
            for network in self.dev_ip_networks:
                if isinstance(network, ip_network):
                    if client_addr in network:
                        return True
                elif isinstance(network, ip_address):
                    if client_addr == network:
                        return True
        except ValueError:
            pass
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header first (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Fall back to direct connection IP
            client_ip = request.client.host if request.client else "unknown"

        return client_ip

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through security middleware."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")

        # Skip security checks for whitelisted IPs in development
        if self._is_ip_whitelisted(client_ip):
            return await call_next(request)

        # Add security context to request state
        request.state.client_ip = client_ip
        request.state.user_agent = user_agent

        try:
            # Check rate limiting and penetration detection
            is_allowed, security_info = await self._check_security(request)

            if not is_allowed:
                # Log security violation
                await self._log_security_event(
                    "SECURITY_VIOLATION",
                    client_ip,
                    user_agent,
                    security_info,
                    request.url.path,
                    request.method
                )

                # Return appropriate error response
                if security_info.get("reason") == "rate_limited":
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests. Please try again later.",
                            "retry_after": security_info.get("retry_after", 60)
                        },
                        headers={"Retry-After": str(security_info.get("retry_after", 60))}
                    )
                else:  # banned
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Access denied due to suspicious activity.",
                            "ban_duration_minutes": self.settings.security_ban_duration_minutes
                        }
                    )

            # Log successful request (for audit trail)
            if request.url.path not in ["/health", "/docs", "/redoc", "/openapi.json"]:
                await self._log_security_event(
                    "REQUEST_ALLOWED",
                    client_ip,
                    user_agent,
                    {"method": request.method, "path": request.url.path},
                    request.url.path,
                    request.method
                )

            # Process request
            response = await call_next(request)

            # Add security headers to response
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"

            return response

        except Exception as e:
            # Log unexpected errors
            await self._log_security_event(
                "SECURITY_ERROR",
                client_ip,
                user_agent,
                {"error": str(e)},
                request.url.path,
                request.method
            )
            # Continue processing request despite security middleware errors
            return await call_next(request)

    async def _check_security(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """Check rate limiting and penetration detection."""
        client_ip = request.state.client_ip

        try:
            # Check if IP is currently banned
            ban_key = f"security:ban:{client_ip}"
            is_banned = await self.redis.exists(ban_key)

            if is_banned:
                ban_ttl = await self.redis.ttl(ban_key)
                return False, {
                    "reason": "banned",
                    "ban_remaining_seconds": ban_ttl
                }

            # Check rate limiting
            rate_limit_key = f"security:rate_limit:{client_ip}"
            current_count = await self.redis.get(rate_limit_key)

            if current_count is None:
                await self.redis.setex(rate_limit_key, 60, 1)  # 1 minute window
                current_count = 1
            else:
                current_count = int(current_count)

            if current_count >= self.settings.security_rate_limit_per_minute:
                retry_after = await self.redis.ttl(rate_limit_key)
                return False, {
                    "reason": "rate_limited",
                    "retry_after": retry_after,
                    "current_count": current_count
                }

            # Increment rate limit counter
            await self.redis.incr(rate_limit_key)

            # Check for suspicious patterns (penetration detection)
            suspicious_patterns = self._detect_suspicious_patterns(request)
            if suspicious_patterns:
                await self._handle_suspicious_activity(client_ip, suspicious_patterns, request)
                attempt_count = await self._increment_failed_attempts(client_ip)

                if attempt_count >= self.settings.security_penetration_attempts_threshold:
                    await self._ban_ip(client_ip)
                    return False, {
                        "reason": "banned",
                        "attempts": attempt_count,
                        "patterns": suspicious_patterns
                    }

                return False, {
                    "reason": "suspicious_activity",
                    "attempts": attempt_count,
                    "patterns": suspicious_patterns
                }

            return True, {}

        except Exception as e:
            self.logger.error(f"Security check error for {client_ip}: {e}")
            # Allow request to continue if security check fails
            return True, {"warning": "security_check_failed"}

    def _detect_suspicious_patterns(self, request: Request) -> List[str]:
        """Detect suspicious patterns in the request."""
        patterns = []
        path = request.url.path
        method = request.method
        headers = request.headers
        query_params = request.query_params

        # Common attack patterns
        if any(pattern in path.lower() for pattern in [
            "../", "..\\", "wp-admin", "wp-content", "admin.php", ".env", "config.json"
        ]):
            patterns.append("directory_traversal")

        if any(pattern in path.lower() for pattern in [
            "union", "select", "insert", "drop", "update", "delete", "--", "/*", "*/"
        ]):
            patterns.append("sql_injection")

        if any(pattern in path.lower() for pattern in [
            "<script", "javascript:", "onload=", "onerror=", "alert(", "eval("
        ]):
            patterns.append("xss_attempt")

        if method in ["TRACE", "CONNECT", "OPTIONS"] and path == "*":
            patterns.append("http_method_tunneling")

        if len(str(query_params)) > 1000:
            patterns.append("large_query_string")

        if any(header.lower().startswith("x-forwarded-") for header in headers.keys()):
            # Check for header injection attempts
            for header_value in headers.values():
                if len(str(header_value)) > 500:
                    patterns.append("large_header_value")
                if any(char in str(header_value) for char in ["\r", "\n", "\0"]):
                    patterns.append("header_injection")

        return patterns

    async def _handle_suspicious_activity(self, client_ip: str, patterns: List[str], request: Request):
        """Handle detected suspicious activity."""
        await self._log_security_event(
            "SUSPICIOUS_ACTIVITY",
            client_ip,
            request.headers.get("User-Agent", "unknown"),
            {"patterns": patterns, "path": request.url.path, "method": request.method},
            request.url.path,
            request.method
        )

    async def _increment_failed_attempts(self, client_ip: str) -> int:
        """Increment failed attempts counter for IP."""
        key = f"security:failed_attempts:{client_ip}"
        attempts = await self.redis.incr(key)
        # Reset counter after 1 hour if not banned
        await self.redis.expire(key, 3600)
        return attempts

    async def _ban_ip(self, client_ip: str):
        """Ban an IP address for the configured duration."""
        ban_key = f"security:ban:{client_ip}"
        ban_duration = self.settings.security_ban_duration_minutes * 60
        await self.redis.setex(ban_key, ban_duration, "banned")

        await self._log_security_event(
            "IP_BANNED",
            client_ip,
            "unknown",
            {"ban_duration_minutes": self.settings.security_ban_duration_minutes},
            "N/A",
            "N/A"
        )

    async def _log_security_event(self, event_type: str, client_ip: str, user_agent: str,
                                details: Dict[str, Any], path: str, method: str):
        """Log security event with structured data."""
        extra = {
            'ip': client_ip,
            'user_agent': user_agent,
            'event_type': event_type,
            'details': details,
            'path': path,
            'method': method,
            'timestamp': time.time()
        }

        if event_type in ["SECURITY_VIOLATION", "IP_BANNED"]:
            self.logger.warning(f"Security event: {event_type}", extra=extra)
        elif event_type == "SUSPICIOUS_ACTIVITY":
            self.logger.info(f"Security event: {event_type}", extra=extra)
        else:
            self.logger.info(f"Security event: {event_type}", extra=extra)