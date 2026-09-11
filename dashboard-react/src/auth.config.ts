import type { NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { istOeffentlich, istNurFuerGaeste } from "@/lib/oeffentliche-pfade";

import { erneuereToken } from "@/lib/token-erneuerung";

// Laufzeit des Backend-Access-Tokens. Kommt aus derselben Umgebungsvariable,
// die das Backend liest (docker-compose.yml reicht sie beiden Diensten), damit
// beide dieselbe Zahl kennen. Bis zum 11.09.2026 standen hier 60 Minuten, das
// Backend praegte aber 15: das Dashboard hielt ein totes Token fuer gueltig,
// jede Anfrage lief in 401, und die Sitzung endete nach einer Viertelstunde.
// Ein Waechtertest haelt Standardwert und compose zusammen.
const ACCESS_TOKEN_LAUFZEIT_MS = Number(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || 480) * 60 * 1000;

// Wie lange vor dem Ablauf verlaengert wird: ein Drittel der Laufzeit, aber
// hoechstens 30 Minuten. Eine Sitzung, die in diesem Fenster irgendetwas
// abfragt, bekommt ein frisches Paar; eine, die erst nach dem Ablauf
// zurueckkommt, ebenfalls (der Refresh-Token gilt 30 Tage).
const ERNEUERN_VOR_ABLAUF_MS = Math.min(30 * 60 * 1000, Math.floor(ACCESS_TOKEN_LAUFZEIT_MS / 3));

const API_URL = process.env.NEXTAUTH_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
  // Zweiter Faktor. Optional: die meisten Konten haben keinen, und die
  // Anmeldeseite weiss vorher nicht, ob dieses hier einen hat.
  code: z.string().optional(),
});

export const authConfig: NextAuthConfig = {
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;

      // Die Liste steht in lib/oeffentliche-pfade. Dieser Rueckruf laeuft VOR
      // middleware.ts; solange beide ihre eigene Kopie hatten, war die dort
      // wirkungslos.
      if (istOeffentlich(nextUrl.pathname)) {
        if (isLoggedIn && istNurFuerGaeste(nextUrl.pathname)) {
          return Response.redirect(new URL("/", nextUrl));
        }
        return true;
      }

      if (!isLoggedIn) {
        const redirectUrl = new URL("/login", nextUrl);
        // Mit Abfrage: /settings?tab=sicherheit soll nach dem Anmelden wieder
        // auf dem Sicherheits-Reiter landen, nicht auf dem ersten.
        redirectUrl.searchParams.set("redirect", nextUrl.pathname + nextUrl.search);
        return Response.redirect(redirectUrl);
      }

      return true;
    },
    async jwt({ token, user, trigger, session }) {
      if (user) {
        token.id = user.id as string;
        token.email = user.email;
        token.full_name = user.full_name;
        token.company = user.company;
        token.plan_type = user.plan_type;
        token.role = user.role;
        token.onboarding_completed = user.onboarding_completed;
        token.active_modules = user.active_modules;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessTokenExpiresAt = (user as any).accessTokenExpiresAt ?? (Date.now() + ACCESS_TOKEN_LAUFZEIT_MS);
        token.error = undefined;
      }

      // Verlaengern, bevor das Token ablaeuft. Serverseitig, mit Sperre je
      // Refresh-Token (lib/token-erneuerung): das Backend dreht den
      // Refresh-Token und beendet bei doppeltem Einloesen alle Sitzungen des
      // Kontos. Vor dem 11.09.2026 stand hier nur ein Fehlerflag, auf das
      // AuthContext mit Abmeldung antwortete: die Sitzung endete mit dem
      // Token, verlaengert wurde nie.
      if (!user) {
        const expiresAt = token.accessTokenExpiresAt as number | undefined;
        const refreshToken = token.refreshToken as string | undefined;
        if (expiresAt && refreshToken && Date.now() > expiresAt - ERNEUERN_VOR_ABLAUF_MS) {
          const e = await erneuereToken(refreshToken, API_URL, ACCESS_TOKEN_LAUFZEIT_MS);
          if (e.status === "erneuert") {
            token.accessToken = e.paar.accessToken;
            token.refreshToken = e.paar.refreshToken;
            token.accessTokenExpiresAt = e.paar.expiresAt;
            token.error = undefined;
          } else if (e.status === "ungueltig" || Date.now() > expiresAt) {
            // Kette tot, oder abgelaufen und das Backend gerade nicht
            // erreichbar: ohne gueltiges Token gibt es nichts zu verlaengern.
            token.error = "RefreshAccessTokenError";
            return token;
          }
          // nicht_erreichbar vor dem Ablauf: altes Token gilt noch, naechster
          // Aufruf versucht es wieder.
        }
      }

      if (trigger === "update") {
        // Plan/Rolle/Module frisch aus dem Backend ziehen, damit Planwechsel
        // (z. B. nach Stripe-Checkout) ins JWT übernommen werden und einen
        // Seiten-Reload überleben. Ohne das bleibt plan_type auf dem Wert vom
        // Login stehen → Agentur-Paywall trotz bezahltem Abo.
        if (token.accessToken) {
          try {
            const res = await fetch(`${API_URL}/api/auth/session-info`, {
              headers: { Authorization: `Bearer ${token.accessToken as string}` },
            });
            if (res.ok) {
              const fresh = await res.json();
              token.plan_type = fresh.plan_type ?? token.plan_type;
              token.role = fresh.role ?? token.role;
              token.active_modules = fresh.active_modules ?? token.active_modules;
              token.onboarding_completed = fresh.onboarding_completed ?? token.onboarding_completed;
              token.company = fresh.company ?? token.company;
              token.full_name = fresh.full_name ?? token.full_name;
            }
          } catch {
            // Backend nicht erreichbar — bestehende Token-Werte behalten
          }
        }

        // Explizite Overrides aus update(...) anwenden (z. B. optimistisches
        // onboarding_completed-Flag), nachdem die frischen Backend-Werte gesetzt sind.
        if (session) {
          Object.assign(token, session);
          if ((session as any).accessTokenExpiresAt) {
            token.accessTokenExpiresAt = (session as any).accessTokenExpiresAt;
          }
        }
        token.error = undefined;
        return token;
      }

      // Kein Refresh-Token (Alt-Sitzung von vor der Umstellung, Social-Login
      // ohne Paar): dann endet die Sitzung mit dem Access-Token.
      const expiresAt = token.accessTokenExpiresAt as number | undefined;
      if (expiresAt && !token.refreshToken && Date.now() > expiresAt) {
        token.error = "RefreshAccessTokenError";
      }

      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      session.user.email = token.email as string;
      session.user.full_name = token.full_name as string;
      session.user.company = token.company as string | undefined;
      session.user.plan_type = token.plan_type as string;
      session.user.role = token.role as string;
      session.user.onboarding_completed = token.onboarding_completed as boolean;
      session.user.active_modules = token.active_modules as string[];
      session.accessToken = token.accessToken as string;
      (session as any).error = token.error;
      return session;
    },
  },
  providers: [
    Credentials({
      async authorize(credentials) {
        const parsed = loginSchema.safeParse(credentials);
        if (!parsed.success) return null;

        try {
          // EIN Anmeldeaufruf, nicht zwei.
          //
          // Vorher liefen hier /verify-credentials und /login nacheinander,
          // beide mit demselben Passwort. Mit zweitem Faktor geht das nicht
          // mehr: der Code gilt genau einmal, der zweite Aufruf waere eine
          // Wiederverwendung und wuerde zu Recht abgewiesen. Also einmal
          // anmelden, danach das Profil mit dem frischen Token holen —
          // /me liefert ohnehin mehr Felder als /verify-credentials.
          const res = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: parsed.data.email,
              password: parsed.data.password,
              code: parsed.data.code,
            }),
          });

          if (!res.ok) return null;
          const tokenData = await res.json();

          // Das Konto verlangt einen zweiten Faktor, und wir haben keinen
          // (gueltigen) mitgebracht. Die Anmeldeseite erkennt das an ihrer
          // eigenen Nachfrage und blendet das Codefeld ein.
          if (tokenData.mfa_required || !tokenData.access_token) return null;

          const meRes = await fetch(`${API_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${tokenData.access_token}` },
          });
          if (!meRes.ok) return null;
          const user = await meRes.json();

          return {
            id: String(user.id),
            email: user.email,
            full_name: user.full_name,
            company: user.company,
            plan_type: user.plan_type,
            role: user.role,
            onboarding_completed: user.onboarding_completed,
            active_modules: user.active_modules || [],
            accessToken: tokenData.access_token,
            refreshToken: tokenData.refresh_token,
            accessTokenExpiresAt: Date.now() + ACCESS_TOKEN_LAUFZEIT_MS,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
};
