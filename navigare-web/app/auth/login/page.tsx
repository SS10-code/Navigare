"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Icon from "@/components/Icon";
import { trackEmailSignup } from "@/lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const supabase = createClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setError(error.message);
    else {
      await trackEmailSignup();
      router.push("/dashboard/upload?onboarding=true");
    }
  };

  return (
    <div className="min-h-screen bg-paper text-ink flex items-center justify-center p-8">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-3">
            <Icon name="logo" size={32} className="text-accent" />
          </div>
          <h1 className="text-display text-2xl font-bold uppercase tracking-tight">Navigare</h1>
          <p className="text-caption text-muted text-[10px] mt-1">Sign in to your dashboard</p>
        </div>
        <div className="border-2 border-border bg-panel p-8">
          {error && (
            <div className="bg-accent/10 border-2 border-accent text-accent px-4 py-3 text-sm mb-6 font-mono">{error}</div>
          )}
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-caption text-muted text-[10px] block mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full"
                required
              />
            </div>
            <div>
              <label className="text-caption text-muted text-[10px] block mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full"
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full">Log In</button>
          </form>
        </div>
        <p className="text-center text-xs text-muted mt-6">
          Don't have an account? <a href="/auth/signup" className="text-accent hover:underline font-semibold">Sign up</a>
        </p>
      </div>
    </div>
  );
}
