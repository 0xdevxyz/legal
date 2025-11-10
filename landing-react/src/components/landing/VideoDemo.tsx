'use client';

import React, { useState } from 'react';
import { Play, X } from 'lucide-react';

/**
 * VideoDemo - Demo-Video Section
 * Placeholder für YouTube/Vimeo Video
 */
export default function VideoDemo() {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <section className="bg-white py-20" id="demo">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Sehen Sie Complyo in Aktion
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Von der ersten Analyse bis zum exportierbaren Fix in unter 2 Minuten
          </p>
        </div>
        
        {/* Video Container */}
        <div className="relative">
          {!isPlaying ? (
            <div className="relative group cursor-pointer" onClick={() => setIsPlaying(true)}>
              {/* Thumbnail */}
              <div className="aspect-video bg-gradient-to-br from-gray-800 via-blue-900 to-purple-900 rounded-2xl shadow-2xl flex items-center justify-center overflow-hidden">
                {/* Mock Dashboard Screenshot */}
                <div className="relative w-full h-full flex items-center justify-center">
                  <div className="absolute inset-0 bg-black/40 group-hover:bg-black/30 transition-colors"></div>
                  
                  {/* Play Button */}
                  <div className="relative z-10 w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-2xl transform group-hover:scale-110 transition-transform">
                    <Play className="w-10 h-10 text-blue-600 ml-1" fill="currentColor" />
                  </div>
                  
                  {/* Mock Content Behind */}
                  <div className="absolute inset-0 p-12 opacity-50">
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 max-w-2xl">
                      <div className="flex items-center justify-between mb-4">
                        <div className="h-6 bg-white/20 rounded w-48"></div>
                        <div className="h-6 bg-green-500/30 rounded w-24"></div>
                      </div>
                      <div className="h-32 bg-white/10 rounded-lg mb-4"></div>
                      <div className="space-y-3">
                        <div className="h-12 bg-white/10 rounded-lg"></div>
                        <div className="h-12 bg-white/10 rounded-lg"></div>
                        <div className="h-12 bg-white/10 rounded-lg"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Duration Badge */}
              <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm font-semibold">
                ⏱️ 2:14
              </div>
            </div>
          ) : (
            <div className="relative aspect-video bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
              {/* Close Button */}
              <button
                onClick={() => setIsPlaying(false)}
                className="absolute top-4 right-4 z-20 w-10 h-10 bg-black/60 hover:bg-black/80 backdrop-blur-sm rounded-full flex items-center justify-center transition-colors"
                aria-label="Video schließen"
              >
                <X className="w-6 h-6 text-white" />
              </button>
              
              {/* Video Embed - Replace with actual video URL */}
              <iframe
                className="w-full h-full"
                src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
                title="Complyo Demo Video"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
            </div>
          )}
        </div>
        
        {/* Features Below Video */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-6">
            <div className="text-4xl font-bold text-blue-600 mb-2">1.</div>
            <h3 className="font-semibold text-gray-900 mb-2">Website scannen</h3>
            <p className="text-sm text-gray-600">URL eingeben und automatische Analyse starten</p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl font-bold text-purple-600 mb-2">2.</div>
            <h3 className="font-semibold text-gray-900 mb-2">Lösungen generieren</h3>
            <p className="text-sm text-gray-600">KI erstellt Code-Fixes mit genauer Lokalisierung</p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl font-bold text-green-600 mb-2">3.</div>
            <h3 className="font-semibold text-gray-900 mb-2">Copy & Paste</h3>
            <p className="text-sm text-gray-600">Fixes implementieren und Score verbessern</p>
          </div>
        </div>
      </div>
    </section>
  );
}

