'use client';

import React, { useState, useEffect } from 'react';
import { 
  Type, 
  Contrast, 
  Eye, 
  ZoomIn, 
  ZoomOut,
  MousePointer,
  Minus,
  Plus,
  Settings,
  X
} from 'lucide-react';

/**
 * Barrierefreiheits-Widget gemäß BFSG (Barrierefreiheitsstärkungsgesetz)
 * Sichtbarer Showcase für Complyo's Accessibility Features
 */
export default function AccessibilityWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [fontSize, setFontSize] = useState(100);
  const [contrast, setContrast] = useState('normal');
  const [cursorSize, setCursorSize] = useState('normal');
  const [lineHeight, setLineHeight] = useState('normal');

  useEffect(() => {
    // Load saved preferences
    const savedFontSize = localStorage.getItem('a11y-fontSize');
    const savedContrast = localStorage.getItem('a11y-contrast');
    const savedCursor = localStorage.getItem('a11y-cursor');
    const savedLineHeight = localStorage.getItem('a11y-lineHeight');

    if (savedFontSize) setFontSize(parseInt(savedFontSize));
    if (savedContrast) setContrast(savedContrast);
    if (savedCursor) setCursorSize(savedCursor);
    if (savedLineHeight) setLineHeight(savedLineHeight);

    applySettings(
      savedFontSize ? parseInt(savedFontSize) : 100,
      savedContrast || 'normal',
      savedCursor || 'normal',
      savedLineHeight || 'normal'
    );
  }, []);

  const applySettings = (
    size: number, 
    contrastMode: string, 
    cursor: string,
    line: string
  ) => {
    const root = document.documentElement;
    
    // Font Size
    root.style.fontSize = `${size}%`;
    
    // Contrast Mode
    root.classList.remove('contrast-high', 'contrast-inverted');
    if (contrastMode === 'high') {
      root.classList.add('contrast-high');
    } else if (contrastMode === 'inverted') {
      root.classList.add('contrast-inverted');
    }
    
    // Cursor Size
    root.classList.remove('cursor-large');
    if (cursor === 'large') {
      root.classList.add('cursor-large');
    }

    // Line Height
    root.classList.remove('line-height-large');
    if (line === 'large') {
      root.classList.add('line-height-large');
    }
  };

  const handleFontSizeChange = (delta: number) => {
    const newSize = Math.min(150, Math.max(80, fontSize + delta));
    setFontSize(newSize);
    localStorage.setItem('a11y-fontSize', newSize.toString());
    applySettings(newSize, contrast, cursorSize, lineHeight);
  };

  const handleContrastChange = () => {
    const modes = ['normal', 'high', 'inverted'];
    const currentIndex = modes.indexOf(contrast);
    const newMode = modes[(currentIndex + 1) % modes.length];
    setContrast(newMode);
    localStorage.setItem('a11y-contrast', newMode);
    applySettings(fontSize, newMode, cursorSize, lineHeight);
  };

  const handleCursorChange = () => {
    const newCursor = cursorSize === 'normal' ? 'large' : 'normal';
    setCursorSize(newCursor);
    localStorage.setItem('a11y-cursor', newCursor);
    applySettings(fontSize, contrast, newCursor, lineHeight);
  };

  const handleLineHeightChange = () => {
    const newLineHeight = lineHeight === 'normal' ? 'large' : 'normal';
    setLineHeight(newLineHeight);
    localStorage.setItem('a11y-lineHeight', newLineHeight);
    applySettings(fontSize, contrast, cursorSize, newLineHeight);
  };

  const handleReset = () => {
    setFontSize(100);
    setContrast('normal');
    setCursorSize('normal');
    setLineHeight('normal');
    localStorage.removeItem('a11y-fontSize');
    localStorage.removeItem('a11y-contrast');
    localStorage.removeItem('a11y-cursor');
    localStorage.removeItem('a11y-lineHeight');
    applySettings(100, 'normal', 'normal', 'normal');
  };

  return (
    <>
      {/* Floating Button - BFSG Compliant */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-2xl transition-all hover:scale-110 focus:outline-none focus:ring-4 focus:ring-blue-300"
        aria-label="Barrierefreiheits-Einstellungen öffnen"
        aria-expanded={isOpen}
        title="Barrierefreiheits-Einstellungen"
      >
        <Settings className="w-6 h-6" aria-hidden="true" />
      </button>

      {/* Widget Panel */}
      {isOpen && (
        <div 
          className="fixed bottom-24 right-6 z-50 bg-gray-900 border-2 border-blue-500 rounded-2xl shadow-2xl p-6 w-80 animate-fade-in"
          role="dialog"
          aria-label="Barrierefreiheits-Einstellungen"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-400" aria-hidden="true" />
              <h3 className="text-lg font-bold text-white">Barrierefreiheit</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition"
              aria-label="Schließen"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* BFSG Badge */}
          <div className="bg-green-500 bg-opacity-20 border border-green-500 rounded-lg p-3 mb-6">
            <p className="text-xs text-green-300 font-semibold">
              ✓ BFSG-konform (Barrierefreiheitsstärkungsgesetz)
            </p>
          </div>

          {/* Font Size Control */}
          <div className="mb-6">
            <label className="text-sm text-gray-300 mb-2 block font-medium">
              <Type className="w-4 h-4 inline mr-2" aria-hidden="true" />
              Schriftgröße: {fontSize}%
            </label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleFontSizeChange(-10)}
                disabled={fontSize <= 80}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-lg transition"
                aria-label="Schrift verkleinern"
              >
                <Minus className="w-4 h-4" />
              </button>
              <div className="flex-1 bg-gray-800 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-blue-500 h-full transition-all"
                  style={{ width: `${((fontSize - 80) / 70) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={fontSize}
                  aria-valuemin={80}
                  aria-valuemax={150}
                />
              </div>
              <button
                onClick={() => handleFontSizeChange(10)}
                disabled={fontSize >= 150}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-lg transition"
                aria-label="Schrift vergrößern"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Contrast Control */}
          <div className="mb-6">
            <label className="text-sm text-gray-300 mb-2 block font-medium">
              <Contrast className="w-4 h-4 inline mr-2" aria-hidden="true" />
              Kontrast
            </label>
            <button
              onClick={handleContrastChange}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white p-3 rounded-lg transition text-left"
              aria-label={`Kontrast: ${contrast === 'normal' ? 'Normal' : contrast === 'high' ? 'Hoch' : 'Invertiert'}`}
            >
              {contrast === 'normal' && '⚪ Normal'}
              {contrast === 'high' && '⚫ Hoher Kontrast'}
              {contrast === 'inverted' && '🔄 Invertiert'}
            </button>
          </div>

          {/* Cursor Size */}
          <div className="mb-6">
            <label className="text-sm text-gray-300 mb-2 block font-medium">
              <MousePointer className="w-4 h-4 inline mr-2" aria-hidden="true" />
              Mauszeiger
            </label>
            <button
              onClick={handleCursorChange}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white p-3 rounded-lg transition text-left"
              aria-label={`Mauszeiger: ${cursorSize === 'normal' ? 'Normal' : 'Groß'}`}
            >
              {cursorSize === 'normal' ? '🖱️ Normal' : '🖱️ Groß'}
            </button>
          </div>

          {/* Line Height */}
          <div className="mb-6">
            <label className="text-sm text-gray-300 mb-2 block font-medium">
              <Type className="w-4 h-4 inline mr-2" aria-hidden="true" />
              Zeilenabstand
            </label>
            <button
              onClick={handleLineHeightChange}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white p-3 rounded-lg transition text-left"
              aria-label={`Zeilenabstand: ${lineHeight === 'normal' ? 'Normal' : 'Groß'}`}
            >
              {lineHeight === 'normal' ? '≡ Normal' : '≡ Groß'}
            </button>
          </div>

          {/* Reset Button */}
          <button
            onClick={handleReset}
            className="w-full bg-red-600 hover:bg-red-700 text-white p-3 rounded-lg transition font-semibold"
            aria-label="Alle Einstellungen zurücksetzen"
          >
            Zurücksetzen
          </button>

          {/* Info */}
          <p className="text-xs text-gray-500 mt-4 text-center">
            Powered by Complyo • WCAG 2.1 AA
          </p>
        </div>
      )}

      {/* Global Styles */}
      <style jsx global>{`
        .contrast-high {
          filter: contrast(1.5);
        }
        .contrast-inverted {
          filter: invert(1) hue-rotate(180deg);
        }
        .cursor-large * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><circle cx="16" cy="16" r="10" fill="white" stroke="black" stroke-width="2"/></svg>') 16 16, auto !important;
        }
        .line-height-large {
          line-height: 1.8 !important;
        }
        .animate-fade-in {
          animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  );
}

