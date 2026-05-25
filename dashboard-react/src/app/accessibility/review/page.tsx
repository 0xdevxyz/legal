import { Metadata } from 'next';
import AltTextReviewQueue from '@/components/accessibility/AltTextReviewQueue';

export const metadata: Metadata = {
  title: 'Alt-Text Review | Complyo',
};

export default function AltTextReviewPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <AltTextReviewQueue />
    </main>
  );
}
