"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import * as api from "./api";
import type { User } from "./api";

interface LatLng {
  latitude: number;
  longitude: number;
}

interface AuthState {
  user: User | null;
  /** True until the first fetchMe() resolves, so the UI can avoid flashing "signed out". */
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signUp: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /**
   * Home/work location picking is armed from the header (AppHeader) but the point comes
   * from a map click (MapPanel/ReportMap) — living here, rather than in either component,
   * is what lets those two siblings share it without prop-drilling through page.tsx.
   */
  pickingLocation: "home" | "work" | null;
  /** The point clicked while picking, awaiting confirmation. */
  pendingLocationPoint: LatLng | null;
  armLocationPicking: (kind: "home" | "work") => void;
  setPendingLocationPoint: (point: LatLng) => void;
  cancelLocationPicking: () => void;
  /** Throws on failure (see api.updateMyLocation) — the caller decides how to show that. */
  confirmLocationPicking: () => Promise<void>;
  removeLocation: (kind: "home" | "work") => Promise<void>;
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
  const [pickingLocation, setPickingLocation] = useState<"home" | "work" | null>(null);
  const [pendingLocationPoint, setPendingLocationPointState] = useState<LatLng | null>(null);

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

  const armLocationPicking = useCallback((kind: "home" | "work") => {
    setPendingLocationPointState(null);
    setPickingLocation(kind);
  }, []);

  const setPendingLocationPoint = useCallback((point: LatLng) => {
    setPendingLocationPointState(point);
  }, []);

  const cancelLocationPicking = useCallback(() => {
    setPickingLocation(null);
    setPendingLocationPointState(null);
  }, []);

  const confirmLocationPicking = useCallback(async () => {
    if (!pickingLocation || !pendingLocationPoint) return;
    try {
      setUser(await api.updateMyLocation(pickingLocation, pendingLocationPoint));
    } finally {
      // Cleared whether or not the request succeeded — a failed save shouldn't leave the
      // map stuck in "click to pick" mode; the caller is responsible for showing the error.
      setPickingLocation(null);
      setPendingLocationPointState(null);
    }
  }, [pickingLocation, pendingLocationPoint]);

  const removeLocation = useCallback(async (kind: "home" | "work") => {
    setUser(await api.updateMyLocation(kind, null));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn,
        signUp,
        signOut,
        pickingLocation,
        pendingLocationPoint,
        armLocationPicking,
        setPendingLocationPoint,
        cancelLocationPicking,
        confirmLocationPicking,
        removeLocation,
      }}
    >
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
