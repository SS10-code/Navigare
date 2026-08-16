"use client";

export const isGuestMode = (): boolean => {
  if (typeof window === "undefined") return false;
  return document.cookie.split("; ").some((c) => c.startsWith("navigare_guest_mode=true"));
};

export const setGuestMode = (enabled: boolean): void => {
  if (typeof window === "undefined") return;
  if (enabled) {
    document.cookie = "navigare_guest_mode=true; path=/; max-age=" + 7 * 24 * 60 * 60;
  } else {
    document.cookie = "navigare_guest_mode=; path=/; max-age=0";
  }
};
