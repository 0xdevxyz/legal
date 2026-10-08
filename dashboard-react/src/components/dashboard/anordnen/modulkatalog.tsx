'use client';

/**
 * Katalog der Module auf der Dashboard-Startseite.
 *
 * Reihenfolge im Array = Standardreihenfolge innerhalb der jeweiligen Spalte.
 * Ein neues Modul kommt hier dazu und erscheint damit bei allen Nutzern am Ende
 * seiner Standardspalte, auch wenn sie ihr Layout schon verändert haben
 * (siehe `abgleichen` in lib/dashboard-layout.ts).
 *
 * Die Ids sind Teil des gespeicherten Layouts: umbenennen heißt, dass
 * Nutzer das Modul an der Standardposition wiederfinden.
 */

import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Globe,
  Gauge,
  BarChart3,
  ClipboardList,
  Workflow,
  Newspaper,
  Cookie,
  Layers,
  BrainCircuit,
} from 'lucide-react';
import type { Spalte } from '@/lib/dashboard-layout';
import { WebsiteAnalysis } from '@/components/dashboard/WebsiteAnalysis';
import { LegalNews } from '@/components/dashboard/LegalNews';
import { CookieComplianceWidget } from '@/components/dashboard/CookieComplianceWidget';
import { ComplianceGauge } from '@/components/dashboard/ComplianceGauge';
import { ComplianceFlowWidget } from '@/components/dashboard/ComplianceFlowWidget';
import { MetricsCards } from '@/components/dashboard/MetricsCards';
import { DomainHeroSection } from '@/components/dashboard/DomainHeroSection';
import { AgenturPortfolioKarte } from '@/components/dashboard/AgenturPortfolioKarte';
import { AIComplianceCard } from '@/components/dashboard/AIComplianceCard';

export interface ModulKontext {
  userName?: string;
  planType?: string;
  scoreTrend: number | null;
}

export interface DashboardModul {
  id: string;
  titel: string;
  /** Ein Halbsatz, der im Anordnen-Modus erklärt, was das Modul zeigt. */
  beschreibung: string;
  icon: LucideIcon;
  spalte: Spalte;
  /**
   * Für welche Konten das Modul überhaupt existiert. Fehlt die Angabe, gilt
   * es für alle. Ein nicht verfügbares Modul taucht weder in der Ansicht noch
   * im Anordnen-Modus auf; seine Position im gespeicherten Layout bleibt
   * erhalten, falls sich der Tarif ändert.
   */
  verfuegbar?: (ctx: ModulKontext) => boolean;
  render: (ctx: ModulKontext) => ReactNode;
}

export const MODULKATALOG: DashboardModul[] = [
  {
    id: 'website',
    titel: 'Website-Analyse',
    beschreibung: 'Ihre Domain, Scan starten, letzter Stand',
    icon: Globe,
    spalte: 'haupt',
    render: () => <DomainHeroSection />,
  },
  {
    id: 'kennzahlen',
    titel: 'Kennzahlen',
    beschreibung: 'Befunde, Behobenes und Trend auf einen Blick',
    icon: BarChart3,
    spalte: 'haupt',
    render: () => <MetricsCards />,
  },
  {
    id: 'befunde',
    titel: 'Compliance-Analyse',
    beschreibung: 'Alle Befunde je Säule mit Fundstelle und Reparatur',
    icon: ClipboardList,
    spalte: 'haupt',
    render: () => <WebsiteAnalysis />,
  },
  {
    id: 'ablauf',
    titel: 'Compliance-Flow',
    beschreibung: 'Prüfen, Beheben, Nachweisen, Überwachen als Ablauf',
    icon: Workflow,
    spalte: 'haupt',
    render: () => <ComplianceFlowWidget />,
  },
  {
    id: 'rechtsnews',
    titel: 'Rechtsnews',
    beschreibung: 'Neue Rechtslage, die Ihre Seite betrifft',
    icon: Newspaper,
    spalte: 'haupt',
    render: () => <LegalNews />,
  },
  {
    id: 'cookies',
    titel: 'Cookie-Compliance',
    beschreibung: 'Banner, Einwilligungen und gefundene Dienste',
    icon: Cookie,
    spalte: 'haupt',
    render: () => <CookieComplianceWidget />,
  },
  {
    id: 'score',
    titel: 'Compliance-Score',
    beschreibung: 'Gesamtwert und Entwicklung zum Vormonat',
    icon: Gauge,
    spalte: 'seite',
    render: ({ userName, scoreTrend }) => <ComplianceGauge userName={userName} scoreTrend={scoreTrend} />,
  },
  {
    id: 'portfolio',
    titel: 'Agentur-Portfolio',
    beschreibung: 'Alle betreuten Websites im Überblick',
    icon: Layers,
    spalte: 'seite',
    // Gleiche Bedingung wie in AgenturPortfolioKarte selbst (istAgentur).
    verfuegbar: ({ planType }) => planType === 'agency' || planType === 'expert',
    render: () => <AgenturPortfolioKarte />,
  },
  {
    id: 'ki',
    titel: 'KI-Compliance',
    beschreibung: 'Pflichten aus dem AI Act für Ihre KI-Nutzung',
    icon: BrainCircuit,
    spalte: 'seite',
    render: () => <AIComplianceCard />,
  },
];

export const MODUL_JE_ID: ReadonlyMap<string, DashboardModul> = new Map(
  MODULKATALOG.map((m) => [m.id, m]),
);
