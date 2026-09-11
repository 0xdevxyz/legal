const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

let _inflightRefresh: Promise<string | null> | null = null;

// Der Server antwortet mit 204, wenn gar kein refresh_token-Cookie mitkommt.
// Das ist keine Stoerung, sondern eine Absage: ohne Cookie wird auch der
// naechste Versuch nichts finden. Bis zum 09.09. wurde sie wie ein leeres
// Ergebnis behandelt, und jede weitere 401-Antwort loeste einen neuen Versuch
// aus — gemessen 13 Anlaeufe in 44 Minuten, die letzten drei mit 429 vom
// Rate-Limit. Ab der ersten Absage wird nicht mehr gefragt, bis wieder ein
// Token gesetzt ist.
let _ohneSitzung = false;

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return (window as any).__complyo_access_token ?? null;
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  (window as any).__complyo_access_token = token;
  // Wieder angemeldet: die Absage von vorhin gilt nicht mehr.
  _ohneSitzung = false;
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") return;
  delete (window as any).__complyo_access_token;
}

export async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  if (_ohneSitzung) return null;
  if (_inflightRefresh) return _inflightRefresh;

  _inflightRefresh = (async () => {
    try {
      const res = await fetch(`${API_URL}/api/auth/refresh-cookie`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      // 204 zaehlt fuer fetch als Erfolg, traegt aber keinen Rumpf: es gibt
      // kein Cookie, aus dem sich etwas erneuern liesse.
      if (res.status === 204) {
        _ohneSitzung = true;
        return null;
      }

      if (!res.ok) return null;

      const data = await res.json();
      const newToken: string | undefined = data.access_token;
      if (!newToken) return null;

      setAccessToken(newToken);

      const newExpiry = Date.now() + 480 * 60 * 1000; // wie ACCESS_TOKEN_EXPIRE_MINUTES
      try {
        const { getSession } = await import("next-auth/react");
        const session = await Promise.race([
          getSession(),
          new Promise<null>((resolve) => setTimeout(() => resolve(null), 2000)),
        ]);
        if (session) {
          const nextAuthReact = await import("next-auth/react") as any;
          const update = nextAuthReact.update ?? nextAuthReact.default?.update;
          if (update) await update({ accessToken: newToken, accessTokenExpiresAt: newExpiry });
        }
      } catch {}

      return newToken;
    } catch {
      return null;
    } finally {
      _inflightRefresh = null;
    }
  })();

  return _inflightRefresh;
}
