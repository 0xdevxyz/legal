import { Search, Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <main className="min-h-screen bg-gray-900 text-white flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-6">
          <span className="text-8xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            404
          </span>
        </div>
        <h1 className="text-2xl font-bold mb-3">Seite nicht gefunden</h1>
        <p className="text-gray-400 mb-8">
          Die angeforderte Seite existiert nicht oder wurde verschoben.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            <Home className="w-4 h-4" />
            Zum Dashboard
          </a>
          <a
            href="javascript:history.back()"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Zurueck
          </a>
        </div>
      </div>
    </main>
  )
}
