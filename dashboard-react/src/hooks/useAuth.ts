import { useSession, signIn, signOut } from "next-auth/react";

export function useAuth() {
  const { data: session, status, update } = useSession();

  const isLoading = status === "loading";
  const isAuthenticated = status === "authenticated";
  const user = session?.user ?? null;

  const login = async (email: string, password: string) => {
    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });
    if (result?.error) {
      throw new Error("Ungültige Zugangsdaten");
    }
    return { success: true };
  };

  const logout = async () => {
    await signOut({ redirect: false });
    window.location.href = "/login";
  };

  const markOnboardingCompleted = async () => {
    await update({ onboarding_completed: true });
  };

  return {
    user,
    accessToken: session?.accessToken ?? null,
    isLoading,
    isAuthenticated,
    login,
    logout,
    markOnboardingCompleted,
  };
}
