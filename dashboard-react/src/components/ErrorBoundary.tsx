'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🔴 ErrorBoundary caught error:', error);
    console.error('🔴 Component Stack:', errorInfo.componentStack);
    console.error('🔴 Error Stack:', error.stack);
    
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div className="border-4 border-red-600 rounded-xl p-6 bg-red-50 m-4">
          <div className="flex items-start gap-4">
            <div className="text-4xl">🔴</div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-red-900 mb-2">
                Component Error Gefunden! 🎯
              </h2>
              
              {this.props.componentName && (
                <div className="bg-red-100 border-2 border-red-300 rounded-lg p-3 mb-3">
                  <p className="font-bold text-red-800">
                    📍 Component: {this.props.componentName}
                  </p>
                </div>
              )}
              
              <div className="bg-white border-2 border-red-300 rounded-lg p-4 mb-3">
                <p className="font-bold text-red-800 mb-2">❌ Error Message:</p>
                <pre className="text-sm text-red-700 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded">
                  {this.state.error.message}
                </pre>
              </div>

              <div className="bg-white border-2 border-red-300 rounded-lg p-4 mb-3">
                <p className="font-bold text-red-800 mb-2">📚 Stack Trace:</p>
                <pre className="text-xs text-red-600 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded max-h-96 overflow-auto">
                  {this.state.error.stack}
                </pre>
              </div>

              {this.state.errorInfo && (
                <div className="bg-white border-2 border-red-300 rounded-lg p-4 mb-3">
                  <p className="font-bold text-red-800 mb-2">🧩 Component Stack:</p>
                  <pre className="text-xs text-red-600 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded max-h-96 overflow-auto">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}

              <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg p-3">
                <p className="text-sm text-yellow-900">
                  <strong>💡 Tipp:</strong> Mache einen Screenshot davon und schicke ihn mir!
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
