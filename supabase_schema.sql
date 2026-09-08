-- supabase_schema.sql
-- 即時對戰 MVP 用。到 Supabase SQL Editor 執行一次。
-- 注意：這是公開 MVP 寫法，方便 GitHub Pages 前端直接使用。
-- 正式營運前請再加強 RLS、防洗版與 rate limit。

create table if not exists public.battle_rooms (
  room_code text primary key,
  owner_id text not null,
  date text not null,
  challenge jsonb not null,
  status text not null default 'playing',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.battle_players (
  id uuid primary key default gen_random_uuid(),
  room_code text not null references public.battle_rooms(room_code) on delete cascade,
  player_id text not null,
  player_name text not null,
  score integer not null default 0,
  hits integer not null default 0,
  answers jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(room_code, player_id)
);

alter table public.battle_rooms enable row level security;
alter table public.battle_players enable row level security;

drop policy if exists "public read battle rooms" on public.battle_rooms;
drop policy if exists "public insert battle rooms" on public.battle_rooms;
drop policy if exists "public update battle rooms" on public.battle_rooms;
drop policy if exists "public read battle players" on public.battle_players;
drop policy if exists "public insert battle players" on public.battle_players;
drop policy if exists "public update battle players" on public.battle_players;

create policy "public read battle rooms"
on public.battle_rooms for select
using (true);

create policy "public insert battle rooms"
on public.battle_rooms for insert
with check (char_length(room_code) between 3 and 24);

create policy "public update battle rooms"
on public.battle_rooms for update
using (true)
with check (true);

create policy "public read battle players"
on public.battle_players for select
using (true);

create policy "public insert battle players"
on public.battle_players for insert
with check (
  char_length(room_code) between 3 and 24
  and char_length(player_name) between 1 and 24
);

create policy "public update battle players"
on public.battle_players for update
using (true)
with check (
  char_length(player_name) between 1 and 24
  and score >= 0
  and hits >= 0
);

alter publication supabase_realtime add table public.battle_players;
