# 🧭 Navigare Deployment TODO

Follow these steps to deploy your production stack.

## 1. Supabase (Database & Auth)
- [ ] Create a new project at [supabase.com](https://supabase.com).
- [ ] Run the contents of `supabase-schema.sql` in the Supabase SQL Editor (includes `guest_sessions`, `conversion_events` tables).
- [ ] Go to **Authentication > Providers** and enable **Email**.
- [ ] Under **Project Settings > API**, copy:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_KEY`

## 2. Guest Mode Tracking
- [ ] Verify `guest_sessions` and `conversion_events` tables exist (created via `supabase-schema.sql`).
- [ ] Enable **Row Level Security** on `guest_sessions`:
  ```sql
  ALTER TABLE guest_sessions ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Guests can read own sessions" ON guest_sessions
    FOR SELECT USING (auth.uid() IS NULL);
  CREATE POLICY "Service role can insert sessions" ON guest_sessions
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
  ```
- [ ] Enable **Row Level Security** on `conversion_events`:
  ```sql
  ALTER TABLE conversion_events ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Service role full access" ON conversion_events
    FOR ALL USING (auth.role() = 'service_role');
  ```
- [ ] Create a **Storage bucket** named `guest-uploads` (private, 50MB limit) for temporary guest CSV uploads.
- [ ] Set up **Supabase Edge Function** or **pg_cron** to purge guest data after 30 days:
  ```sql
  -- Using pg_cron (if available)
  SELECT cron.schedule('purge-guest-data', '0 0 * * *', $$
    DELETE FROM guest_sessions WHERE created_at < now() - interval '30 days' AND user_id IS NULL;
  $$);
  ```
- [ ] Connect to your analytics tool (GA4, Mixpanel, PostHog) for guest event tracking.
  - Add `NEXT_PUBLIC_GA_ID` or `NEXT_PUBLIC_MIXPANEL_TOKEN` to Vercel env vars.

## 3. Backend (FastAPI on Render)
- [ ] Create a new **Web Service** at [render.com](https://render.com).
- [ ] Connect your GitHub repository containing the `navigare-api/` directory.
- [ ] Set **Root Directory** to `navigare-api/`.
- [ ] Set **Build Command** to `pip install -r requirements.txt`.
- [ ] Set **Start Command** to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- [ ] Add the following **Environment Variables**:
  - `APP_SECRET` (generate a strong, random string)
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `RESEND_API_KEY` (optional, for email digests)
  - `ALLOWED_ORIGINS` (comma-separated list of your Vercel URL, e.g., `https://navigare.vercel.app`)
  - `GUEST_RATE_LIMIT` (e.g., `100` requests/hour)
- [ ] Verify the `/api/track` endpoint is accessible at `https://your-api.onrender.com/api/track`.

## 4. Frontend (Next.js on Vercel)
- [ ] Create a new project at [vercel.com](https://vercel.com).
- [ ] Connect your GitHub repository containing the `navigare-web/` directory.
- [ ] Set **Root Directory** to `navigare-web/`.
- [ ] Add the following **Environment Variables**:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_RAILWAY_API_URL` (use your Render API URL here)
  - `NEXT_PUBLIC_AUTH_DISABLED` (set to `false` for production)
  - `NEXT_PUBLIC_GA_ID` (optional, Google Analytics 4 Measurement ID)
  - `NEXT_PUBLIC_MIXPANEL_TOKEN` (optional, Mixpanel project token)
- [ ] Deploy.

## 5. Final Setup & Verification
- [ ] In Vercel, set your production domain (or use the auto-generated one).
- [ ] Update the `ALLOWED_ORIGINS` on Render with your final Vercel domain.
- [ ] **Test Guest Mode End-to-End:**
  1. Visit landing page → click "Use Without Account" → lands on dashboard.
  2. Upload a CSV → verify data processes client-side (no API calls to backend).
  3. Try restricted feature (e.g., RFM) → shows "Sign up to unlock" tooltip.
  4. Sign up → verify guest session links to user account (check `guest_sessions.user_id`).
- [ ] **Test Authenticated Mode:**
  1. Sign up → verify all features work (RFM, digests, alerts).
  2. Upload CSV → verify it hits `/api/inventory` etc.
- [ ] **Verify Tracking:**
  1. Check Supabase `guest_sessions` table for guest events.
  2. Check analytics tool (GA4/Mixpanel) for events.
  3. Check `conversion_events` when guest signs up.
- [ ] Verify everything works!

## 6. Post-Launch Monitoring
- [ ] Set up **Render health checks** for API.
- [ ] Set up **Vercel analytics** for frontend performance.
- [ ] Set up **Supabase alerts** for DB usage/errors.
- [ ] Schedule weekly review of guest → signup conversion rate.
- [ ] Plan guest data purge verification (monthly).