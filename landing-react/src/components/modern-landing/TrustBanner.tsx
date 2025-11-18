'use client';

import React from 'react';
import { motion } from 'framer-motion';

/**
 * TrustBanner - Vertrauens-Banner mit Logos
 */
export default function TrustBanner() {
  const logos = [
    'TechStart GmbH',
    'Digital Solutions',
    'WebPro AG',
    'Innovation Labs',
    'Future Web',
    'Smart Systems',
  ];

  return (
    <section className="bg-white py-12 border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-sm text-gray-500 mb-8 uppercase tracking-wider"
        >
          Vertraut von führenden Unternehmen
        </motion.p>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center">
          {logos.map((logo, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <div className="text-gray-400 font-bold text-sm hover:text-gray-600 transition-colors cursor-pointer">
                {logo}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

