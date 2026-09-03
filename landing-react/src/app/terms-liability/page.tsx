import { redirect } from 'next/navigation';

// Der Fix-Dialog im Dashboard verlinkte jahrelang auf /terms-liability, eine
// Route, die es nie gab: der Haftungshinweis fuehrte auf eine 404-Seite.
// Die Haftungsregelung steht in den AGB unter Ziffer 11.
export default function TermsLiabilityPage() {
  redirect('/agb#haftung');
}
