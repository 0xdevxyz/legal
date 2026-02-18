'use client';

import { useState, useEffect } from 'react';
import { Settings, Mail, Bell, Clock, Save, Loader2 } from 'lucide-react';
import { getAlertSettings, updateAlertSettings, type AlertSettings as AlertSettingsType } from '@/lib/ai-compliance-api';

export default function AlertSettings() {
  const [settings, setSettings] = useState<AlertSettingsType>({
    email_on_compliance_drop: true,
    email_on_high_risk: true,
    email_on_scan_reminder: true,
    email_on_scan_completed: false,
    compliance_drop_threshold: 10,
    scan_reminder_days: 30,
    inapp_notifications: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getAlertSettings();
      setSettings(data);
    } catch (err) {
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateAlertSettings(settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Error saving settings:', err);
      alert('Fehler beim Speichern');
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof AlertSettingsType) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (loading) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-48" />
          <div className="h-10 bg-gray-700 rounded" />
          <div className="h-10 bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-6 h-6 text-purple-400" />
        <h2 className="text-xl font-bold text-white">Alert-Einstellungen</h2>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-4">
            <Mail className="w-4 h-4" />
            E-Mail-Benachrichtigungen
          </h3>
          <div className="space-y-3">
            <label className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700">
              <div>
                <span className="text-white">Bei Compliance-Score-Abfall</span>
                <p className="text-sm text-gray-400">Benachrichtigung wenn Score um {settings.compliance_drop_threshold}+ Punkte fällt</p>
              </div>
              <input
                type="checkbox"
                checked={settings.email_on_compliance_drop}
                onChange={() => handleToggle('email_on_compliance_drop')}
                className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700">
              <div>
                <span className="text-white">Bei Hochrisiko-Erkennung</span>
                <p className="text-sm text-gray-400">Sofortige Warnung bei high-risk oder prohibited Klassifizierung</p>
              </div>
              <input
                type="checkbox"
                checked={settings.email_on_high_risk}
                onChange={() => handleToggle('email_on_high_risk')}
                className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700">
              <div>
                <span className="text-white">Scan-Erinnerungen</span>
                <p className="text-sm text-gray-400">Erinnerung nach {settings.scan_reminder_days} Tagen ohne Scan</p>
              </div>
              <input
                type="checkbox"
                checked={settings.email_on_scan_reminder}
                onChange={() => handleToggle('email_on_scan_reminder')}
                className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
              />
            </label>

            <label className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700">
              <div>
                <span className="text-white">Bei abgeschlossenem Scan</span>
                <p className="text-sm text-gray-400">Bestätigung nach jedem automatischen Scan</p>
              </div>
              <input
                type="checkbox"
                checked={settings.email_on_scan_completed}
                onChange={() => handleToggle('email_on_scan_completed')}
                className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
              />
            </label>
          </div>
        </div>

        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-4">
            <Clock className="w-4 h-4" />
            Schwellwerte
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Compliance-Abfall-Schwelle (Punkte)
              </label>
              <input
                type="number"
                min="5"
                max="50"
                value={settings.compliance_drop_threshold}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  compliance_drop_threshold: parseInt(e.target.value) || 10 
                }))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Scan-Erinnerung nach (Tage)
              </label>
              <input
                type="number"
                min="7"
                max="90"
                value={settings.scan_reminder_days}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  scan_reminder_days: parseInt(e.target.value) || 30 
                }))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-4">
            <Bell className="w-4 h-4" />
            In-App-Benachrichtigungen
          </h3>
          <label className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700">
            <div>
              <span className="text-white">In-App-Benachrichtigungen aktivieren</span>
              <p className="text-sm text-gray-400">Zeigt Benachrichtigungen im Dashboard an</p>
            </div>
            <input
              type="checkbox"
              checked={settings.inapp_notifications}
              onChange={() => handleToggle('inapp_notifications')}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {saving ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : saved ? (
            <>
              <Save className="w-5 h-5" />
              Gespeichert!
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Einstellungen speichern
            </>
          )}
        </button>
      </div>
    </div>
  );
}
