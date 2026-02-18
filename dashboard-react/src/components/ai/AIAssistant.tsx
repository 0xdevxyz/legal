'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, X, Send, Minimize2, Maximize2 } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { getAIConversation, getProactiveSuggestion } from '@/lib/ai-explainer';
import type { ComplianceIssue } from '@/types/api';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

export const AIAssistant: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { analysisData, currentWebsite } = useDashboardStore();

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Welcome message when first opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      addAIMessage('Hallo! 👋 Ich bin Ihr KI-Compliance-Assistent. Ich helfe Ihnen, Ihre Website DSGVO-konform und rechtssicher zu machen. Wie kann ich Ihnen helfen?');
    }
  }, [isOpen]);

  // Proactive suggestions after scan
  useEffect(() => {
    if (analysisData && analysisData.issues && analysisData.issues.length > 0 && !isOpen) {
      const criticalIssues = analysisData.issues.filter((issue: ComplianceIssue) => issue.severity === 'critical');
      
      if (criticalIssues.length > 0) {
        // Show bubble notification
        setTimeout(() => {
          if (!isOpen) {
            // Trigger a subtle animation or notification
          }
        }, 3000);
      }
    }
  }, [analysisData]);

  const addAIMessage = (content: string) => {
    const message: Message = {
      id: Date.now().toString() + Math.random(),
      type: 'ai',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const addUserMessage = (content: string) => {
    const message: Message = {
      id: Date.now().toString() + Math.random(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userInput = inputValue.trim();
    addUserMessage(userInput);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI thinking
    setTimeout(() => {
      const response = generateAIResponse(userInput);
      addAIMessage(response);
      setIsTyping(false);
    }, 800);
  };

  const generateAIResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();

    // Check for specific questions
    if (lowerInput.includes('impressum')) {
      return `Das Impressum ist das "Namensschild" Ihrer Website. Es muss folgende Angaben enthalten:

• Vollständiger Name (bei Firmen: Firmenname)
• Adresse
• Kontaktdaten (E-Mail, Telefon)
• Handelsregisternummer (falls vorhanden)
• Umsatzsteuer-ID (falls vorhanden)

💡 **Möchten Sie, dass ich ein Impressum-Template für Sie generiere?**`;
    }

    if (lowerInput.includes('datenschutz') || lowerInput.includes('dsgvo')) {
      return `Die Datenschutzerklärung informiert Besucher über:

• Welche Daten Sie sammeln
• Warum Sie diese Daten brauchen
• Wie lange Sie die Daten speichern
• An wen Sie Daten weitergeben
• Welche Rechte Nutzer haben

📋 **Tipp:** Nutzen Sie einen Generator wie den von eRecht24, um eine vollständige Datenschutzerklärung zu erstellen.

Soll ich Ihnen zeigen, wo Sie das auf Ihrer Website einfügen?`;
    }

    if (lowerInput.includes('cookie') || lowerInput.includes('consent')) {
      return `Cookie-Consent ist seit 2021 Pflicht (TTDSG). Sie brauchen:

✅ **Cookie-Banner** bevor Cookies gesetzt werden
✅ **Ablehnen-Option** genauso prominent wie "Akzeptieren"
✅ **Cookie-Liste** in der Datenschutzerklärung

🍪 **Complyo bietet eine integrierte Cookie-Compliance-Lösung!**

Gehen Sie im Dashboard zu **"Cookie-Compliance"** um:
• Ihre Website automatisch zu scannen
• Ein DSGVO-konformes Banner zu konfigurieren
• Consent-Statistiken zu verfolgen

Soll ich Sie direkt zur Cookie-Compliance-Einrichtung führen?`;
    }

    if (lowerInput.includes('hilf') || lowerInput.includes('help') || lowerInput.includes('anfang')) {
      if (analysisData && analysisData.issues) {
        const criticalCount = analysisData.issues.filter((i: ComplianceIssue) => i.severity === 'critical').length;
        if (criticalCount > 0) {
          return `Ich empfehle, mit den **${criticalCount} kritischen Problemen** zu starten. Diese können zu Abmahnungen führen.

Die wichtigsten sind:
${analysisData.issues
  .filter((i: ComplianceIssue) => i.severity === 'critical')
  .slice(0, 3)
  .map((i: ComplianceIssue, idx: number) => `${idx + 1}. ${i.title}`)
  .join('\n')}

💡 **Soll ich für das erste Problem einen KI-Fix generieren?**`;
        }
      }
      return 'Gerne! Sagen Sie mir einfach, was Sie wissen möchten. Ich kann Ihnen helfen mit:\n\n• Impressum erstellen\n• Datenschutzerklärung\n• Cookie-Banner\n• DSGVO-Anforderungen\n• Schnelle Fixes für Probleme';
    }

    if (lowerInput.includes('fix') || lowerInput.includes('beheben') || lowerInput.includes('lösung')) {
      return `Perfekt! Um einen Fix zu generieren:

1️⃣ Wählen Sie das Problem aus der Liste
2️⃣ Klicken Sie auf "🤖 KI-Fix (5 Min)"
3️⃣ Sie erhalten fertigen Code + Anleitung

Oder sagen Sie mir, welches Problem ich zuerst angehen soll!`;
    }

    // Check if asking about current scan
    if (currentWebsite && (lowerInput.includes('website') || lowerInput.includes('seite') || lowerInput.includes('scan'))) {
      const score = analysisData?.compliance_score || 0;
      return `Ihre Website **${currentWebsite.url}** hat einen Compliance-Score von **${score}/100**.

${score < 60 ? '🚨 Es gibt kritische Probleme, die sofort behoben werden sollten.' : score < 80 ? '⚠️ Einige Verbesserungen sind empfehlenswert.' : '✅ Ihre Website ist weitgehend compliant!'}

Möchten Sie, dass ich Ihnen die wichtigsten Probleme erkläre?`;
    }

    // Default helpful response
    return `Gute Frage! ${input.endsWith('?') ? 'Hier ist meine Antwort:' : ''}

Ich bin spezialisiert auf:
• **DSGVO & Datenschutz** - Was Sie beachten müssen
• **Impressum & TMG** - Pflichtangaben
• **Cookie-Consent** - Banner richtig einrichten
• **Barrierefreiheit** - BFSG-konforme Websites

Stellen Sie mir eine spezifische Frage oder sagen Sie "Hilfe", um zu sehen, wo ich ansetzen sollte! 😊`;
  };

  const handleQuickAction = (action: string) => {
    setInputValue(action);
    handleSend();
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-110 flex items-center justify-center group"
      >
        <Sparkles className="w-7 h-7 text-white animate-pulse" />
        <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-bounce">
          !
        </div>
        <div className="absolute -top-12 right-0 bg-gray-900 text-white px-3 py-2 rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
          Fragen Sie mich!
        </div>
      </button>
    );
  }

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-4 flex items-center gap-3">
        <Sparkles className="w-5 h-5 text-blue-600" />
        <span className="font-medium text-gray-900">KI-Assistent</span>
        <button
          onClick={() => setIsMinimized(false)}
          className="ml-auto text-gray-400 hover:text-gray-600"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 h-[600px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">KI-Assistent</h3>
            <p className="text-xs text-white/80">Immer für Sie da</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(true)}
            className="text-white/80 hover:text-white transition-colors"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {messages.length === 1 && (
        <div className="p-4 border-t border-gray-200 bg-white">
          <p className="text-xs text-gray-500 mb-2">Schnelle Fragen:</p>
          <div className="flex flex-wrap gap-2">
            {['Was ist ein Impressum?', 'Cookie-Banner einrichten', 'DSGVO erklärt', 'Wo anfangen?'].map((action) => (
              <button
                key={action}
                onClick={() => handleQuickAction(action)}
                className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex gap-2">
          <label htmlFor="ai-assistant-input" className="sr-only">Nachricht an KI-Assistent</label>
          <input
            type="text"
            id="ai-assistant-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Fragen Sie mich etwas..."
            aria-label="Nachricht an KI-Assistent eingeben"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

