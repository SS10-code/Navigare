"use client";

import { useState, useEffect } from "react";
import Icon from "@/components/Icon";
import Link from "next/link";
import { submitFeedback } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

const PLACEHOLDER_MESSAGES = new Set([
  "enter your message",
  "type here",
  "n/a",
  "none",
  "test",
  "placeholder",
  "lorem ipsum",
  "example",
]);

export default function Feedback() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getUserEmail = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user?.email) {
        setEmail(user.email);
      }
    };
    getUserEmail();
  }, []);

  const isPlaceholderText = (val: string) => {
    const normalized = val.trim().toLowerCase();
    return (
      normalized === "" ||
      normalized.length < 4 ||
      PLACEHOLDER_MESSAGES.has(normalized)
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    if (isPlaceholderText(message)) {
      setError("Please enter a meaningful message.");
      return;
    }

    setLoading(true);
    try {
      await submitFeedback(email, message);
      setSuccess(true);
      setEmail("");
      setMessage("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper text-ink flex items-center justify-center p-8">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-3">
            <Icon name="logo" size={32} className="text-accent" />
          </div>
          <h1 className="text-display text-2xl font-bold uppercase tracking-tight">
            Navigare
          </h1>
          <p className="text-caption text-muted text-[10px] mt-1">
            Send us your feedback
          </p>
        </div>

        <div className="border-2 border-border bg-panel p-8">
          {error && (
            <div className="bg-accent/10 border-2 border-accent text-accent px-4 py-3 text-sm mb-6 font-mono">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-paper border-2 border-ink text-ink px-4 py-3 text-sm mb-6 font-mono">
              Feedback sent! Thank you for helping improve Navigare.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-caption text-muted text-[10px] block mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full"
                required
                disabled={loading || success}
              />
            </div>

            <div>
              <label className="text-caption text-muted text-[10px] block mb-2">
                Message
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="How can we improve Navigare?"
                className="w-full min-h-[120px] resize-y"
                required
                disabled={loading || success}
              />
            </div>

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading || success}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Icon name="refresh" size={14} className="animate-spin" />
                  Sending...
                </span>
              ) : success ? (
                "Sent"
              ) : (
                "Send Feedback"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-muted mt-6">
          <Link
            href="/"
            className="text-accent hover:underline font-semibold"
          >
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
