import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Navigare — Retail Analytics",
  description: "Ops dashboard for local business owners",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="text-body antialiased">
        {children}
      </body>
    </html>
  );
}
