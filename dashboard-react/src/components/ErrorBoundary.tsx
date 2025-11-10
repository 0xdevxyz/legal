'use client';

import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Strukturiertes Logging statt console.error
    this.logError(error, errorInfo);
    this.setState({ error, errorInfo });
  }

  logError(error: Error, errorInfo: React.ErrorInfo) {
    // TODO: Integration mit Sentry, LogRocket oder anderem Error-Tracking-Service
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 React Error Boundary');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Component Stack:', errorInfo.componentStack);
      console.groupEnd();
    } else {
      // In production: Send to error tracking service
      // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full">
            <div className="bg-gray-800 rounded-xl p-8 border-2 border-red-500/30 shadow-2xl">
              {/* Icon */}
              <div className="flex justify-center mb-6">
                <div className="bg-red-500/20 p-4 rounded-full">
                  <AlertTriangle className="w-12 h-12 text-red-400" />
                </div>
              </div>

              {/* Title */}
              <h1 className="text-3xl font-bold text-white text-center mb-4">
                ⚠️ Ein Fehler ist aufgetreten
              </h1>

              {/* Description */}
              <p className="text-gray-300 text-center mb-6">
                Es tut uns leid, aber etwas ist schiefgelaufen. Bitte laden Sie die Seite neu oder kehren Sie zur Startseite zurück.
              </p>

              {/* Error Details (nur in Development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="mb-6 bg-gray-900 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-red-400 font-semibold mb-2 text-sm">
                    Fehlerdetails (nur in Development sichtbar):
                  </h3>
                  <div className="text-xs text-gray-400 space-y-2">
                    <div>
                      <strong className="text-gray-300">Fehler:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-words text-red-300">
                        {this.state.error.message}
                      </pre>
                    </div>
                    {this.state.error.stack && (
                      <div>
                        <strong className="text-gray-300">Stack Trace:</strong>
                        <pre className="mt-1 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                    {this.state.errorInfo?.componentStack && (
                      <div>
                        <strong className="text-gray-300">Component Stack:</strong>
                        <pre className="mt-1 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={this.handleReset}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Erneut versuchen
                </Button>
                <Button
                  onClick={this.handleReload}
                  variant="secondary"
                  className="flex-1"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Seite neu laden
                </Button>
                <Button
                  onClick={this.handleGoHome}
                  variant="outline"
                  className="flex-1"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Zur Startseite
                </Button>
              </div>

              {/* Support Info */}
              <div className="mt-6 pt-6 border-t border-gray-700">
                <p className="text-sm text-gray-400 text-center">
                  Wenn das Problem weiterhin besteht, kontaktieren Sie bitte unseren{' '}
                  <a
                    href="mailto:support@complyo.tech"
                    className="text-blue-400 hover:text-blue-300 underline"
                  >
                    Support
                  </a>
                  .
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

/**
 * Lightweight Error Boundary für kleinere Bereiche
 */
export class SectionErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Section Error:', error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-900/20 border-2 border-red-500/30 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-400 mb-2">
                Fehler in diesem Bereich
              </h3>
              <p className="text-gray-300 text-sm mb-4">
                Dieser Abschnitt konnte nicht geladen werden. Die restliche Seite funktioniert weiterhin.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-xs text-gray-400 mb-4">
                  <summary className="cursor-pointer hover:text-gray-300 mb-2">
                    Fehlerdetails anzeigen
                  </summary>
                  <pre className="whitespace-pre-wrap break-words bg-gray-900 p-3 rounded">
                    {this.state.error.message}
                  </pre>
                </details>
              )}
              <Button
                size="sm"
                variant="secondary"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Seite neu laden
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

