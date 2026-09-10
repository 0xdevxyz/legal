import { auth } from "@/auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { istOeffentlich, istNurFuerGaeste } from "@/lib/oeffentliche-pfade";

export default auth(function middleware(req) {
  const { nextUrl, auth: session } = req;
  const isLoggedIn = !!session;

  const isPublic = istOeffentlich(nextUrl.pathname);

  if (isPublic) {
    if (isLoggedIn && istNurFuerGaeste(nextUrl.pathname)) {
      return NextResponse.redirect(new URL("/", nextUrl));
    }
    return NextResponse.next();
  }

  if (!isLoggedIn) {
    const redirectUrl = new URL("/login", nextUrl);
    // Mit Abfrage: /settings?tab=sicherheit soll nach dem Anmelden wieder
    // auf dem Sicherheits-Reiter landen, nicht auf dem ersten.
    redirectUrl.searchParams.set("redirect", nextUrl.pathname + nextUrl.search);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*|public|api/auth).*)"],
};
