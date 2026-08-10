import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { tokenStorage } from "../api/tokenStorage";
import { fetchMe } from "../api/auth";
import type { UserOut } from "../types/api";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  isAuthenticated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!tokenStorage.getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const setTokens = useCallback(
    async (accessToken: string, refreshToken: string) => {
      tokenStorage.setTokens(accessToken, refreshToken);
      setLoading(true);
      await refreshUser();
    },
    [refreshUser],
  );

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, isAuthenticated: !!user, setTokens, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
