import { Metadata } from 'next';
import AccessibilityWorklist from '@/components/accessibility/AccessibilityWorklist';

export const metadata: Metadata = {
  title: 'Barrierefreiheit-Worklist | Complyo',
};

export default function AccessibilityWorklistPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <AccessibilityWorklist />
    </main>
  );
}
