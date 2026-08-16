-- ============================================
-- Navigare — Supabase Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid references auth.users primary key,
  store_name text,
  store_type text CHECK (store_type IN ('Retail', 'Food', 'Service', 'E-Commerce')),
  digest_email text,
  digest_day int default 1,
  digest_time text default '08:00',
  onboarded boolean default false,
  created_at timestamptz default now()
);

-- Transactions / Sales
CREATE TABLE IF NOT EXISTS public.transactions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  transaction_id text,
  transaction_date date not null,
  customer_id text,
  product_id text,
  product_name text,
  quantity int,
  line_total_usd numeric(10,2),
  category text,
  store_type text,
  uploaded_at timestamptz default now()
);

-- Inventory
CREATE TABLE IF NOT EXISTS public.inventory (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  product_id text not null,
  product_name text,
  category text,
  current_stock int default 0,
  retail_price numeric(10,2),
  cost_price numeric(10,2),
  reorder_threshold int default 10,
  last_updated timestamptz default now()
);

-- Digest send history
CREATE TABLE IF NOT EXISTS public.digest_log (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  sent_at timestamptz default now(),
  subject text,
  open_count int default 0
);

-- Guest sessions table to track guest events
CREATE TABLE IF NOT EXISTS public.guest_sessions (
  id uuid default gen_random_uuid() primary key,
  session_id uuid not null,
  user_id uuid references auth.users,
  event_type text not null,
  metadata jsonb,
  created_at timestamptz default now()
);

-- Conversion events table to track guest to authenticated user conversions
CREATE TABLE IF NOT EXISTS public.conversion_events (
  id uuid default gen_random_uuid() primary key,
  guest_session_id uuid not null references public.guest_sessions(session_id),
  user_id uuid not null references auth.users,
  converted_at timestamptz default now(),
  metadata jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_guest_sessions_session_id ON public.guest_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_guest_sessions_user_id ON public.guest_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_guest_session_id ON public.conversion_events(guest_session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_events_user_id ON public.conversion_events(user_id);

-- Row Level Security
ALTER TABLE public.profiles enable row level security;
ALTER TABLE public.transactions enable row level security;
ALTER TABLE public.inventory enable row level security;
ALTER TABLE public.digest_log enable row level security;
ALTER TABLE public.guest_sessions enable row level security;
ALTER TABLE public.conversion_events enable row level security;

-- RLS Policies
CREATE POLICY "own data" on public.profiles for all using (auth.uid() = id);
CREATE POLICY "own data" on public.transactions for all using (auth.uid() = user_id);
CREATE POLICY "own data" on public.inventory for all using (auth.uid() = user_id);
CREATE POLICY "own data" on public.digest_log for all using (auth.uid() = user_id);
CREATE POLICY "guests can write sessions" on public.guest_sessions for insert using (auth.uid() is null);
CREATE POLICY "users can read own guest sessions" on public.guest_sessions for select using (auth.uid() = user_id);
CREATE POLICY "users can read own conversion events" on public.conversion_events for select using (auth.uid() = user_id);
