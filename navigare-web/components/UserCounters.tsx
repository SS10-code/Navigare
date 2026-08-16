"use client";

import { useEffect, useState } from "react";
import { getCounters } from "@/lib/api";

type Counters = {
  email_signups: number;
  guest_sessions: number;
  total_users: number;
};

export default function UserCounters() {
  const [counters, setCounters] = useState<Counters>({ email_signups: 0, guest_sessions: 0, total_users: 0 });

  useEffect(() => {
    getCounters().then(setCounters);
  }, []);

  return (
    <div className="px-3 py-2 border-t border-border mt-auto">
      <div className="text-[9px] text-muted uppercase tracking-[0.2em] mb-2">Community</div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-sm font-black text-text">{counters.email_signups}</div>
          <div className="text-[9px] text-muted uppercase">Email</div>
        </div>
        <div>
          <div className="text-sm font-black text-text">{counters.guest_sessions}</div>
          <div className="text-[9px] text-muted uppercase">Guest</div>
        </div>
        <div>
          <div className="text-sm font-black text-teal">{counters.total_users}</div>
          <div className="text-[9px] text-muted uppercase">Total</div>
        </div>
      </div>
    </div>
  );
}
