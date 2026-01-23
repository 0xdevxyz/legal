'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Facebook,
  Twitter,
  Linkedin,
  Instagram,
  Github,
  Mail,
  MapPin,
  Phone,
} from 'lucide-react';
import { Logo } from '../Logo';

/**
 * FooterModern - Moderner, umfassender Footer
 */
export default function FooterModern() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    Produkte: [
      { name: 'Accessibility Widget', href: '#' },
      { name: 'Accessibility Checker', href: '#' },
      { name: 'Accessibility Monitor', href: '#' },
      { name: 'Accessibility Audit', href: '#' },
      { name: 'VPAT / ACR', href: '#' },
    ],
    Lösungen: [
      { name: 'WordPress', href: '#' },
      { name: 'Shopify', href: '#' },
      { name: 'Wix', href: '#' },
      { name: 'Webflow', href: '#' },
      { name: 'Custom Websites', href: '#' },
    ],
    Compliance: [
      { name: 'WCAG 2.1', href: '#' },
      { name: 'ADA', href: '#' },
      { name: 'Section 508', href: '#' },
      { name: 'EN 301-549', href: '#' },
      { name: 'DSGVO', href: '#' },
    ],
    Unternehmen: [
      { name: 'Über uns', href: '#' },
      { name: 'Team', href: '#' },
      { name: 'Karriere', href: '#' },
      { name: 'Kontakt', href: '#' },
      { name: 'Blog', href: '#' },
    ],
  };

  const socialLinks = [
    { icon: Facebook, href: '#', label: 'Facebook' },
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: Linkedin, href: '#', label: 'LinkedIn' },
    { icon: Instagram, href: '#', label: 'Instagram' },
    { icon: Github, href: '#', label: 'GitHub' },
  ];

  return (
    <footer className="bg-gradient-to-br from-slate-900 via-gray-900 to-black text-white relative z-10">
      {/* Main Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-12 mb-12">
          {/* Company Info */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              {/* Logo */}
              <Logo size="xl" variant="default" className="mb-4" />
              <p className="text-gray-400 mb-6 leading-relaxed">
                Die führende Plattform für Web-Barrierefreiheit und WCAG-Compliance. 
                Automatisiert, KI-gestützt und von Experten unterstützt.
              </p>

              {/* Contact Info */}
              <div className="space-y-3 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-blue-400" />
                  <span>Berlin, Deutschland</span>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-blue-400" />
                  <a
                    href="mailto:info@complyo.tech"
                    className="hover:text-white transition-colors"
                  >
                    info@complyo.tech
                  </a>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-blue-400" />
                  <a href="tel:+49301234567" className="hover:text-white transition-colors">
                    +49 (0) 30 1234567
                  </a>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Links Columns */}
          {Object.entries(footerLinks).map(([title, links], idx) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
            >
              <h4 className="font-bold text-white mb-4">{title}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      className="text-gray-400 hover:text-white transition-colors text-sm"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-800 my-8" />

        {/* Bottom Footer */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Copyright */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex items-center gap-3"
          >
            <Logo size="sm" variant="default" />
            <p className="text-sm text-gray-400">
              © {currentYear} Alle Rechte vorbehalten.
            </p>
          </motion.div>

          {/* Social Links */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex items-center gap-4"
          >
            {socialLinks.map((social, idx) => {
              const Icon = social.icon;
              return (
                <motion.a
                  key={social.label}
                  href={social.href}
                  whileHover={{ scale: 1.2, y: -2 }}
                  whileTap={{ scale: 0.9 }}
                  aria-label={social.label}
                  className="w-10 h-10 bg-gray-800 hover:bg-gradient-to-r hover:from-blue-600 hover:to-purple-600 rounded-full flex items-center justify-center transition-all"
                >
                  <Icon className="w-5 h-5" />
                </motion.a>
              );
            })}
          </motion.div>

          {/* Legal Links */}
          <div className="flex items-center gap-6 text-sm text-gray-400">
            <Link href="/datenschutz" className="hover:text-white transition-colors">
              Datenschutz
            </Link>
            <Link href="/impressum" className="hover:text-white transition-colors">
              Impressum
            </Link>
            <Link href="/agb" className="hover:text-white transition-colors">
              AGB
            </Link>
          </div>
        </div>
      </div>

      {/* W3C Badge */}
      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex items-center justify-center gap-4"
          >
            <div className="text-xs text-gray-500">
              WCAG 2.1 Level AA konform
            </div>
            <div className="w-px h-4 bg-gray-700" />
            <div className="text-xs text-gray-500">ISO 27001 zertifiziert</div>
            <div className="w-px h-4 bg-gray-700" />
            <div className="text-xs text-gray-500">DSGVO-konform</div>
          </motion.div>
        </div>
      </div>
    </footer>
  );
}
