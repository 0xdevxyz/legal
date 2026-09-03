/**
 * AI Explainer Service
 * Converts technical compliance jargon into simple, understandable language
 */

import { ComplianceIssue } from '@/types/api';

interface SimpleExplanation {
  simple: string;
  why: string;
  risk: string;
  fix: string;
  urgency: 'high' | 'medium' | 'low';
  estimatedTime: string;
}

const explanations: Record<string, SimpleExplanation> = {
  'impressum': {
    simple: 'Das Impressum zeigt, wer die Website betreibt. Es ist wie das "Namensschild" Ihrer Firma im Internet.',
    why: 'Geschäftsmäßige Websites brauchen ein Impressum (§ 5 DDG, seit 2024 Nachfolger des TMG). Es schützt Verbraucher und schafft Vertrauen.',
    risk: 'Bußgeld nach dem DDG sowie Abmahnungen durch Wettbewerber. Die Höhe hängt vom Einzelfall ab.',
    fix: 'Erstellen Sie eine Impressum-Seite mit Name, Adresse, Kontaktdaten und Handelsregisternummer.',
    urgency: 'high',
    estimatedTime: '10 Minuten'
  },
  'datenschutz': {
    simple: 'Die Datenschutzerklärung erklärt Besuchern, welche Daten Sie sammeln und was Sie damit machen.',
    why: 'Seit der DSGVO (2018) müssen Sie transparent sein, wie Sie mit Nutzerdaten umgehen.',
    risk: 'Bußgeldrahmen nach Art. 83 DSGVO: bis 20 Mio. € oder 4 % des weltweiten Jahresumsatzes. Die tatsächliche Höhe hängt vom Einzelfall ab.',
    fix: 'Erstellen Sie eine detaillierte Datenschutzerklärung mit allen Datenverarbeitungen.',
    urgency: 'high',
    estimatedTime: '30 Minuten mit Generator'
  },
  'cookies': {
    simple: 'Ein Cookie-Banner fragt Besucher, ob Sie deren Surfverhalten tracken dürfen.',
    why: 'Nutzer müssen aktiv zustimmen, bevor Tracking-Cookies gesetzt werden (§ 25 TDDDG, vormals TTDSG).',
    risk: 'Bußgeld nach dem TDDDG sowie Abmahnungen. Die Höhe hängt vom Einzelfall ab.',
    fix: 'Nutzen Sie unsere integrierte Cookie-Compliance-Lösung unter "Cookie-Compliance" im Dashboard.',
    urgency: 'high',
    estimatedTime: '15 Minuten'
  },
  'ssl': {
    simple: 'HTTPS verschlüsselt die Verbindung zwischen Besuchern und Ihrer Website.',
    why: 'Ohne HTTPS können Dritte Daten mitlesen. Es ist der Basis-Sicherheitsstandard im Web.',
    risk: 'Vertrauensverlust bei Nutzern. Google straft Websites ohne HTTPS ab.',
    fix: 'Installieren Sie ein SSL-Zertifikat (oft kostenlos über Hoster) und aktivieren Sie HTTPS.',
    urgency: 'high',
    estimatedTime: '1 Stunde'
  },
  'barrierefreiheit': {
    simple: 'Barrierefreiheit bedeutet, dass auch Menschen mit Einschränkungen Ihre Website nutzen können.',
    why: 'Seit dem 28.06.2025 gilt das BFSG für Websites, über die Verbrauchern Dienstleistungen angeboten werden. Kleinstunternehmen (unter 10 Beschäftigte und höchstens 2 Mio. € Jahresumsatz) sind bei Dienstleistungen ausgenommen.',
    risk: 'Bußgeld nach dem BFSG sowie Anordnungen der Marktüberwachung. Die Höhe hängt vom Einzelfall ab.',
    fix: 'Fügen Sie Alt-Texte zu Bildern hinzu, sorgen Sie für ausreichende Kontraste und Tastaturnavigation.',
    urgency: 'medium',
    estimatedTime: '2-4 Stunden'
  },
  'contact': {
    simple: 'Kontaktdaten müssen leicht auffindbar sein, damit Nutzer Sie erreichen können.',
    why: 'Transparenz und Erreichbarkeit sind Teil der Vertrauensbildung und gesetzlich vorgeschrieben.',
    risk: 'Abmahnungen durch Wettbewerber. Die Höhe hängt vom Einzelfall ab.',
    fix: 'Fügen Sie eine deutlich sichtbare Kontaktseite mit E-Mail und Telefonnummer hinzu.',
    urgency: 'medium',
    estimatedTime: '5 Minuten'
  },
  'social-media': {
    simple: 'Social Media Plugins (z.B. Facebook Like-Button) übertragen oft Daten ohne Zustimmung.',
    why: 'Jede Datenübertragung an Dritte braucht die Zustimmung des Nutzers (DSGVO).',
    risk: 'Abmahnungen und Bußgelder wegen Datenübermittlung ohne Einwilligung.',
    fix: 'Verwenden Sie 2-Klick-Lösungen oder entfernen Sie die Plugins.',
    urgency: 'medium',
    estimatedTime: '30 Minuten'
  }
};

/**
 * Get simple explanation for a compliance issue
 */
export function explainInSimpleTerms(issue: ComplianceIssue): SimpleExplanation {
  const category = issue.category.toLowerCase();
  
  // Try exact match first
  if (explanations[category]) {
    return explanations[category];
  }
  
  // Try partial matches
  for (const [key, explanation] of Object.entries(explanations)) {
    if (category.includes(key) || issue.title.toLowerCase().includes(key)) {
      return explanation;
    }
  }
  
  // Default fallback
  return {
    simple: issue.description || 'Dieses Problem sollte behoben werden.',
    why: issue.legal_basis || 'Gesetzliche Anforderung',
    risk: issue.risk_euro_max
      ? `Bußgeldrahmen bis ${issue.risk_euro_max} €, abhängig vom Einzelfall`
      : 'Abmahnung oder Bußgeld möglich, abhängig vom Einzelfall',
    fix: issue.solution?.steps?.[0] || 'Bitte Dokumentation prüfen',
    urgency: issue.severity === 'critical' ? 'high' : issue.severity === 'warning' ? 'medium' : 'low',
    estimatedTime: 'Unbekannt'
  };
}

/**
 * Get AI-style conversational explanation
 */
export function getAIConversation(issue: ComplianceIssue): string {
  const explanation = explainInSimpleTerms(issue);
  
  return `Ich habe ein Problem entdeckt: **${issue.title}**

**Was bedeutet das?**
${explanation.simple}

**Warum ist das wichtig?**
${explanation.why}

**Was kann passieren?**
${explanation.risk}

**Wie kann ich das beheben?**
${explanation.fix} ⏱️ Dauert ca. ${explanation.estimatedTime}

💡 **Möchten Sie, dass ich einen detaillierten Fix für Sie generiere?**`;
}

/**
 * Get quick tip without opening modal
 */
export function getQuickTip(issue: ComplianceIssue): string {
  const explanation = explainInSimpleTerms(issue);
  
  const urgencyEmoji = {
    high: '🚨',
    medium: '⚠️',
    low: 'ℹ️'
  };
  
  return `${urgencyEmoji[explanation.urgency]} **Quick-Tipp:** ${explanation.fix} (ca. ${explanation.estimatedTime})`;
}

/**
 * Get priority recommendations
 */
export function getPriorityRecommendations(issues: ComplianceIssue[]): Array<{
  issue: ComplianceIssue;
  explanation: SimpleExplanation;
  priority: number;
}> {
  return issues
    .map(issue => ({
      issue,
      explanation: explainInSimpleTerms(issue),
      priority: calculatePriority(issue, explainInSimpleTerms(issue))
    }))
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 3); // Top 3
}

function calculatePriority(issue: ComplianceIssue, explanation: SimpleExplanation): number {
  let priority = 0;
  
  // Urgency weight
  if (explanation.urgency === 'high') priority += 100;
  if (explanation.urgency === 'medium') priority += 50;
  
  // Risk weight
  const risk = issue.risk_euro_max || 0;
  priority += Math.min(risk / 100, 50); // Max 50 points from risk
  
  // Auto-fixable bonus
  if (issue.auto_fixable) priority += 25;
  
  // Missing element penalty (should be fixed first)
  if (issue.is_missing) priority += 30;
  
  return priority;
}

/**
 * Generate proactive AI suggestions based on user behavior
 */
export function getProactiveSuggestion(
  issue: ComplianceIssue,
  context: 'scroll' | 'hover' | 'scan_complete'
): string | null {
  const explanation = explainInSimpleTerms(issue);
  
  switch (context) {
    case 'scroll':
      if (explanation.urgency === 'high') {
        return `💡 Kurz gestoppt? Dieses Problem ist besonders kritisch (${explanation.risk}). Soll ich mehr erklären?`;
      }
      return null;
    
    case 'hover':
      return `Dieses Problem lässt sich in ca. ${explanation.estimatedTime} beheben. Möchten Sie einen KI-Fix generieren?`;
    
    case 'scan_complete':
      return `Ich habe ${explanation.urgency === 'high' ? 'kritische' : 'wichtige'} Probleme gefunden. Möchten Sie mit dem Wichtigsten starten?`;
    
    default:
      return null;
  }
}

/**
 * Format explanation for display
 */
export function formatExplanation(issue: ComplianceIssue, mode: 'simple' | 'detailed' | 'conversation'): string {
  const explanation = explainInSimpleTerms(issue);
  
  switch (mode) {
    case 'simple':
      return explanation.simple;
    
    case 'detailed':
      return `${explanation.simple}\n\n**Warum:** ${explanation.why}\n\n**Risiko:** ${explanation.risk}\n\n**Lösung:** ${explanation.fix}`;
    
    case 'conversation':
      return getAIConversation(issue);
    
    default:
      return explanation.simple;
  }
}

