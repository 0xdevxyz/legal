      setReportUrl(result.url);
    } catch (err) {
      setError('Fehler beim Generieren des Berichts: ' + (err.message || 'Unbekannter Fehler'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-start mb-4">
        <div className="p-2 rounded-md bg-indigo-900 text-indigo-300 mr-3">
          <FileText className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-medium mb-1">Compliance-Bericht generieren</h2>
          <p className="text-sm text-gray-400">
            Erstellen Sie einen detaillierten PDF-Bericht mit allen Compliance-Ergebnissen für {scanUrl}.
          </p>
        </div>
      </div>
      
      {error && (
        <div className="mb-4 p-3 bg-red-900 text-red-200 rounded-md flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      
      {success ? (
        <div className="mb-4 p-3 bg-green-900 text-green-200 rounded-md">
          <p className="mb-2">Bericht wurde erfolgreich generiert!</p>
          <a 
            href={reportUrl} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="inline-flex items-center text-white bg-green-700 px-4 py-2 rounded-md hover:bg-green-800"
          >
            <FileText className="h-4 w-4 mr-2" />
            PDF herunterladen
          </a>
        </div>
      ) : (
        <button
          onClick={handleGenerateReport}
          disabled={loading}
          className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
              Bericht wird erstellt...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4 mr-2" />
              PDF-Bericht generieren
            </>
          )}
        </button>
      )}
      
      <p className="mt-3 text-xs text-gray-400">
        {success ? 
          "Der Bericht enthält alle Compliance-Ergebnisse, Risikobewertungen und Handlungsempfehlungen." :
          "Der Bericht enthält detaillierte Analyseergebnisse, Risikobewertungen und konkrete Handlungsempfehlungen zur Optimierung Ihrer Website-Compliance."}
      </p>
    </div>
  );
}
