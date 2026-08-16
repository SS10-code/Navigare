"use client";

/**
 * Check if the user is in guest mode via localStorage.
 * @returns {boolean} True if guest mode is enabled.
 */
export const isGuestMode = (): boolean => {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("navigare_guest_mode") === "true";
};

/**
 * Enable or disable guest mode.
 * @param {boolean} enabled - Whether to enable guest mode.
 */
export const setGuestMode = (enabled: boolean): void => {
  if (typeof window === "undefined") return;
  if (enabled) {
    localStorage.setItem("navigare_guest_mode", "true");
  } else {
    localStorage.removeItem("navigare_guest_mode");
  }
};