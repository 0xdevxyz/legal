import NextAuth from "next-auth";

declare module "next-auth" {
  interface User {
    id: string;
    email: string;
    full_name: string;
    company?: string;
    plan_type: string;
    role: string;
    onboarding_completed: boolean;
    active_modules: string[];
    accessToken: string;
    refreshToken: string;
  }

  interface Session {
    user: {
      id: string;
      email: string;
      full_name: string;
      company?: string;
      plan_type: string;
      role: string;
      onboarding_completed: boolean;
      active_modules: string[];
    };
    accessToken: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    full_name: string;
    company?: string;
    plan_type: string;
    role: string;
    onboarding_completed: boolean;
    active_modules: string[];
    accessToken: string;
    refreshToken: string;
  }
}
