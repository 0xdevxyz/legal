/**
 * Firebase Configuration & Initialization
 * 
 * Setup Instructions:
 * 1. Gehe zu https://console.firebase.google.com/
 * 2. Erstelle ein Projekt "Complyo"
 * 3. Authentication aktivieren (Email/Password, Google, Apple)
 * 4. Web App hinzufügen → Config kopieren
 * 5. Config in .env.local einfügen
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  UserCredential
} from 'firebase/auth';

// Firebase Config aus Environment Variables
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Check if Firebase is configured
const isFirebaseConfigured = Object.values(firebaseConfig).every(value => value && value !== 'undefined');

// Initialize Firebase (only once)
const app = !getApps().length && isFirebaseConfigured ? initializeApp(firebaseConfig) : getApps()[0];

// Get Auth instance
export const auth = isFirebaseConfigured ? getAuth(app) : null;

// Providers
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account' // Always show account picker
});

// Export Firebase status
export const isFirebaseEnabled = isFirebaseConfigured && auth !== null;

/**
 * Firebase Auth Methods
 */

export const firebaseAuth = {
  /**
   * Sign in with Google
   */
  signInWithGoogle: async (): Promise<UserCredential> => {
    if (!auth) throw new Error('Firebase not configured');
    return signInWithPopup(auth, googleProvider);
  },

  /**
   * Sign in with Email/Password
   */
  signInWithEmail: async (email: string, password: string): Promise<UserCredential> => {
    if (!auth) throw new Error('Firebase not configured');
    return signInWithEmailAndPassword(auth, email, password);
  },

  /**
   * Register with Email/Password
   */
  registerWithEmail: async (email: string, password: string): Promise<UserCredential> => {
    if (!auth) throw new Error('Firebase not configured');
    return createUserWithEmailAndPassword(auth, email, password);
  },

  /**
   * Sign out
   */
  signOut: async (): Promise<void> => {
    if (!auth) throw new Error('Firebase not configured');
    return signOut(auth);
  },

  /**
   * Listen to auth state changes
   */
  onAuthStateChanged: (callback: (user: User | null) => void) => {
    if (!auth) throw new Error('Firebase not configured');
    return onAuthStateChanged(auth, callback);
  },

  /**
   * Get current user's ID token
   */
  getIdToken: async (): Promise<string | null> => {
    if (!auth) throw new Error('Firebase not configured');
    const user = auth.currentUser;
    if (!user) return null;
    return user.getIdToken();
  }
};

// Log Firebase status (only in development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  if (isFirebaseEnabled) {

  } else {

  }
}

