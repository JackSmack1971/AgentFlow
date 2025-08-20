'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../providers/auth-provider.ts';
import { handleLogin, loginSchema, type LoginValues } from './utils.ts';

export default function LoginPage(): JSX.Element {
  const { login, loading } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginValues): Promise<void> => {
    const msg = await handleLogin(values, login, (p) => router.push(p));
    setError(msg);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <input type="email" {...register('email')} placeholder="Email" />
      {errors.email && <div>{errors.email.message}</div>}
      <input type="password" {...register('password')} placeholder="Password" />
      {errors.password && <div>{errors.password.message}</div>}
      {error && <div>{error}</div>}
      <button type="submit" disabled={loading} className="border px-4 py-2">
        {loading ? 'Loading...' : 'Login'}
      </button>
    </form>
  );
}

