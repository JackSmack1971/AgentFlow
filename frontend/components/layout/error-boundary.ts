'use client';

import React from 'react';

export class LayoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LayoutError';
  }
}

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error): void {
    console.error(new LayoutError(error.message));
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return this.props.fallback || React.createElement('div', null, 'Something went wrong');
    }
    return this.props.children;
  }
}
