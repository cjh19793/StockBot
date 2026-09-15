-- StockBot: 관심종목/알림 스키마.
-- Supabase 대시보드 > SQL Editor 에서 1회 실행한다. (Alembic 등 마이그레이션 도구는
-- 이 프로젝트 규모상 과함 — 필요해지면 나중에 도입.)
--
-- auth.users 는 Supabase Auth가 관리하므로 별도 users 테이블은 만들지 않고 참조만 한다.
-- FastAPI 백엔드는 postgres 역할(테이블 소유자)로 접속해 RLS를 우회하지만, Supabase가
-- 자동 생성하는 PostgREST API(anon/authenticated 키)가 같은 테이블을 노출하므로 방어
-- 차원에서 모든 테이블에 RLS를 켜고 "자기 행만" 정책을 건다.

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  telegram_chat_id text,  -- 향후 텔레그램 알림 연동용 (MVP에서는 미사용)
  created_at timestamptz not null default now()
);

-- 신규 가입 시 profiles 행을 자동 생성.
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (user_id) values (new.id);
  return new;
end;
$$ language plpgsql security definer set search_path = public;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create table if not exists public.watchlist_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  ticker text not null,
  mode text not null default '기본',
  created_at timestamptz not null default now(),
  unique (user_id, ticker, mode)
);
create index if not exists idx_watchlist_items_user on public.watchlist_items(user_id);

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  ticker text not null,
  mode text not null default '기본',
  condition_type text not null
    check (condition_type in ('price_above', 'price_below', 'buy_score_above', 'sell_score_above')),
  condition_value double precision not null,
  is_active boolean not null default true,
  last_triggered_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists idx_alerts_user on public.alerts(user_id);
create index if not exists idx_alerts_active on public.alerts(is_active) where is_active;

create table if not exists public.alert_events (
  id uuid primary key default gen_random_uuid(),
  alert_id uuid not null references public.alerts(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  message text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_alert_events_user on public.alert_events(user_id, is_read);

alter table public.profiles enable row level security;
alter table public.watchlist_items enable row level security;
alter table public.alerts enable row level security;
alter table public.alert_events enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = user_id);
drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = user_id);

drop policy if exists "watchlist_select_own" on public.watchlist_items;
create policy "watchlist_select_own" on public.watchlist_items
  for select using (auth.uid() = user_id);
drop policy if exists "watchlist_insert_own" on public.watchlist_items;
create policy "watchlist_insert_own" on public.watchlist_items
  for insert with check (auth.uid() = user_id);
drop policy if exists "watchlist_delete_own" on public.watchlist_items;
create policy "watchlist_delete_own" on public.watchlist_items
  for delete using (auth.uid() = user_id);

drop policy if exists "alerts_select_own" on public.alerts;
create policy "alerts_select_own" on public.alerts
  for select using (auth.uid() = user_id);
drop policy if exists "alerts_insert_own" on public.alerts;
create policy "alerts_insert_own" on public.alerts
  for insert with check (auth.uid() = user_id);
drop policy if exists "alerts_update_own" on public.alerts;
create policy "alerts_update_own" on public.alerts
  for update using (auth.uid() = user_id);
drop policy if exists "alerts_delete_own" on public.alerts;
create policy "alerts_delete_own" on public.alerts
  for delete using (auth.uid() = user_id);

drop policy if exists "alert_events_select_own" on public.alert_events;
create policy "alert_events_select_own" on public.alert_events
  for select using (auth.uid() = user_id);
drop policy if exists "alert_events_update_own" on public.alert_events;
create policy "alert_events_update_own" on public.alert_events
  for update using (auth.uid() = user_id);
