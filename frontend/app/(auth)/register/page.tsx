'use client';

import React, { useRef, useState } from 'react';
import { useForm, type FieldErrors, type UseFormRegister } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import ApiClient from '../../../lib/api.ts';
import {
  registerSchema,
  type RegisterValues,
  registerUser,
  RegisterError,
  type Client,
} from './utils.ts';

interface FieldsProps {
  register: UseFormRegister<RegisterValues>;
  errors: FieldErrors<RegisterValues>;
  status: { error: string | null; success: string | null };
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

function Fields({ register, errors, status, loading, onSubmit }: FieldsProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input type="email" {...register('email')} placeholder="Email" />
      {errors.email && <div>{errors.email.message}</div>}
      <input type="password" {...register('password')} placeholder="Password" />
      {errors.password && <div>{errors.password.message}</div>}
      <input type="password" {...register('confirmPassword')} placeholder="Confirm Password" />
      {errors.confirmPassword && <div>{errors.confirmPassword.message}</div>}
      {status.error && <div>{status.error}</div>}
      {status.success && <div>{status.success}</div>}
      <button type="submit" disabled={loading} className="border px-4 py-2">
        {loading ? 'Loading...' : 'Register'}
      </button>
    </form>
  );
}

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const clientRef = useRef<Client>(new ApiClient() as unknown as Client);
  const [status, setStatus] = useState<{ error: string | null; success: string | null }>({ error: null, success: null });
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  const submit = async (values: RegisterValues): Promise<void> => {
    setLoading(true); setStatus({ error: null, success: null });
    try {
      await registerUser(values, clientRef.current);
      setStatus({ error: null, success: 'Registration successful' });
      setTimeout(() => router.push('/login'), 1500);
    } catch (err) {
      const message = err instanceof RegisterError ? err.message : 'Registration failed';
      setStatus({ error: message, success: null });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Fields register={register} errors={errors} status={status} loading={loading} onSubmit={handleSubmit(submit)} />
  );
}

