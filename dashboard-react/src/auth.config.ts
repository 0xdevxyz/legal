import type { NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";

const API_URL = process.env.NEXTAUTH_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const authConfig: NextAuthConfig = {
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const publicPaths = ["/login", "/register", "/auth/callback", "/forgot-password", "/reset-password"];
      const isPublic = publicPaths.some((p) => nextUrl.pathname.startsWith(p));

      if (isPublic) {
        if (isLoggedIn && (nextUrl.pathname === "/login" || nextUrl.pathname === "/register")) {
          return Response.redirect(new URL("/", nextUrl));
        }
        return true;
      }

      if (!isLoggedIn) {
        const redirectUrl = new URL("/login", nextUrl);
        redirectUrl.searchParams.set("redirect", nextUrl.pathname);
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
        token.accessTokenExpiresAt = (user as any).accessTokenExpiresAt ?? (Date.now() + 60 * 60 * 1000);
        token.error = undefined;
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

      const expiresAt = token.accessTokenExpiresAt as number | undefined;
      if (expiresAt && Date.now() > expiresAt - 5 * 60 * 1000) {
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
          const res = await fetch(`${API_URL}/api/auth/verify-credentials`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: parsed.data.email, password: parsed.data.password }),
          });

          if (!res.ok) return null;

          const user = await res.json();

          const tokenRes = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: parsed.data.email, password: parsed.data.password }),
          });

          if (!tokenRes.ok) return null;
          const tokenData = await tokenRes.json();

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
            accessTokenExpiresAt: Date.now() + 60 * 60 * 1000,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
};
