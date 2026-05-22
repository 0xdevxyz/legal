import { auth } from "@/auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export default auth(function middleware(req) {
  const { nextUrl, auth: session } = req;
  const isLoggedIn = !!session;

  const publicPaths = ["/login", "/register", "/auth/callback", "/forgot-password", "/reset-password"];
  const isPublic = publicPaths.some((p) => nextUrl.pathname.startsWith(p));

  if (isPublic) {
    if (isLoggedIn && (nextUrl.pathname === "/login" || nextUrl.pathname === "/register")) {
      return NextResponse.redirect(new URL("/", nextUrl));
    }
    return NextResponse.next();
  }

  if (!isLoggedIn) {
    const redirectUrl = new URL("/login", nextUrl);
    redirectUrl.searchParams.set("redirect", nextUrl.pathname);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*|public).*)"],
};
