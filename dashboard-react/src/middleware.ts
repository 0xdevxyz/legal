import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware: Route Protection
 * 
 * Schützt das Dashboard vor unbefugtem Zugriff.
 * Nur authentifizierte Benutzer können auf geschützte Routen zugreifen.
 */

// Öffentliche Routen (kein Login erforderlich)
const publicRoutes = [
  '/login',
  '/register',
  '/auth/callback',
];

// Routen die explizit geschützt sind
const protectedRoutes = [
  '/',
  '/profile',
  '/subscription',
  '/journey',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Statische Assets und API-Routen durchlassen
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }
  
  // Prüfe ob Route öffentlich ist
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));
  
  // Token aus Cookie holen
  const token = request.cookies.get('access_token')?.value;
  
  // Wenn geschützte Route und kein Token → Redirect zu Login
  if (!isPublicRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // Wenn öffentliche Route (Login/Register) und Token vorhanden → Redirect zu Dashboard
  if (isPublicRoute && token && (pathname === '/login' || pathname === '/register')) {
    return NextResponse.redirect(new URL('/', request.url));
  }
  
  return NextResponse.next();
}

// Konfiguration: Auf welche Routen soll die Middleware angewendet werden
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|public).*)',
  ],
};
