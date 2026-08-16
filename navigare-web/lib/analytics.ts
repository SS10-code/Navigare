"use client";

import { apiFetch } from "./api";

type EventType =
  | "page_view"
  | "csv_upload"
  | "feature_usage"
  | "login"
  | "signup"
  | "guest_session_start";

type EventPayload = {
  event: EventType;
  userId?: string; // Authenticated user ID
  guestId?: string; // Guest session ID
  properties?: Record<string, unknown>;
  timestamp?: string;
};

class Analytics {
  private static instance: Analytics;
  private guestId: string | null = null;
  private ga4Enabled: boolean = false;
  private mixpanelEnabled: boolean = false;

  private constructor() {
    // Initialize guest ID from localStorage
    if (typeof window !== "undefined") {
      this.guestId = localStorage.getItem("guestId");
      if (!this.guestId) {
        this.guestId = this.generateGuestId();
        localStorage.setItem("guestId", this.guestId);
      }
      
      // Check for GA4 and Mixpanel
      this.ga4Enabled = !!window.gtag;
      this.mixpanelEnabled = !!window.mixpanel;
    }
  }

  public static getInstance(): Analytics {
    if (!Analytics.instance) {
      Analytics.instance = new Analytics();
    }
    return Analytics.instance;
  }

  private generateGuestId(): string {
    return `guest_${Math.random().toString(36).substring(2, 15)}_${Date.now()}`;
  }

  private async trackViaAPI(payload: EventPayload): Promise<void> {
    try {
      await apiFetch("/api/track", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error("Failed to track event via API:", error);
    }
  }

  private trackViaGA4(payload: EventPayload): void {
    if (!this.ga4Enabled || !window.gtag) return;
    
    window.gtag("event", payload.event, {
      ...payload.properties,
      user_id: payload.userId,
      guest_id: payload.guestId,
    });
  }

  private trackViaMixpanel(payload: EventPayload): void {
    if (!this.mixpanelEnabled || !window.mixpanel) return;
    
    window.mixpanel.track(payload.event, {
      ...payload.properties,
      distinct_id: payload.userId || payload.guestId,
    });
  }

  public async track(event: EventType, properties?: Record<string, unknown>): Promise<void> {
    const payload: EventPayload = {
      event,
      guestId: this.guestId || undefined,
      properties: properties || {},
      timestamp: new Date().toISOString(),
    };
    
    // Track via all available methods
    this.trackViaGA4(payload);
    this.trackViaMixpanel(payload);
    await this.trackViaAPI(payload);
  }

  public identify(userId: string): void {
    if (typeof window === "undefined") return;
    
    // GA4
    if (this.ga4Enabled && window.gtag) {
      window.gtag("set", "user_id", userId);
    }
    
    // Mixpanel
    if (this.mixpanelEnabled && window.mixpanel) {
      window.mixpanel.identify(userId);
    }
  }
}

export const analytics = Analytics.getInstance();