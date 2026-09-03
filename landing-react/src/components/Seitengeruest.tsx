'use client';

import { usePathname } from 'next/navigation';
import NavBar from '@/components/saas-landing/NavBar';
import FooterSection from '@/components/saas-landing/FooterSection';

// Bereiche, die den Marketing-Rahmen nicht bekommen: die Admin-Oberflaeche
// hat ihre eigene Navigation, die Bestaetigungsseite soll niemanden ablenken.
const OHNE_RAHMEN = ['/admin', '/verify-email'];

export default function Seitengeruest({ children }: { children: React.ReactNode }) {
  const pfad = usePathname() || '/';
  const nackt = OHNE_RAHMEN.some((p) => pfad.startsWith(p));

  if (nackt) {
    return <>{children}</>;
  }

  return (
    <>
      <header>
        <NavBar />
      </header>
      {children}
      <FooterSection />
    </>
  );
}
