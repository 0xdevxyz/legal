# ADR-002: shadcn/ui v2 + Tailwind v4 als UI-Stack

Datum: 2026-05-22
Status: Accepted

## Context
Aktuelles UI verwendet @chakra-ui/react 2.x + Tailwind v3. Chakra bringt Emotion-Runtime-Overhead mit, ist nicht tree-shakeable und passt nicht zu Next.js App Router RSC. Tailwind v3 hat keine native CSS-Variable-First-Architektur.

## Decision
Migration auf shadcn/ui v2 + Tailwind v4 (CSS-First, OKLCH-Tokens).

## Consequences
- Alle bestehenden Chakra-Komponenten werden durch shadcn/ui-Äquivalente ersetzt
- globals.css: OKLCH-Farbtoken, CSS-Variables (--background, --foreground, etc.)
- components.json konfiguriert für New York style, typescript, tailwind v4
- next-themes für Dark/Light-Mode
- components/ui-v2/ als neues Komponentenverzeichnis
