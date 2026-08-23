type AnalyticsEvent = {
  name: string;
  data?: Record<string, unknown>;
};

class Analytics {
  private enabled: boolean;

  constructor() {
    this.enabled = typeof window !== "undefined";
  }

  track(name: string, data?: Record<string, unknown>) {
    if (!this.enabled) return;
    console.log("[analytics]", name, data);
  }
}

export const analytics = new Analytics();
