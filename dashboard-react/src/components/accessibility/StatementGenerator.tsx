'use client';

import { useState, FormEvent } from 'react';
import { apiClient } from '@/lib/api';
import { generateSiteId, isValidSiteId } from '@/lib/siteIdUtils';
import { Download, Printer, FileText, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

// =============================================================================
// Types — matching Plan 02-01 backend contract exactly
// =============================================================================

interface GenerateStatementRequest {
  site_id: string;
  site_url?: string;
  contact_email?: string;
  review_date?: string;
}

interface GenerateStatementResponse {
  html: string;
  markdown: string;
  filename: string;
}

// =============================================================================
// StatementGenerator Component
// =============================================================================

export default function StatementGenerator() {
  const [siteUrl, setSiteUrl] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [reviewDate, setReviewDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [generated, setGenerated] = useState<GenerateStatementResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [siteIdError, setSiteIdError] = useState<string | null>(null);

  // -----------------------------------------------------------------------
  // Submit handler — calls POST /api/v2/accessibility/generate-statement
  // -----------------------------------------------------------------------
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSiteIdError(null);

    // Client-side validation: check that siteUrl yields a valid site_id
    const computedSiteId = generateSiteId(siteUrl);
    if (computedSiteId === 'unknown-site' || !isValidSiteId(computedSiteId)) {
      setSiteIdError(
        'Ungültige Website-URL. Bitte geben Sie eine vollständige URL ein (z.B. https://www.example.de).'
      );
      return;
    }

    setLoading(true);
    try {
      const payload: GenerateStatementRequest = {
        site_id: computedSiteId,
        site_url: siteUrl || undefined,
        contact_email: contactEmail || undefined,
        review_date: reviewDate || undefined,
      };
      const { data } = await apiClient.post<GenerateStatementResponse>(
        '/api/v2/accessibility/generate-statement',
        payload
      );
      setGenerated(data);
    } catch (err: any) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (status === 401) {
        setError('Sitzung abgelaufen. Bitte erneut anmelden.');
      } else if (status === 403) {
        setError('Accessibility-Modul nicht aktiviert für diesen Account.');
      } else {
        setError(detail || 'Fehler beim Generieren der Erklärung.');
      }
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------------------------------------
  // HTML download — Blob + anchor click pattern from ComplianceIssueCard.tsx
  // -----------------------------------------------------------------------
  const handleDownloadHTML = () => {
    if (!generated) return;
    const blob = new Blob([generated.html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = generated.filename || 'barrierefreiheitserklaerung.html';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // -----------------------------------------------------------------------
  // PDF export via window.print() — zero new dependencies
  // -----------------------------------------------------------------------
  const handleExportPDF = () => {
    if (!generated) return;
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      setError('Popup-Blocker verhindert PDF-Export. Bitte Popups erlauben.');
      return;
    }
    printWindow.document.open();
    printWindow.document.write(generated.html);
    printWindow.document.close();
    printWindow.focus();
    // Defer print() until the document is fully parsed
    setTimeout(() => printWindow.print(), 250);
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Barrierefreiheitserklärung generieren
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Erstellen Sie eine BFSG-konforme Barrierefreiheitserklärung für Ihre Website.{' '}
          <a
            href="https://www.bfsg.de/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Mehr über das BFSG
          </a>
        </p>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg p-6 space-y-4">
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {/* Site URL */}
          <div>
            <label
              htmlFor="siteUrl"
              className="block text-sm font-medium text-gray-700"
            >
              Website-URL <span className="text-red-500">*</span>
            </label>
            <input
              id="siteUrl"
              type="url"
              required
              value={siteUrl}
              onChange={(e) => {
                setSiteUrl(e.target.value);
                setSiteIdError(null);
              }}
              placeholder="https://www.example.de"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {siteIdError && (
              <p className="mt-1 text-xs text-red-600">{siteIdError}</p>
            )}
          </div>

          {/* Contact Email */}
          <div>
            <label
              htmlFor="contactEmail"
              className="block text-sm font-medium text-gray-700"
            >
              Kontakt-E-Mail{' '}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              id="contactEmail"
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              placeholder="kontakt@example.de"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Review Date */}
          <div>
            <label
              htmlFor="reviewDate"
              className="block text-sm font-medium text-gray-700"
            >
              Datum der letzten Überprüfung
            </label>
            <input
              id="reviewDate"
              type="date"
              value={reviewDate}
              onChange={(e) => setReviewDate(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Submit button */}
          <div>
            <button
              type="submit"
              disabled={loading || !siteUrl}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Wird generiert...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4" />
                  Erklärung generieren
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Result section */}
      {generated && (
        <div className="space-y-4">
          {/* Success banner */}
          <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-600" />
            <p className="text-sm font-medium text-green-800">
              Erklärung erfolgreich generiert
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleDownloadHTML}
              className="inline-flex items-center gap-2 rounded-md bg-white border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <Download className="h-4 w-4" />
              HTML herunterladen
            </button>
            <button
              type="button"
              onClick={handleExportPDF}
              className="inline-flex items-center gap-2 rounded-md bg-white border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <Printer className="h-4 w-4" />
              PDF exportieren
            </button>
          </div>

          {/* Live preview — sandboxed iframe (defense in depth; backend uses Jinja2 autoescape) */}
          <div className="rounded-lg border border-gray-200 overflow-hidden">
            <div className="bg-gray-100 px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
              Vorschau
            </div>
            <iframe
              srcDoc={generated.html}
              title="Vorschau Barrierefreiheitserklärung"
              className="w-full h-[600px] border-0 bg-white"
              sandbox=""
            />
          </div>
        </div>
      )}
    </div>
  );
}
