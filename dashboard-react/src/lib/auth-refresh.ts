const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

let _inflightRefresh: Promise<string | null> | null = null;

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return (window as any).__complyo_access_token ?? null;
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  (window as any).__complyo_access_token = token;
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") return;
  delete (window as any).__complyo_access_token;
}

export async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  if (_inflightRefresh) return _inflightRefresh;

  _inflightRefresh = (async () => {
    try {
      const res = await fetch(`${API_URL}/api/auth/refresh-cookie`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) return null;

      const data = await res.json();
      const newToken: string | undefined = data.access_token;
      if (!newToken) return null;

      setAccessToken(newToken);

      const newExpiry = Date.now() + 60 * 60 * 1000;
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
