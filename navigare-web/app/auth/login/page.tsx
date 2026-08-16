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
      router.push("/dashboard/upload");
    }
  };

  return (
    <div className="min-h-screen bg-paper text-text flex items-center justify-center p-6">
      <div className="bg-panel border-2 border-border p-8 w-full max-w-sm relative" style={{ boxShadow: "8px 8px 0 0 #423A8E" }}>
        <div className="absolute top-0 left-0 right-0 h-[4px] bg-gradient-to-r from-teal via-purple to-magenta" />
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Icon name="logo" size={32} className="text-teal" />
          </div>
          <h1 className="text-3xl font-black uppercase tracking-tight">Navigare</h1>
          <p className="label-mono text-[10px] text-muted mt-1">Sign in to your dashboard</p>
        </div>
        {error && (
          <div className="bg-[#2E0A10] border-2 border-red text-red px-4 py-2 text-sm mb-4 font-mono">{error}</div>
        )}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="label-mono block text-[10px] font-bold text-muted mb-1.5">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full" required />
          </div>
          <div>
            <label className="label-mono block text-[10px] font-bold text-muted mb-1.5">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full" required />
          </div>
          <button type="submit" className="btn-primary w-full">Log In</button>
        </form>
        <p className="text-center text-xs text-muted mt-4">
          Don't have an account? <a href="/auth/signup" className="text-teal hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
}
