import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError: ((error: Error, errorInfo: ErrorInfo) => void) | undefined;
}

interface State {
  hasError: boolean;
  error: Error | undefined;
  errorInfo: ErrorInfo | undefined;
  errorId: string;
}

class WorkflowErrorBoundary extends Component<Props, State> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: this.generateErrorId()
    };
  }

  private generateErrorId(): string {
    return `workflow_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `workflow_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details for debugging
    console.error('Workflow Error Boundary caught an error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Update state with error info
    this.setState({
      error,
      errorInfo
    });

    // Report to error tracking service (if available)
    this.reportError(error, errorInfo);
  }

  private reportError(error: Error, errorInfo: ErrorInfo) {
    try {
      // In a real application, you would send this to your error tracking service
      // For now, we'll just log it with additional context
      const errorReport = {
        errorId: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        workflowContext: {
          // Add workflow-specific context here
          nodeCount: 0,
          edgeCount: 0,
          lastAction: 'unknown'
        }
      };

      // Store error report for debugging
      sessionStorage.setItem(`workflow_error_${this.state.errorId}`, JSON.stringify(errorReport));

      // In production, send to error tracking service
      if (process.env.NODE_ENV === 'production') {
        // Example: Sentry, LogRocket, etc.
        // Sentry.captureException(error, { contexts: { workflow: errorReport } });
      }
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  private handleRetry = () => {
    // Clear any existing retry timeout
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }

    // Reset error state
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: this.generateErrorId()
    });
  };

  private handleReset = () => {
    // Force a hard reset by reloading the workflow
    window.location.reload();
  };

  private handleExportError = () => {
    if (!this.state.error || !this.state.errorInfo) return;

    const errorReport = {
      errorId: this.state.errorId,
      message: this.state.error.message,
      stack: this.state.error.stack,
      componentStack: this.state.errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    const blob = new Blob([JSON.stringify(errorReport, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-error-${this.state.errorId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  override render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return React.createElement(
        'div',
        {
          className: 'flex flex-col items-center justify-center min-h-[400px] p-6 bg-red-50 border border-red-200 rounded-lg',
          role: 'alert',
          'aria-live': 'assertive'
        },
        [
          // Error Icon
          React.createElement(
            'div',
            {
              className: 'text-red-500 mb-4',
              'aria-hidden': 'true'
            },
            React.createElement('svg', {
              className: 'w-16 h-16',
              fill: 'none',
              stroke: 'currentColor',
              viewBox: '0 0 24 24'
            }, React.createElement('path', {
              strokeLinecap: 'round',
              strokeLinejoin: 'round',
              strokeWidth: 2,
              d: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z'
            }))
          ),

          // Error Title
          React.createElement(
            'h2',
            {
              className: 'text-xl font-semibold text-red-800 mb-2'
            },
            'Workflow Error'
          ),

          // Error Message
          React.createElement(
            'p',
            {
              className: 'text-red-600 text-center mb-4 max-w-md'
            },
            this.state.error?.message || 'An unexpected error occurred in the workflow editor.'
          ),

          // Error ID
          React.createElement(
            'p',
            {
              className: 'text-sm text-red-500 mb-6 font-mono'
            },
            `Error ID: ${this.state.errorId}`
          ),

          // Action Buttons
          React.createElement(
            'div',
            {
              className: 'flex flex-wrap gap-3 justify-center'
            },
            [
              React.createElement(
                'button',
                {
                  key: 'retry',
                  onClick: this.handleRetry,
                  className: 'px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                  type: 'button'
                },
                'Try Again'
              ),
              React.createElement(
                'button',
                {
                  key: 'reset',
                  onClick: this.handleReset,
                  className: 'px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
                  type: 'button'
                },
                'Reset Workflow'
              ),
              React.createElement(
                'button',
                {
                  key: 'export',
                  onClick: this.handleExportError,
                  className: 'px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
                  type: 'button'
                },
                'Export Error Report'
              )
            ]
          ),

          // Development Error Details
          process.env.NODE_ENV === 'development' && this.state.error?.stack && React.createElement(
            'details',
            {
              className: 'mt-6 p-4 bg-red-100 rounded max-w-2xl w-full',
              key: 'details'
            },
            [
              React.createElement(
                'summary',
                {
                  className: 'cursor-pointer font-medium text-red-800 mb-2',
                  key: 'summary'
                },
                'Error Details (Development Only)'
              ),
              React.createElement(
                'pre',
                {
                  className: 'text-xs text-red-700 whitespace-pre-wrap overflow-auto max-h-64',
                  key: 'stack'
                },
                this.state.error.stack
              )
            ]
          )
        ].filter(Boolean)
      );
    }

    return this.props.children;
  }

  override componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }
}

// Higher-order component for easier usage
export function withWorkflowErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  const WrappedComponent = (props: P) => React.createElement(
    WorkflowErrorBoundary,
    {
      fallback,
      onError,
      children: React.createElement(Component, props)
    }
  );

  WrappedComponent.displayName = `withWorkflowErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default WorkflowErrorBoundary;