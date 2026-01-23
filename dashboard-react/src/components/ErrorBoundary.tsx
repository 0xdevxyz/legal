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
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      return (
        <div className="border-4 border-red-600 rounded-xl p-6 bg-red-50 m-4">
          <div className="flex items-start gap-4">
            <div className="text-4xl">🔴</div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-red-900 mb-2">
                Etwas ist schiefgelaufen
              </h2>
              
              <p className="text-red-800 mb-4 text-lg">
                {this.state.error.message || 'Ein unerwarteter Fehler ist aufgetreten.'}
              </p>
              
              <div className="bg-white border-2 border-red-300 rounded-lg p-4 mb-3">
                <p className="text-sm text-red-700 mb-2 font-semibold">
                  <strong>Was können Sie tun?</strong>
                </p>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1 mb-3">
                  <li>Seite neu laden (F5 oder Strg+R)</li>
                  <li>Browser-Cache leeren (Strg+Shift+Delete)</li>
                  <li>In einem anderen Browser versuchen</li>
                  <li>Support kontaktieren: <a href="mailto:support@complyo.tech" className="underline">support@complyo.tech</a></li>
                </ul>
                
                <button
                  onClick={() => window.location.reload()}
                  className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Seite neu laden
                </button>
              </div>
              
              {/* Technische Details nur für Entwickler */}
              {isDevelopment && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-red-600 font-semibold hover:text-red-800">
                    🔧 Technische Details (nur für Entwickler)
                  </summary>
                  
                  {this.props.componentName && (
                    <div className="bg-red-100 border-2 border-red-300 rounded-lg p-3 mt-2">
                      <p className="font-bold text-red-800 text-xs">
                        📍 Component: {this.props.componentName}
                      </p>
                    </div>
                  )}
                  
                  <div className="bg-white border-2 border-red-300 rounded-lg p-4 mt-2">
                    <p className="font-bold text-red-800 mb-2 text-xs">❌ Error Message:</p>
                    <pre className="text-xs text-red-700 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded">
                      {this.state.error.message}
                    </pre>
                  </div>

                  <div className="bg-white border-2 border-red-300 rounded-lg p-4 mt-2">
                    <p className="font-bold text-red-800 mb-2 text-xs">📚 Stack Trace:</p>
                    <pre className="text-xs text-red-600 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded max-h-96 overflow-auto">
                      {this.state.error.stack}
                    </pre>
                  </div>

                  {this.state.errorInfo && (
                    <div className="bg-white border-2 border-red-300 rounded-lg p-4 mt-2">
                      <p className="font-bold text-red-800 mb-2 text-xs">🧩 Component Stack:</p>
                      <pre className="text-xs text-red-600 whitespace-pre-wrap font-mono bg-red-50 p-3 rounded max-h-96 overflow-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
