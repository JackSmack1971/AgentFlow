"use client";

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import ApiClient from '../lib/api.ts';
import { z } from 'zod';

class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

interface LoginPayload { email: string; password: string; otpCode?: string }
interface TokenResponse { access_token: string; refresh_token: string }

export interface AuthContextValue {
  accessToken: string | null;
  refreshToken: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  error: string | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
  otpCode: z.string().min(1).optional(),
});

function parseJwt(token: string): { exp?: number } {
  try {
    const base64 = token.split('.')[1];
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch {
    return {};
  }
}

function isExpired(token: string): boolean {
  const { exp } = parseJwt(token);
  return exp ? Date.now() >= exp * 1000 - 60000 : false;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clientRef = useRef(new ApiClient());

  useEffect(() => {
    const at = localStorage.getItem('accessToken');
    const rt = localStorage.getItem('refreshToken');
    if (at && rt) {
      setAccessToken(at);
      setRefreshToken(rt);
    }
  }, []);

  async function saveTokens(tokens: TokenResponse): Promise<void> {
    setAccessToken(tokens.access_token);
    setRefreshToken(tokens.refresh_token);
    localStorage.setItem('accessToken', tokens.access_token);
    localStorage.setItem('refreshToken', tokens.refresh_token);
  }

  const login = async (payload: LoginPayload): Promise<void> => {
    setLoading(true);
    try {
      const data = loginSchema.parse(payload);
      const tokens = (await (clientRef.current as any).request(
        '/auth/login',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        },
      )) as TokenResponse;
      await saveTokens(tokens);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw new AuthError(message);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async (): Promise<void> => {
    if (!refreshToken) throw new AuthError('Missing refresh token');
    try {
      const tokens = (await (clientRef.current as any).request(
        '/auth/refresh',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        },
      )) as TokenResponse;
      await saveTokens(tokens);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Refresh failed';
      setError(message);
      throw new AuthError(message);
    }
  };

  const logout = async (): Promise<void> => {
    if (!refreshToken) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setAccessToken(null);
      setRefreshToken(null);
      return;
    }
    try {
      await (clientRef.current as any).request('/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (err) {
      // ignore logout errors
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setAccessToken(null);
      setRefreshToken(null);
    }
  };

  useEffect(() => {
    const id = setInterval(() => {
      if (accessToken && isExpired(accessToken)) {
        refresh().catch(() => logout());
      }
    }, 60000);
    return () => clearInterval(id);
  }, [accessToken, refreshToken]);

  const value: AuthContextValue = {
    accessToken,
    refreshToken,
    login,
    logout,
    refresh,
    error,
    loading,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new AuthError('AuthContext not found');
  return ctx;
};

export default AuthProvider;
