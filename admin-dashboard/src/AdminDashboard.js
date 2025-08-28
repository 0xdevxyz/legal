import React, { useState } from 'react';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const mockStats = {
    totalTests: 12,
    activeTests: 3,
    conversions: 847,
    conversionRate: 4.2
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Complyo Admin Dashboard</h1>
        </div>
      </header>

      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { id: 'overview', name: 'Übersicht' },
              { id: 'ab-tests', name: 'A/B Tests' },
              { id: 'analytics', name: 'Analytics' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Übersicht</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Tests</h3>
                <div className="text-3xl font-bold text-blue-600">{mockStats.totalTests}</div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Aktive Tests</h3>
                <div className="text-3xl font-bold text-green-600">{mockStats.activeTests}</div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Konversionen</h3>
                <div className="text-3xl font-bold text-purple-600">{mockStats.conversions}</div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Conversion Rate</h3>
                <div className="text-3xl font-bold text-orange-600">{mockStats.conversionRate}%</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Status</h3>
              <div className="text-green-600 font-semibold">✅ Admin Dashboard läuft erfolgreich!</div>
              <p className="text-gray-600 mt-2">Alle Systeme sind betriebsbereit.</p>
            </div>
          </div>
        )}

        {activeTab === 'ab-tests' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">A/B Tests</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600">A/B Test Management wird hier implementiert...</p>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Analytics</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600">Analytics Dashboard wird hier implementiert...</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
