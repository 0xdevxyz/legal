# ADR-003: Rollen-Modell admin / agency / customer

Datum: 2026-05-22
Status: Accepted

## Context
Die users-Tabelle hat kein role-Feld. Aktuell wird plan_type (free/pro/enterprise) als Proxy für Berechtigungen verwendet. Neue Features (Admin-Panel, Agency-Verwaltung) erfordern ein echtes RBAC-Modell.

## Decision
Drei Rollen: admin, agency, customer.
- admin: nur der Plattform-Owner (1 User), Zugang zu /api/admin/*, /app/admin/*
- agency: Wiederverkäufer, kann customer-Accounts verwalten, Zugang zu /app/agency/*
- customer: Endkunde, Standard-Rolle

## Consequences
- Migration: ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'customer'
- Bestehende Users bekommen role='customer'
- Admin-User wird manuell gesetzt via SQL
- RBAC-Decorator @require_role(["admin"]) auf admin_routes.py
- NextAuth session.user.role aus Backend-Response
