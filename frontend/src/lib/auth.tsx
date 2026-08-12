"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import * as api from "./api";
import type { User } from "./api";

interface AuthState {
  user: User | null;
  /** True until the first fetchMe() resolves, so the UI can avoid flashing "signed out". */
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signUp: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

/**
 * Holds the signed-in user for the whole app.
 *
 * Mounted in the root layout so every page shares one answer to "who is signed in?"
 * instead of each component asking the API separately. The mount-time fetchMe() call
 * doubles as the thing that seeds Django's CSRF cookie.
 */
export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .fetchMe()
      .then(setUser)
      // A failure here means the API is unreachable, which the map already surfaces;
      // treating it as "signed out" keeps the page usable rather than blank.
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    setUser(await api.login({ username, password }));
  }, []);

  const signUp = useCallback(async (username: string, password: string) => {
    setUser(await api.register({ username, password }));
  }, []);

  const signOut = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useUser(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useUser must be used inside a UserProvider.");
  }
  return context;
}
