import { fetchWithAuth } from './api';

const API_URL = 'https://api.complyo.tech';

export const createCheckoutSession = async (subscriptionTier, paymentType = 'subscription') => {
  const response = await fetchWithAuth(`${API_URL}/api/payment/create-checkout-session`, {
    method: 'POST',
    body: JSON.stringify({
      subscription_tier: subscriptionTier,
      payment_type: paymentType
    })
  });
  
  return response;
};

export const verifyPayment = async (sessionId) => {
  return fetchWithAuth(`${API_URL}/api/payment/verify/${sessionId}`);
};
