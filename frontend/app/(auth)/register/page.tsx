'use client';

import React, { useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import ApiClient from '../../../lib/api.ts';
import { registerSchema, type RegisterValues, registerUser, RegisterError } from './utils.ts';

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const clientRef = useRef<any>(new ApiClient());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (values: RegisterValues): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      await registerUser(values, clientRef.current);
      setSuccess('Registration successful');
      setTimeout(() => router.push('/login'), 1500);
    } catch (err) {
      const message = err instanceof RegisterError ? err.message : 'Registration failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <input type="email" {...register('email')} placeholder="Email" />
      {errors.email && <div>{errors.email.message}</div>}
      <input type="password" {...register('password')} placeholder="Password" />
      {errors.password && <div>{errors.password.message}</div>}
      <input type="password" {...register('confirmPassword')} placeholder="Confirm Password" />
      {errors.confirmPassword && <div>{errors.confirmPassword.message}</div>}
      {error && <div>{error}</div>}
      {success && <div>{success}</div>}
      <button type="submit" disabled={loading} className="border px-4 py-2">
        {loading ? 'Loading...' : 'Register'}
      </button>
    </form>
  );
}
