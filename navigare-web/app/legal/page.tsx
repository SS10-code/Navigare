"use client";

import Link from "next/link";
import Icon from "@/components/Icon";

export default function LegalPage() {
  return (
    <div className="min-h-screen bg-paper text-text flex items-center justify-center p-6">
      <div className="bg-panel border-2 border-border p-8 w-full max-w-2xl relative" style={{ boxShadow: "8px 8px 0 0 #423A8E" }}>
        <div className="absolute top-0 left-0 right-0 h-[4px] bg-gradient-to-r from-teal via-purple to-magenta" />
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Icon name="logo" size={32} className="text-teal" />
          </div>
          <h1 className="text-3xl font-black uppercase tracking-tight">Terms of Service</h1>
          <p className="label-mono text-[10px] text-muted mt-1">Last updated: August 2026</p>
        </div>

        <div className="space-y-6 text-sm text-muted leading-relaxed">
          <section>
            <h2 className="text-lg font-bold text-text mb-2">1. Acceptance of Terms</h2>
            <p>By accessing or using Navigare, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use the service.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">2. Description of Service</h2>
            <p>Navigare provides retail analytics, inventory tracking, sales forecasting, and related dashboard tools. The service is provided "as is" without warranties of any kind.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">3. User Accounts</h2>
            <p>You are responsible for maintaining the confidentiality of your account credentials. You agree to notify us immediately of any unauthorized use of your account.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">4. Data & Uploads</h2>
            <p>You retain ownership of any data you upload. By uploading data, you grant Navigare a limited license to process it solely for providing the service. We do not sell or share your data with third parties.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">5. Limitation of Liability</h2>
            <p>To the maximum extent permitted by law, Navigare shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or business opportunities arising from your use of the service.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">6. No Professional Advice</h2>
            <p>The analytics, forecasts, and recommendations provided by Navigare are for informational purposes only and do not constitute financial, accounting, or business advice. You should consult qualified professionals before making business decisions.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">7. Indemnification</h2>
            <p>You agree to indemnify and hold harmless Navigare and its operators from any claims, damages, losses, or expenses arising from your use of the service or violation of these terms.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">8. Changes to Terms</h2>
            <p>We reserve the right to modify these terms at any time. Continued use of the service after changes constitutes acceptance of the new terms.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-text mb-2">9. Contact</h2>
            <p>For questions about these terms, contact the service owner at the email associated with your account or deployment.</p>
          </section>
        </div>

        <div className="mt-8 text-center">
          <Link href="/dashboard" className="btn-secondary inline-block">
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
