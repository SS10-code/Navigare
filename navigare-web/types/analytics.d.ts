interface Window {
  gtag?: (...args: unknown[]) => void;
  mixpanel?: {
    track: (event: string, properties?: Record<string, unknown>) => void;
    identify: (id: string) => void;
  };
}
