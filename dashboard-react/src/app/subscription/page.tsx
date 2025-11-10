'use client';

import React, { useState, useEffect } from 'react';
import { getSubscriptionStatus, createPortalSession } from '../../lib/api';
import { useRouter } from 'next/navigation';

interface Subscription {
  plan: string;
  status: string;
  current_period_end: string;
  features: string[];
}

const SubscriptionPage: React.FC = () => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const response = await getSubscriptionStatus();
      if (response.data.has_subscription) {
        setSubscription(response.data);
      }
    } catch (err) {
      setError('Failed to load subscription status. Please try again later.');
      console.error('Error fetching subscription status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await createPortalSession();
      window.location.href = response.data.portal_url;
    } catch (err) {
      setError('Failed to open subscription management. Please try again.');
      console.error('Error creating portal session:', err);
    }
  };

  if (loading) {
    return <p className="text-center">Loading subscription status...</p>;
  }

  if (error) {
    return <p className="text-center text-red-500">{error}</p>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Subscription Management</h1>
        {subscription ? (
          <div className="bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold mb-4">Your Current Plan: {subscription.plan}</h2>
            <p className="text-lg mb-2">Status: <span className="font-semibold capitalize">{subscription.status}</span></p>
            <p className="text-lg mb-4">
              Renews on: {new Date(subscription.current_period_end).toLocaleDateString()}
            </p>
            <div className="mb-6">
              <h3 className="font-semibold mb-2 text-xl">Your plan includes:</h3>
              <ul className="list-disc list-inside">
                {subscription.features.map((feature, index) => (
                  <li key={index} className="text-gray-300">{feature}</li>
                ))}
              </ul>
            </div>
            <button
              className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-200"
              onClick={handleManageSubscription}
            >
              Manage Subscription & Billing
            </button>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-xl mb-4">You do not have an active subscription.</p>
            <button
              className="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-200"
              onClick={() => router.push('/')}
            >
              View Plans
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionPage;