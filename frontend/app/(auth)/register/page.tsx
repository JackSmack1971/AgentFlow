'use client';

import React, { useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import ApiClient from '../../../lib/api.ts';
import { registerSchema, type RegisterValues, registerUser, RegistrationError } from './utils.ts';

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const clientRef = useRef(new ApiClient());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (values: RegisterValues): Promise<void> => {
    try {
      await registerUser(clientRef.current, values);
      setSuccess('Registration successful');
      setTimeout(() => router.push('/login'), 1000);
    } catch (err) {
      const message = err instanceof RegistrationError ? err.message : 'Registration failed';
      setError(message);
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
      <button type="submit" disabled={isSubmitting} className="border px-4 py-2">
        {isSubmitting ? 'Loading...' : 'Register'}
      </button>
    </form>
  );
}
