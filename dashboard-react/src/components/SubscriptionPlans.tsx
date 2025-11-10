'use client';

import React, { useState, useEffect } from 'react';
import { getAvailablePlans, createCheckoutSession } from '../lib/api';

interface Plan {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  setup_fee?: number;
  setup_fee_description?: string;
  features: string[];
}

const SubscriptionPlans: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await getAvailablePlans();
      
      // Parse features from JSON string to array
      const parsedPlans = response.data.map((plan: any) => ({
        ...plan,
        features: typeof plan.features === 'string' 
          ? JSON.parse(plan.features) 
          : plan.features
      }));
      
      setPlans(parsedPlans);
    } catch (err) {
      setError('Failed to load subscription plans. Please try again later.');
      console.error('Error fetching plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    try {
      const response = await createCheckoutSession(
        planId,
        `${window.location.origin}/dashboard?subscription=success`,
        `${window.location.origin}/dashboard?subscription=canceled`
      );
      window.location.href = response.data.checkout_url;
    } catch (err) {
      setError('Failed to initiate checkout. Please try again.');
      console.error('Error creating checkout session:', err);
    }
  };

  if (loading) {
    return <p className="text-center">Loading plans...</p>;
  }

  if (error) {
    return <p className="text-center text-red-500">{error}</p>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold mb-8 text-center">Choose Your Subscription Plan</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {plans.map((plan) => (
          <div key={plan.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
              <p className="text-gray-600 mb-4">{plan.description}</p>
              <p className="text-2xl font-bold mb-1">€{plan.price_monthly.toFixed(2)} <span className="text-sm font-normal text-gray-500">netto / Monat</span></p>
              {plan.price_yearly && plan.price_yearly !== plan.price_monthly && (
                <p className="text-sm text-gray-500 mb-4">
                  oder €{plan.price_yearly.toFixed(2)} / Jahr
                </p>
              )}
              {plan.setup_fee && plan.setup_fee > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                  <p className="text-sm font-semibold text-amber-900 mb-1">
                    ⚠️ Einmalige Setup-Gebühr: €{plan.setup_fee.toFixed(2)}
                  </p>
                  {plan.setup_fee_description && (
                    <p className="text-xs text-amber-700">{plan.setup_fee_description}</p>
                  )}
                </div>
              )}
              <div className="mb-6">
                <h4 className="font-semibold mb-2">Features:</h4>
                <ul className="list-disc list-inside">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="text-gray-600">{feature}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="px-6 pb-6">
              <button
                className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-200"
                onClick={() => handleSubscribe(plan.id)}
              >
                Subscribe
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SubscriptionPlans;