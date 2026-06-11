import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'CMS Integration Guides | Complyo',
};

export default function CmsIntegrationPage() {
  const htmlSnippet = `<script src="https://api.complyo.de/api/widgets/cookie-compliance.js" data-site-id="IHRE-SITE-ID"></script>`;
  const phpSnippet = `wp_enqueue_script('complyo', 'https://api.complyo.de/api/widgets/cookie-compliance.js', [], null, true);`;

  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold dark:text-white text-gray-900 mb-4">CMS Integration Guides</h1>
          <p className="dark:text-zinc-400 text-gray-600 text-lg">
            Binden Sie das Complyo Cookie-Banner in Ihr CMS ein. Wählen Sie unten Ihre Plattform.
          </p>
        </div>

        <div className="space-y-10">
          {/* WordPress */}
          <section className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6">
            <h2 className="text-2xl font-bold dark:text-white text-gray-900 mb-3">WordPress</h2>
            <p className="dark:text-zinc-400 text-gray-600 mb-1">
              Fügen Sie das Script-Tag direkt im Theme-Editor oder via Plugin in den{' '}
              <code className="text-green-400 dark:bg-zinc-800 bg-gray-100 px-1 rounded">&lt;head&gt;</code> ein.
              Alternativ können Sie die PHP-Funktion in der{' '}
              <code className="text-green-400 dark:bg-zinc-800 bg-gray-100 px-1 rounded">functions.php</code> Ihres
              Child-Themes nutzen.
            </p>

            <p className="dark:text-zinc-500 text-gray-500 text-sm mt-4 mb-1">HTML (im Theme-Header):</p>
            <pre className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-4 text-sm text-green-400 overflow-x-auto my-3">
              <code>{htmlSnippet}</code>
            </pre>

            <p className="dark:text-zinc-500 text-gray-500 text-sm mt-4 mb-1">PHP (functions.php):</p>
            <pre className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-4 text-sm text-green-400 overflow-x-auto my-3">
              <code>{phpSnippet}</code>
            </pre>
          </section>

          {/* Shopify */}
          <section className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6">
            <h2 className="text-2xl font-bold dark:text-white text-gray-900 mb-3">Shopify</h2>
            <p className="dark:text-zinc-400 text-gray-600 mb-1">
              Navigieren Sie zu <strong className="dark:text-white text-gray-900">Online Store → Themes → Edit Code</strong>{' '}
              und fügen Sie das Snippet kurz vor dem schließenden{' '}
              <code className="text-green-400 dark:bg-zinc-800 bg-gray-100 px-1 rounded">&lt;/body&gt;</code>-Tag in{' '}
              <code className="text-green-400 dark:bg-zinc-800 bg-gray-100 px-1 rounded">theme.liquid</code> ein.
            </p>
            <pre className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-4 text-sm text-green-400 overflow-x-auto my-3">
              <code>{htmlSnippet}</code>
            </pre>
          </section>

          {/* Wix */}
          <section className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6">
            <h2 className="text-2xl font-bold dark:text-white text-gray-900 mb-3">Wix</h2>
            <p className="dark:text-zinc-400 text-gray-600 mb-1">
              Öffnen Sie den Wix Editor, gehen Sie zu{' '}
              <strong className="dark:text-white text-gray-900">Settings → Custom Code → Head</strong> und fügen Sie
              das Script-Tag dort ein. Wix lädt es automatisch auf jeder Seite.
            </p>
            <pre className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-4 text-sm text-green-400 overflow-x-auto my-3">
              <code>{htmlSnippet}</code>
            </pre>
          </section>

          {/* Squarespace */}
          <section className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6">
            <h2 className="text-2xl font-bold dark:text-white text-gray-900 mb-3">Squarespace</h2>
            <p className="dark:text-zinc-400 text-gray-600 mb-1">
              Gehen Sie in Squarespace zu{' '}
              <strong className="dark:text-white text-gray-900">Settings → Advanced → Code Injection → Header</strong>{' '}
              und fügen Sie das Snippet ein. Es wird seitenübergreifend geladen.
            </p>
            <pre className="dark:bg-zinc-800 bg-gray-100 rounded-lg p-4 text-sm text-green-400 overflow-x-auto my-3">
              <code>{htmlSnippet}</code>
            </pre>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t dark:border-zinc-800 border-gray-200 text-center dark:text-zinc-500 text-gray-500 text-sm">
          <a href="/dashboard" className="text-blue-400 hover:text-blue-300">
            ← Zurück zum Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
