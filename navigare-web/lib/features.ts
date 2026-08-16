"use client";

import { isGuestMode } from "./auth";

/**
 * Check if a feature is enabled for the current user.
 * @param {string} feature - The feature key to check.
 * @returns {boolean} True if the feature is enabled.
 */
export const isFeatureEnabled = (feature: string): boolean => {
  const restrictedFeatures = [
    "rfm",
    "email_digest",
    "profit_optimizer",
    "seo_auditor",
  ];

  if (!restrictedFeatures.includes(feature)) return true;
  return !isGuestMode();
};

/**
 * Get a tooltip message for disabled features.
 * @param {string} feature - The feature key to check.
 * @returns {string | null} The tooltip message if the feature is disabled, otherwise null.
 */
export const getFeatureTooltip = (feature: string): string | null => {
  if (isFeatureEnabled(feature)) return null;
  return "This feature is disabled in guest mode. Create an account to unlock it.";
};