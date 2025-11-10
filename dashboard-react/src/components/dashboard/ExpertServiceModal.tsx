'use client';

import React, { useState } from 'react';
import { X, Send, CheckCircle } from 'lucide-react';

/**
 * ExpertServiceModal - Kontaktformular für Expertenservice
 * Öffnet sich wenn User auf "Expertenservice kontaktieren" klickt
 */
export default function ExpertServiceModal() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    website: '',
    message: '',
    service_type: '2900'  // '2900' für Expertenservice, '39' für DIY
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // TODO: API-Endpunkt für Kontaktanfrage
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const response = await fetch(`${API_URL}/api/v2/contact/expert-service`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        setIsSuccess(true);
        setTimeout(() => {
          closeModal();
        }, 3000);
      } else {
        alert('Fehler beim Senden der Anfrage. Bitte versuchen Sie es erneut.');
      }
    } catch (error) {
      console.error('Fehler beim Senden:', error);
      alert('Fehler beim Senden der Anfrage.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const closeModal = () => {
    const modal = document.getElementById('expert-service-modal') as any;
    modal?.close();
    // Reset Form
    setTimeout(() => {
      setFormData({
        name: '',
        email: '',
        phone: '',
        website: '',
        message: '',
        service_type: '2900'
      });
      setIsSuccess(false);
    }, 300);
  };
  
  return (
    <dialog 
      id="expert-service-modal" 
      className="modal backdrop:bg-black/50 rounded-2xl p-0 max-w-2xl w-full"
    >
      <div className="bg-gray-900 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Expertenservice anfragen</h2>
              <p className="text-white/80 text-sm mt-1">
                Wir setzen Ihre Compliance-Anforderungen professionell um
              </p>
            </div>
            <button
              onClick={closeModal}
              className="text-white/80 hover:text-white transition"
              type="button"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          {isSuccess ? (
            // Success Message
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-white mb-2">
                Anfrage erfolgreich gesendet!
              </h3>
              <p className="text-gray-400">
                Wir melden uns innerhalb von 24 Stunden bei Ihnen.
              </p>
            </div>
          ) : (
            // Form
            <>
              {/* Service-Typ Auswahl */}
              <div className="mb-6 bg-gray-800 rounded-lg p-4">
                <label className="block text-white font-semibold mb-3">
                  Welcher Service interessiert Sie?
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* DIY mit KI */}
                  <div
                    onClick={() => setFormData({...formData, service_type: '39'})}
                    className={`cursor-pointer p-4 rounded-lg border-2 transition ${
                      formData.service_type === '39'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <input
                        type="radio"
                        checked={formData.service_type === '39'}
                        onChange={() => setFormData({...formData, service_type: '39'})}
                        className="w-4 h-4"
                      />
                      <h4 className="text-white font-semibold">DIY mit KI</h4>
                    </div>
                    <p className="text-gray-400 text-sm">39€/Monat</p>
                    <p className="text-gray-500 text-xs mt-1">
                      KI-Fixes selbst umsetzen
                    </p>
                  </div>
                  
                  {/* Expertenservice */}
                  <div
                    onClick={() => setFormData({...formData, service_type: '2900'})}
                    className={`cursor-pointer p-4 rounded-lg border-2 transition ${
                      formData.service_type === '2900'
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <input
                        type="radio"
                        checked={formData.service_type === '2900'}
                        onChange={() => setFormData({...formData, service_type: '2900'})}
                        className="w-4 h-4"
                      />
                      <h4 className="text-white font-semibold">Expertenservice</h4>
                    </div>
                    <p className="text-gray-400 text-sm">2.900€ + 29€/Monat</p>
                    <p className="text-gray-500 text-xs mt-1">
                      Wir setzen alles für Sie um
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
                    placeholder="Ihr vollständiger Name"
                  />
                </div>
                
                {/* Email */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    E-Mail *
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
                    placeholder="ihre@email.de"
                  />
                </div>
                
                {/* Phone */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    Telefon (optional)
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
                    placeholder="+49 123 456789"
                  />
                </div>
                
                {/* Website */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    Website-URL *
                  </label>
                  <input
                    type="url"
                    required
                    value={formData.website}
                    onChange={(e) => setFormData({...formData, website: e.target.value})}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
                    placeholder="https://ihre-website.de"
                  />
                </div>
                
                {/* Message */}
                <div>
                  <label className="block text-white font-semibold mb-2">
                    Ihre Nachricht
                  </label>
                  <textarea
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                    rows={4}
                    className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none resize-none"
                    placeholder="Beschreiben Sie kurz Ihre Anforderungen..."
                  />
                </div>
                
                {/* Submit Button */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex-1 bg-gray-800 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition"
                  >
                    Abbrechen
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>Wird gesendet...</>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        Anfrage senden
                      </>
                    )}
                  </button>
                </div>
              </form>
              
              {/* Info */}
              <div className="mt-6 bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <p className="text-gray-400 text-sm">
                  <strong className="text-white">Was passiert als Nächstes?</strong><br/>
                  Unser Team meldet sich innerhalb von 24 Stunden bei Ihnen, um Ihre Anforderungen 
                  zu besprechen und ein individuelles Angebot zu erstellen.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </dialog>
  );
}

