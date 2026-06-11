'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { CheckCircle, XCircle, Shield, Zap, Plus, Loader2, AlertTriangle } from 'lucide-react';
import { getMyAddons, cancelAddon } from '@/lib/ai-compliance-api';
import type { Addon } from '@/types/ai-compliance';

const ADDON_META: Record<string, { icon: React.ElementType; color: string }> = {
  comploai_guard: { icon: Shield, color: 'text-purple-400' },
  priority_support: { icon: Zap, color: 'text-yellow-400' },
};

function AddonCard({ addon, onCancel }: { addon: Addon; onCancel: (key: string) => void }) {
  const [confirming, setConfirming] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const meta = ADDON_META[addon.addon_key] ?? { icon: Shield, color: 'dark:text-gray-400 text-gray-600' };
  const Icon = meta.icon;

  const handleCancel = async () => {
    if (!confirming) { setConfirming(true); return; }
    setCancelling(true);
    await onCancel(addon.addon_key);
    setCancelling(false);
    setConfirming(false);
  };

  const startedDate = new Date(addon.started_at).toLocaleDateString('de-DE');

  return (
    <div className="dark:bg-zinc-800 bg-white border dark:border-zinc-700 border-gray-200 rounded-xl p-6 flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 dark:bg-zinc-800 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Icon className={`w-5 h-5 ${meta.color}`} />
          </div>
          <div>
            <div className="font-semibold">{addon.addon_name}</div>
            <div className="text-sm dark:text-gray-400 text-gray-600">seit {startedDate}</div>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-lg font-bold">{addon.price_monthly}€<span className="text-sm font-normal dark:text-gray-400 text-gray-600">/Mo</span></div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            addon.status === 'active'
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            {addon.status === 'active' ? 'Aktiv' : addon.status === 'cancelled' ? 'Gekündigt' : 'Abgelaufen'}
          </span>
        </div>
      </div>

      {addon.limits && Object.keys(addon.limits).length > 0 && (
        <div className="text-xs text-gray-500 bg-gray-900/50 rounded-lg px-3 py-2">
          {Object.entries(addon.limits).map(([k, v]) => (
            <span key={k}>{k}: {v === -1 ? 'Unbegrenzt' : v}</span>
          ))}
        </div>
      )}

      {addon.status === 'active' && (
        <div className="flex justify-end">
          {confirming ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-400">Wirklich kündigen?</span>
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-sm rounded-lg transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {cancelling && <Loader2 className="w-3 h-3 animate-spin" />}
                Ja, kündigen
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="px-3 py-1.5 dark:bg-zinc-800 bg-gray-100 hover:bg-gray-600 text-sm rounded-lg transition-colors"
              >
                Abbrechen
              </button>
            </div>
          ) : (
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 text-sm dark:text-gray-400 text-gray-600 hover:text-red-400 border dark:border-zinc-700 border-gray-200 hover:border-red-700 rounded-lg transition-colors"
            >
              Kündigen
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function AddonsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const success = searchParams.get('success') === 'true';
  const canceled = searchParams.get('canceled') === 'true';

  const [addons, setAddons] = useState<Addon[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      setLoading(true);
      const data = await getMyAddons();
      setAddons(data.addons);
      setTotalCost(data.total_monthly_cost);
    } catch (err: any) {
      setError('Add-ons konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (addonKey: string) => {
    try {
      setCancelError(null);
      await cancelAddon(addonKey);
      await load();
    } catch (err: any) {
      setCancelError(err.response?.data?.detail || 'Kündigung fehlgeschlagen.');
    }
  };

  const activeAddons = addons.filter(a => a.status === 'active');
  const inactiveAddons = addons.filter(a => a.status !== 'active');

  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-3xl mx-auto">

        {/* Success Banner */}
        {success && (
          <div className="mb-8 flex items-start gap-4 bg-green-500/10 border border-green-500/40 rounded-xl p-5">
            <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-green-300">Zahlung erfolgreich!</div>
              <div className="text-sm dark:text-gray-400 text-gray-600 mt-1">
                Ihr Add-on wurde aktiviert. Es kann einige Sekunden dauern bis es hier erscheint.
              </div>
            </div>
          </div>
        )}

        {/* Canceled Banner */}
        {canceled && (
          <div className="mb-8 flex items-start gap-4 bg-yellow-500/10 border border-yellow-500/40 rounded-xl p-5">
            <XCircle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-yellow-300">Checkout abgebrochen</div>
              <div className="text-sm dark:text-gray-400 text-gray-600 mt-1">
                Es wurde nichts berechnet. Sie können jederzeit ein Add-on aktivieren.
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Meine Add-ons</h1>
            {totalCost > 0 && (
              <p className="dark:text-gray-400 text-gray-600 mt-1">
                Monatliche Gesamtkosten: <span className="dark:text-white text-gray-900 font-semibold">{totalCost}€</span>
              </p>
            )}
          </div>
          <button
            onClick={() => router.push('/ai-compliance/upgrade')}
            className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 rounded-xl font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add-on hinzufügen
          </button>
        </div>

        {cancelError && (
          <div className="mb-4 flex items-center gap-3 bg-red-500/10 border border-red-500/40 rounded-xl p-4 text-sm text-red-400">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {cancelError}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20 dark:text-gray-400 text-gray-600">
            <Loader2 className="w-6 h-6 animate-spin mr-3" />
            Lade Add-ons...
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-400">{error}</div>
        ) : activeAddons.length === 0 && inactiveAddons.length === 0 ? (
          <div className="text-center py-20">
            <Shield className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="dark:text-gray-400 text-gray-600 mb-6">Sie haben noch keine Add-ons aktiviert.</p>
            <button
              onClick={() => router.push('/ai-compliance/upgrade')}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-xl font-medium transition-colors"
            >
              Add-ons entdecken
            </button>
          </div>
        ) : (
          <div className="space-y-8">
            {activeAddons.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold dark:text-gray-400 text-gray-600 uppercase tracking-wider mb-4">Aktiv</h2>
                <div className="space-y-4">
                  {activeAddons.map(addon => (
                    <AddonCard key={addon.id} addon={addon} onCancel={handleCancel} />
                  ))}
                </div>
              </section>
            )}

            {inactiveAddons.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold dark:text-gray-400 text-gray-600 uppercase tracking-wider mb-4">Inaktiv</h2>
                <div className="space-y-4">
                  {inactiveAddons.map(addon => (
                    <AddonCard key={addon.id} addon={addon} onCancel={handleCancel} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
