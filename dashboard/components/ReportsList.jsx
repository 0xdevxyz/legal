import React, { useState, useEffect } from 'react';
import { getReports } from '../services/api';
import { Download, FileText, AlertTriangle } from 'lucide-react';

export default function ReportsList() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const reportsList = await getReports();
        setReports(reportsList);
      } catch (err) {
        setError('Fehler beim Abrufen der Berichte: ' + (err.message || 'Unbekannter Fehler'));
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchReports();
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
        <span className="ml-2 text-gray-400">Berichte werden geladen...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-900 text-red-200 p-4 rounded-md flex items-center">
        <AlertTriangle className="h-5 w-5 mr-2" />
        <span>{error}</span>
      </div>
    );
  }
  
  if (reports.length === 0) {
    return (
      <div className="text-center p-8 bg-gray-800 rounded-lg">
        <FileText className="h-12 w-12 mx-auto mb-4 text-gray-600" />
        <h3 className="text-lg font-medium text-gray-300">Keine Berichte gefunden</h3>
        <p className="mt-2 text-gray-400">
          Sie haben noch keine Compliance-Berichte generiert. Führen Sie einen Website-Scan durch und erstellen Sie Ihren ersten Bericht.
        </p>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-medium">Ihre Compliance-Berichte</h2>
      </div>
      
      <ul className="divide-y divide-gray-700">
        {reports.map((report) => (
          <li key={report.id} className="p-4 hover:bg-gray-750">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="p-2 rounded-md bg-indigo-900 text-indigo-300">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-white">
                    Bericht für {report.url?.replace(/(^\w+:|^)\/\//, '')}
                  </p>
                  <p className="text-xs text-gray-400">
                    Erstellt am {new Date(report.created_at).toLocaleDateString()} um{' '}
                    {new Date(report.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </p>
                </div>
              </div>
              
                href={report.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-sm text-indigo-400 hover:text-indigo-300"
              >
                <Download className="h-4 w-4 mr-1" />
                PDF herunterladen
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
