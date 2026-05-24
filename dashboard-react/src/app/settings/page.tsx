'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import {
  User, Bell, Shield, Key, Globe, Mail, Building,
  Save, CheckCircle, AlertCircle, Loader2, Eye, EyeOff,
  Trash2, Download, ToggleLeft, ToggleRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { safeStorage } from '@/lib/storage';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de';

type Tab = 'profil' | 'benachrichtigungen' | 'sicherheit' | 'datenschutz';

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'profil', label: 'Profil', icon: User },
  { id: 'benachrichtigungen', label: 'Benachrichtigungen', icon: Bell },
  { id: 'sicherheit', label: 'Sicherheit', icon: Shield },
  { id: 'datenschutz', label: 'Datenschutz', icon: Globe },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>('profil');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [profile, setProfile] = useState({
    full_name: user?.full_name ?? '',
    email: user?.email ?? '',
    company: user?.company ?? '',
  });

  const [notifications, setNotifications] = useState({
    email_legal_updates: true,
    email_scan_complete: true,
    email_weekly_report: false,
    browser_alerts: true,
  });

  const [passwords, setPasswords] = useState({
    current: '',
    next: '',
    confirm: '',
  });

  useEffect(() => {
    if (user) {
      setProfile({
        full_name: user.full_name ?? '',
        email: user.email ?? '',
        company: user.company ?? '',
      });
    }
  }, [user]);

  const getHeaders = () => ({
    Authorization: `Bearer ${safeStorage.get('access_token')}`,
    'Content-Type': 'application/json',
  });

  const showResult = (msg: string, isError = false) => {
    if (isError) { setError(msg); setSuccess(''); }
    else { setSuccess(msg); setError(''); }
    setTimeout(() => { setSuccess(''); setError(''); }, 4000);
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/user/profile`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ full_name: profile.full_name, company: profile.company }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? 'Fehler');
      showResult('Profil gespeichert.');
    } catch (e: any) {
      showResult(e.message ?? 'Fehler beim Speichern.', true);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/user/notifications`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(notifications),
      });
      if (!res.ok) throw new Error('Fehler');
      showResult('Benachrichtigungen gespeichert.');
    } catch {
      showResult('Einstellungen konnten nicht gespeichert werden.', true);
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwords.next !== passwords.confirm) {
      showResult('Passwörter stimmen nicht überein.', true);
      return;
    }
    if (passwords.next.length < 8) {
      showResult('Passwort muss mindestens 8 Zeichen haben.', true);
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/user/change-password`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ current_password: passwords.current, new_password: passwords.next }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? 'Fehler');
      setPasswords({ current: '', next: '', confirm: '' });
      showResult('Passwort erfolgreich geändert.');
    } catch (e: any) {
      showResult(e.message ?? 'Passwortänderung fehlgeschlagen.', true);
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/user/export-data`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Export fehlgeschlagen');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'complyo-daten-export.json';
      a.click();
      URL.revokeObjectURL(url);
      showResult('Daten-Export erfolgreich.');
    } catch {
      showResult('Export fehlgeschlagen. Bitte später versuchen.', true);
    }
  };

  const planLabel: Record<string, string> = {
    free: 'Kostenlos', single: 'Einzelne Säule', pro: 'Pro',
    agency: 'Agentur', expert: 'Expertenservice', update: 'Updateservice',
  };

  return (
    <main role="main" aria-label="Einstellungen" className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Einstellungen</h1>
          <p className="text-zinc-400 text-sm mt-1">Verwalten Sie Ihr Profil, Benachrichtigungen und Datenschutz-Optionen.</p>
        </div>

        {/* Feedback */}
        {success && (
          <div className="mb-6 flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
            <CheckCircle className="w-4 h-4 shrink-0" />
            {success}
          </div>
        )}
        {error && (
          <div className="mb-6 flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <aside className="lg:w-52 shrink-0">
            <nav className="flex flex-row lg:flex-col gap-1">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors w-full text-left ${
                    activeTab === id
                      ? 'bg-zinc-800 text-white'
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {label}
                </button>
              ))}
            </nav>

            {/* Current Plan */}
            <div className="mt-6 p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Ihr Plan</p>
              <p className="text-sm font-semibold text-white">
                {planLabel[user?.plan_type ?? 'free'] ?? user?.plan_type ?? 'Kostenlos'}
              </p>
              <button
                onClick={() => router.push('/subscription')}
                className="mt-2 text-xs text-orange-400 hover:text-orange-300 transition-colors"
              >
                Upgrade →
              </button>
            </div>
          </aside>

          {/* Content */}
          <div className="flex-1 space-y-5">

            {/* ── Profil ── */}
            {activeTab === 'profil' && (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-base">
                    <User className="w-4 h-4 text-orange-400" />
                    Profil-Informationen
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label className="text-zinc-400 text-sm">Vollständiger Name</Label>
                      <Input
                        value={profile.full_name}
                        onChange={e => setProfile(p => ({ ...p, full_name: e.target.value }))}
                        className="bg-zinc-800 border-zinc-700 text-white focus:border-orange-500"
                        placeholder="Max Mustermann"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-zinc-400 text-sm">E-Mail (nicht änderbar)</Label>
                      <Input
                        value={profile.email}
                        disabled
                        className="bg-zinc-800/50 border-zinc-700 text-zinc-500 cursor-not-allowed"
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-zinc-400 text-sm flex items-center gap-1">
                      <Building className="w-3.5 h-3.5" />
                      Unternehmen (optional)
                    </Label>
                    <Input
                      value={profile.company}
                      onChange={e => setProfile(p => ({ ...p, company: e.target.value }))}
                      className="bg-zinc-800 border-zinc-700 text-white focus:border-orange-500"
                      placeholder="Musterfirma GmbH"
                    />
                  </div>
                  <Button
                    onClick={handleSaveProfile}
                    disabled={saving}
                    className="bg-orange-500 hover:bg-orange-600 text-white gap-2"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Profil speichern
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* ── Benachrichtigungen ── */}
            {activeTab === 'benachrichtigungen' && (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-base">
                    <Bell className="w-4 h-4 text-orange-400" />
                    Benachrichtigungen
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { key: 'email_legal_updates', label: 'Rechtliche Updates per E-Mail', desc: 'Bei neuen Gesetzesänderungen informiert werden' },
                    { key: 'email_scan_complete', label: 'Scan abgeschlossen', desc: 'E-Mail wenn ein Compliance-Scan fertig ist' },
                    { key: 'email_weekly_report', label: 'Wöchentlicher Bericht', desc: 'Zusammenfassung Ihrer Compliance-Werte' },
                    { key: 'browser_alerts', label: 'Browser-Benachrichtigungen', desc: 'Push-Meldungen im Dashboard' },
                  ].map(({ key, label, desc }) => (
                    <div key={key} className="flex items-center justify-between py-3 border-b border-zinc-800 last:border-0">
                      <div>
                        <p className="text-sm font-medium text-white">{label}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">{desc}</p>
                      </div>
                      <Switch
                        checked={notifications[key as keyof typeof notifications]}
                        onCheckedChange={val => setNotifications(n => ({ ...n, [key]: val }))}
                      />
                    </div>
                  ))}
                  <Button
                    onClick={handleSaveNotifications}
                    disabled={saving}
                    className="bg-orange-500 hover:bg-orange-600 text-white gap-2"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Einstellungen speichern
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* ── Sicherheit ── */}
            {activeTab === 'sicherheit' && (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-base">
                    <Shield className="w-4 h-4 text-orange-400" />
                    Passwort ändern
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-1.5">
                    <Label className="text-zinc-400 text-sm">Aktuelles Passwort</Label>
                    <div className="relative">
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        value={passwords.current}
                        onChange={e => setPasswords(p => ({ ...p, current: e.target.value }))}
                        className="bg-zinc-800 border-zinc-700 text-white focus:border-orange-500 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(s => !s)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label className="text-zinc-400 text-sm">Neues Passwort</Label>
                      <Input
                        type="password"
                        value={passwords.next}
                        onChange={e => setPasswords(p => ({ ...p, next: e.target.value }))}
                        className="bg-zinc-800 border-zinc-700 text-white focus:border-orange-500"
                        placeholder="Min. 8 Zeichen"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-zinc-400 text-sm">Passwort bestätigen</Label>
                      <Input
                        type="password"
                        value={passwords.confirm}
                        onChange={e => setPasswords(p => ({ ...p, confirm: e.target.value }))}
                        className={`bg-zinc-800 border-zinc-700 text-white focus:border-orange-500 ${
                          passwords.confirm && passwords.next !== passwords.confirm ? 'border-red-500' : ''
                        }`}
                      />
                    </div>
                  </div>
                  {passwords.confirm && passwords.next !== passwords.confirm && (
                    <p className="text-xs text-red-400">Passwörter stimmen nicht überein.</p>
                  )}
                  <Button
                    onClick={handleChangePassword}
                    disabled={saving || !passwords.current || !passwords.next}
                    className="bg-orange-500 hover:bg-orange-600 text-white gap-2"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                    Passwort ändern
                  </Button>

                  {/* Session Info */}
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <h3 className="text-sm font-medium text-white mb-2">Anmeldung</h3>
                    <p className="text-xs text-zinc-500">
                      Eingeloggt als: <span className="text-zinc-300">{user?.email}</span>
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ── Datenschutz ── */}
            {activeTab === 'datenschutz' && (
              <div className="space-y-4">
                <Card className="bg-zinc-900 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2 text-base">
                      <Download className="w-4 h-4 text-orange-400" />
                      Daten-Export (DSGVO Art. 20)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-zinc-400 mb-4">
                      Laden Sie alle Ihre gespeicherten Daten als JSON-Datei herunter. Dies entspricht Ihrem Recht auf Datenportabilität gemäß DSGVO Art. 20.
                    </p>
                    <Button
                      onClick={handleExportData}
                      variant="outline"
                      className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Daten exportieren
                    </Button>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-red-900/30">
                  <CardHeader>
                    <CardTitle className="text-red-400 flex items-center gap-2 text-base">
                      <Trash2 className="w-4 h-4" />
                      Konto löschen
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-zinc-400 mb-4">
                      Löscht Ihren Account und alle zugehörigen Daten unwiderruflich. Diese Aktion kann nicht rückgängig gemacht werden.
                    </p>
                    <Button
                      variant="outline"
                      className="border-red-800 text-red-400 hover:bg-red-900/20 hover:text-red-300 gap-2"
                      onClick={() => {
                        if (typeof window !== 'undefined' &&
                          window.confirm('Konto wirklich löschen? Diese Aktion ist nicht rückgängig zu machen.')) {
                          window.location.href = 'mailto:support@complyo.tech?subject=Kontolöschung';
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                      Konto löschen
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
