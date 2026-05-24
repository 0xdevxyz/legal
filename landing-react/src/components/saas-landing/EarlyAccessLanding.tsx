'use client';
import React from 'react';
import NavBar from './NavBar';
import HeroSection from './HeroSection';
import WebsiteScanner from '../landing/WebsiteScanner';
import JoinEarlySection from './JoinEarlySection';
import FooterSection from './FooterSection';

export default function EarlyAccessLanding() {
  return (
    <main className="font-sans antialiased bg-white">
      <NavBar />
      <HeroSection />
      <WebsiteScanner />
      <JoinEarlySection />
      <FooterSection />
    </main>
  );
}
