import React, { Suspense, type ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps): JSX.Element {
  const brand = process.env.NEXT_PUBLIC_BRAND_NAME;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Suspense fallback={<div>Loading...</div>}>
        <div className="w-full max-w-md space-y-6">
          {brand && (
            <div className="text-center text-2xl font-semibold">{brand}</div>
          )}
          {children}
        </div>
      </Suspense>
    </div>
  );
}
