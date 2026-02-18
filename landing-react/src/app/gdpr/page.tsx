'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function GDPRDataManagement() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | ''>('');

  const handleDataDeletion = async () => {
    if (!email) {
      setMessage('Bitte geben Sie Ihre E-Mail-Adresse ein.');
      setMessageType('error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/gdpr/request-deletion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          reason: 'user_request',
          confirmation: true
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage('Ihre Daten werden gelöscht. Sie erhalten eine Bestätigungs-E-Mail.');
        setMessageType('success');
        setEmail('');
      } else {
        setMessage(data.message || 'Fehler beim Löschen der Daten.');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleDataExport = async () => {
    if (!email) {
      setMessage('Bitte geben Sie Ihre E-Mail-Adresse ein.');
      setMessageType('error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/gdpr/export-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage('Ihr Datenexport wird erstellt und per E-Mail versandt.');
        setMessageType('success');
        setEmail('');
      } else {
        setMessage(data.message || 'Fehler beim Erstellen des Datenexports.');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              🛡️ DSGVO Datenverwaltung
            </h1>
            <p className="text-xl text-gray-600">
              Verwalten Sie Ihre personenbezogenen Daten gemäß DSGVO
            </p>
          </div>

          {/* Message Display */}
          {message && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`mb-8 p-4 rounded-lg ${
                messageType === 'success' 
                  ? 'bg-green-100 border border-green-400 text-green-700'
                  : 'bg-red-100 border border-red-400 text-red-700'
              }`}
            >
              {message}
            </motion.div>
          )}

          {/* Email Input */}
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">
              E-Mail-Adresse eingeben
            </h2>
            <div className="flex flex-col sm:flex-row gap-4">
              <label htmlFor="gdpr-email" className="sr-only">E-Mail-Adresse für DSGVO-Anfrage</label>
              <input
                id="gdpr-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ihre.email@beispiel.de"
                aria-label="E-Mail-Adresse für DSGVO-Anfrage"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Data Deletion Section */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-xl shadow-lg p-8"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🗑️</span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                  Recht auf Löschung
                </h3>
                <p className="text-gray-600">
                  Artikel 17 DSGVO - „Recht auf Vergessenwerden"
                </p>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Was wird gelöscht?</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Ihre E-Mail-Adresse und Name</li>
                    <li>• Website-Analyse-Ergebnisse</li>
                    <li>• Alle E-Mail-Kommunikation</li>
                    <li>• Einwilligungsnachweis</li>
                    <li>• Technische Logs und Daten</li>
                  </ul>
                </div>
                
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>⚠️ Wichtig:</strong> Diese Aktion ist unwiderruflich. 
                    Alle Ihre Daten werden permanent gelöscht.
                  </p>
                </div>
              </div>
              
              <button
                onClick={handleDataDeletion}
                disabled={loading || !email}
                className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                {loading ? '⏳ Wird gelöscht...' : '🗑️ Daten löschen'}
              </button>
            </motion.div>

            {/* Data Export Section */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white rounded-xl shadow-lg p-8"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📥</span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                  Datenexport
                </h3>
                <p className="text-gray-600">
                  Artikel 20 DSGVO - „Recht auf Datenübertragbarkeit"
                </p>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Was erhalten Sie?</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Vollständige Datenübersicht (JSON)</li>
                    <li>• Persönliche Informationen</li>
                    <li>• Einwilligungshistorie</li>
                    <li>• Website-Analysedaten</li>
                    <li>• Technische Metadaten</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800">
                    <strong>ℹ️ Hinweis:</strong> Der Export wird per E-Mail 
                    im JSON-Format versendet.
                  </p>
                </div>
              </div>
              
              <button
                onClick={handleDataExport}
                disabled={loading || !email}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                {loading ? '⏳ Wird erstellt...' : '📥 Daten exportieren'}
              </button>
            </motion.div>
          </div>

          {/* GDPR Information Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 bg-gray-50 rounded-xl p-8"
          >
            <h3 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
              Ihre Rechte nach DSGVO
            </h3>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">📋</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Auskunft</h4>
                <p className="text-sm text-gray-600">Artikel 15 - Recht auf Auskunft</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">✏️</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Berichtigung</h4>
                <p className="text-sm text-gray-600">Artikel 16 - Recht auf Berichtigung</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">🗑️</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Löschung</h4>
                <p className="text-sm text-gray-600">Artikel 17 - Recht auf Löschung</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">📥</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Portabilität</h4>
                <p className="text-sm text-gray-600">Artikel 20 - Datenübertragbarkeit</p>
              </div>
            </div>
            
            <div className="mt-8 text-center">
              <p className="text-gray-600">
                Bei Fragen zu Ihren Datenschutzrechten wenden Sie sich an: 
                <a href="mailto:datenschutz@complyo.tech" className="text-blue-600 hover:underline ml-1">
                  datenschutz@complyo.tech
                </a>
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}