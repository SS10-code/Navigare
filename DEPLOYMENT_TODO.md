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

## 2. Backend (FastAPI on Render)
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

## 3. Frontend (Next.js on Vercel)
- [ ] Create a new project at [vercel.com](https://vercel.com).
- [ ] Connect your GitHub repository containing the `navigare-web/` directory.
- [ ] Set **Root Directory** to `navigare-web/`.
- [ ] Add the following **Environment Variables**:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_RAILWAY_API_URL` (use your Render API URL here)
  - `NEXT_PUBLIC_AUTH_DISABLED` (set to `false` for production)
- [ ] Deploy.

## 4. Final Setup
- [ ] In Vercel, set your production domain (or use the auto-generated one).
- [ ] Update the `ALLOWED_ORIGINS` on Render with your final Vercel domain.
- [ ] Verify everything works!
