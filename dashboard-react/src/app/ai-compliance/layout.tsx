import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Compliance - ComploAI Guard | Complyo',
  description: 'EU AI Act Compliance für Ihre KI-Systeme',
};

export default function AIComplianceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}

