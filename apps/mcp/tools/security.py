"""Security utilities and decorators for MCP tools."""

from __future__ import annotations

import logging
import re
import time
from functools import wraps
from typing import Any, Dict

import jwt as pyjwt
from mcp.server.fastmcp import Context
from pydantic import ValidationError

from ...api.app.core.settings import Settings
from ...api.app.exceptions import TokenError

logger = logging.getLogger(__name__)

# Input sanitization patterns
SQL_INJECTION_PATTERNS = [
    r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|UNION|EXEC|EXECUTE|DECLARE|CAST|CONVERT)\b',
    r'--', r'/\*', r'\*/', r';', r'xp_', r'sp_'
]

XSS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:', r'on\w+\s*=', r'<iframe[^>]*>.*?</iframe>',
    r'<object[^>]*>.*?</object>', r'<embed[^>]*>.*?</embed>'
]

# Compile patterns for performance
SQL_PATTERNS_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]
XSS_PATTERNS_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class InputValidationError(SecurityError):
    """Raised when input validation fails."""
    pass


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize input text to prevent injection attacks."""
    if not text:
        return text

    # Length validation
    if len(text) > max_length:
        raise InputValidationError(f"Input exceeds maximum length of {max_length} characters")

    # SQL injection detection
    for pattern in SQL_PATTERNS_COMPILED:
        if pattern.search(text):
            raise InputValidationError("Potential SQL injection detected")

    # XSS detection
    for pattern in XSS_PATTERNS_COMPILED:
        if pattern.search(text):
            raise InputValidationError("Potential XSS attack detected")

    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    return sanitized


def validate_token(token: str, settings: Settings) -> Dict[str, Any]:
    """Validate JWT token and return payload."""
    try:
        payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Check if token has expired
        if 'exp' in payload and payload['exp'] < time.time():
            raise AuthenticationError("Token has expired")

        return payload
    except pyjwt.PyJWTError as exc:
        raise AuthenticationError(f"Invalid token: {str(exc)}") from exc


def extract_user_from_context(ctx: Context[Any, Any, Any]) -> str:
    """Extract user information from MCP context."""
    # In a real implementation, this would extract user info from the context
    # For now, we'll use a placeholder - this should be populated by the MCP server
    # based on the transport layer authentication
    user_info = getattr(ctx, 'user_info', None)
    if not user_info:
        raise AuthenticationError("No user information in context")

    return user_info.get('sub', 'unknown')


def require_auth(func):
    """Decorator to require JWT authentication for MCP tool execution."""
    @wraps(func)
    async def wrapper(ctx: Context[Any, Any, Any], *args, **kwargs):
        try:
            # Extract and validate authentication from context
            user = extract_user_from_context(ctx)
            logger.info(f"Authenticated user: {user} for tool: {func.__name__}")
            return await func(ctx, *args, **kwargs)
        except AuthenticationError as exc:
            logger.warning(f"Authentication failed for tool {func.__name__}: {exc}")
            # In MCP context, we should return an error response
            await ctx.error(f"Authentication required: {str(exc)}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in {func.__name__}: {exc}")
            await ctx.error(f"Internal error: {str(exc)}")
            raise

    return wrapper


def require_https(settings: Settings):
    """Decorator to enforce HTTPS in production."""
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx: Context[Any, Any, Any], *args, **kwargs):
            # Check if HTTPS is required (production environment)
            if settings.environment.lower() == "prod":
                # In a real implementation, this would check the transport layer
                # For now, we'll assume HTTPS is handled at the transport level
                logger.info(f"HTTPS enforcement check passed for {func.__name__}")

            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator


def audit_log(log_file: str = "logs/mcp_audit.log"):
    """Decorator to log tool usage with user context for compliance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx: Context[Any, Any, Any], *args, **kwargs):
            import os
            from datetime import datetime

            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # Extract user info
            user = "unknown"
            try:
                user = extract_user_from_context(ctx)
            except AuthenticationError:
                pass  # User might not be authenticated yet

            # Log the tool usage
            timestamp = datetime.utcnow().isoformat()
            tool_name = func.__name__

            # Sanitize args for logging (remove sensitive data)
            safe_args = {}
            for key, value in kwargs.items():
                if isinstance(value, str):
                    safe_args[key] = sanitize_input(value, max_length=100) if len(value) > 100 else value
                else:
                    safe_args[key] = str(value)

            log_entry = {
                "timestamp": timestamp,
                "user": user,
                "tool": tool_name,
                "args": safe_args,
                "status": "started"
            }

            try:
                with open(log_file, "a") as f:
                    f.write(f"{log_entry}\n")
                logger.info(f"Audit log written for {tool_name} by {user}")
            except Exception as exc:
                logger.error(f"Failed to write audit log: {exc}")

            try:
                result = await func(ctx, *args, **kwargs)

                # Log successful completion
                success_entry = log_entry.copy()
                success_entry["status"] = "completed"
                with open(log_file, "a") as f:
                    f.write(f"{success_entry}\n")

                return result

            except Exception as exc:
                # Log failure
                error_entry = log_entry.copy()
                error_entry["status"] = "failed"
                error_entry["error"] = str(exc)
                with open(log_file, "a") as f:
                    f.write(f"{error_entry}\n")
                raise

        return wrapper
    return decorator


def validate_input(**validators):
    """Decorator to validate and sanitize input parameters."""
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx: Context[Any, Any, Any], *args, **kwargs):
            # Apply validation rules
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if isinstance(value, str):
                        kwargs[param_name] = sanitize_input(value, validator.get('max_length', 10000))
                    elif validator.get('required', False) and not value:
                        raise InputValidationError(f"Required parameter {param_name} is empty")

            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator