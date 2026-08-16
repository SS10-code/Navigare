# 🧭 Navigare Deployment TODO

Follow these steps to deploy your production stack.

## 1. Supabase (Database & Auth)
- [ ] Create a new project at [supabase.com](https://supabase.com).
- [ ] Run the contents of `supabase-schema.sql` in the Supabase SQL Editor.
- [ ] Go to **Authentication > Providers** and enable **Email**.
- [ ] Under **Project Settings > API**, copy:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_KEY`

## 2. Guest Mode Tracking
- [ ] Create `guest_analytics` table in Supabase SQL Editor:
  ```sql
  CREATE TABLE guest_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  CREATE INDEX idx_guest_analytics_session ON guest_analytics(session_id);
  ```
- [ ] Enable **Row Level Security** on `guest_analytics`:
  ```sql
  ALTER TABLE guest_analytics ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Guests can read own analytics" ON guest_analytics
    FOR SELECT USING (auth.uid() IS NULL);
  ```
- [ ] Create a **Storage bucket** named `guest-uploads` (private, 50MB limit).
- [ ] Set up **Supabase Edge Function** or **pg_cron** to purge guest data after 30 days:
  ```sql
  SELECT cron.schedule('purge-guest-data', '0 0 * * *', $$
    DELETE FROM guest_analytics WHERE created_at < now() - interval '30 days';
  $$);
  ```
- [ ] Connect to your analytics tool (e.g., PostHog, Mixpanel) for guest event tracking.

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
  - `RESEND_API_KEY` (optional)
  - `ALLOWED_ORIGINS` (comma-separated list of your Vercel URL, e.g., `https://navigare.vercel.app`)
  - `GUEST_RATE_LIMIT` (e.g., `100` requests/hour)

## 4. Frontend (Next.js on Vercel)
- [ ] Create a new project at [vercel.com](https://vercel.com).
- [ ] Connect your GitHub repository containing the `navigare-web/` directory.
- [ ] Set **Root Directory** to `navigare-web/`.
- [ ] Add the following **Environment Variables**:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_RAILWAY_API_URL` (use your Render API URL here)
  - `NEXT_PUBLIC_AUTH_DISABLED` (set to `false` for production)
- [ ] Deploy.

## 6. Final Setup
- [ ] In Vercel, set your production domain (or use the auto-generated one).
- [ ] Update the `ALLOWED_ORIGINS` on Render with your final Vercel domain.
- [ ] Verify guest mode tracking works end-to-end.
- [ ] Verify everything works!
