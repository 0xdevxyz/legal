'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Shield, User, CreditCard, Lock, Mail, Building, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ProfilePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'billing' | 'password'>('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    company: user?.company || '',
  });

  const [billingData, setBillingData] = useState({
    company_name: '',
    vat_id: '',
    street: '',
    postal_code: '',
    city: '',
    country: 'Deutschland',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const handleSaveProfile = async () => {
    setIsSaving(true);
    setSuccessMessage('');
    setErrorMessage('');

    try {
      // TODO: API-Call zum Speichern der Profildaten
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulation
      setSuccessMessage('Profil erfolgreich aktualisiert!');
    } catch (error) {
      setErrorMessage('Fehler beim Speichern der Profildaten');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveBilling = async () => {
    setIsSaving(true);
    setSuccessMessage('');
    setErrorMessage('');

    try {
      // TODO: API-Call zum Speichern der Rechnungsdaten
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulation
      setSuccessMessage('Rechnungsdaten erfolgreich gespeichert!');
    } catch (error) {
      setErrorMessage('Fehler beim Speichern der Rechnungsdaten');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      setErrorMessage('Passwörter stimmen nicht überein');
      return;
    }

    setIsSaving(true);
    setSuccessMessage('');
    setErrorMessage('');

    try {
      // TODO: API-Call zum Ändern des Passworts
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulation
      setSuccessMessage('Passwort erfolgreich geändert!');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      setErrorMessage('Fehler beim Ändern des Passworts');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold">Profil & Einstellungen</h1>
          </div>
          <p className="text-gray-300">Verwalten Sie Ihre persönlichen Daten und Rechnungsinformationen</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Success/Error Messages */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-900/30 border border-green-500 rounded-lg flex items-center gap-2 text-green-200">
            <CheckCircle className="w-5 h-5" />
            {successMessage}
          </div>
        )}
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-500 rounded-lg flex items-center gap-2 text-red-200">
            <AlertCircle className="w-5 h-5" />
            {errorMessage}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-4 py-3 font-semibold transition-colors flex items-center gap-2 ${
              activeTab === 'profile'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            <User className="w-4 h-4" />
            Profil
          </button>
          <button
            onClick={() => setActiveTab('billing')}
            className={`px-4 py-3 font-semibold transition-colors flex items-center gap-2 ${
              activeTab === 'billing'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            <CreditCard className="w-4 h-4" />
            Rechnungsdaten
          </button>
          <button
            onClick={() => setActiveTab('password')}
            className={`px-4 py-3 font-semibold transition-colors flex items-center gap-2 ${
              activeTab === 'password'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            <Lock className="w-4 h-4" />
            Passwort
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'profile' && (
          <Card>
            <CardHeader>
              <CardTitle>Persönliche Informationen</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  <Mail className="w-4 h-4 inline mr-2" />
                  E-Mail
                </label>
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  <User className="w-4 h-4 inline mr-2" />
                  Vollständiger Name
                </label>
                <input
                  type="text"
                  value={profileData.full_name}
                  onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  <Building className="w-4 h-4 inline mr-2" />
                  Firma (optional)
                </label>
                <input
                  type="text"
                  value={profileData.company}
                  onChange={(e) => setProfileData({ ...profileData, company: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <Button
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? 'Speichern...' : 'Profil speichern'}
              </Button>
            </CardContent>
          </Card>
        )}

        {activeTab === 'billing' && (
          <Card>
            <CardHeader>
              <CardTitle>Rechnungsdaten</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-400 mb-4">
                Diese Daten werden für Ihre Rechnungen verwendet
              </p>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Firmenname *
                </label>
                <input
                  type="text"
                  value={billingData.company_name}
                  onChange={(e) => setBillingData({ ...billingData, company_name: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  USt-IdNr. (optional)
                </label>
                <input
                  type="text"
                  value={billingData.vat_id}
                  onChange={(e) => setBillingData({ ...billingData, vat_id: e.target.value })}
                  placeholder="DE123456789"
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Straße & Hausnummer *
                </label>
                <input
                  type="text"
                  value={billingData.street}
                  onChange={(e) => setBillingData({ ...billingData, street: e.target.value })}
                  placeholder="Musterstraße 123"
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    PLZ *
                  </label>
                  <input
                    type="text"
                    value={billingData.postal_code}
                    onChange={(e) => setBillingData({ ...billingData, postal_code: e.target.value })}
                    placeholder="12345"
                    className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">
                    Stadt *
                  </label>
                  <input
                    type="text"
                    value={billingData.city}
                    onChange={(e) => setBillingData({ ...billingData, city: e.target.value })}
                    placeholder="Berlin"
                    className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Land *
                </label>
                <select
                  value={billingData.country}
                  onChange={(e) => setBillingData({ ...billingData, country: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="Deutschland">Deutschland</option>
                  <option value="Österreich">Österreich</option>
                  <option value="Schweiz">Schweiz</option>
                </select>
              </div>

              <Button
                onClick={handleSaveBilling}
                disabled={isSaving}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? 'Speichern...' : 'Rechnungsdaten speichern'}
              </Button>
            </CardContent>
          </Card>
        )}

        {activeTab === 'password' && (
          <Card>
            <CardHeader>
              <CardTitle>Passwort ändern</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Aktuelles Passwort
                </label>
                <input
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Neues Passwort
                </label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  placeholder="Mindestens 8 Zeichen"
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-300">
                  Passwort bestätigen
                </label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  placeholder="Neues Passwort wiederholen"
                  className="w-full px-4 py-3 rounded-lg bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <Button
                onClick={handleChangePassword}
                disabled={isSaving}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Lock className="w-4 h-4 mr-2" />
                {isSaving ? 'Ändern...' : 'Passwort ändern'}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

