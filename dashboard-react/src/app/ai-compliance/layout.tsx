import { Metadata } from 'next';
import { ComploaiGate } from '@/components/ai-compliance/ComploaiGate';

export const metadata: Metadata = {
  title: 'AI Compliance - ComploAI Guard | Complyo',
  description: 'EU AI Act Compliance für Ihre KI-Systeme',
};

export default function AIComplianceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ComploaiGate>{children}</ComploaiGate>;
}

