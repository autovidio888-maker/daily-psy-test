create table if not exists battle_rooms (
  room_code text primary key,
  status text not null default 'waiting',
  host_name text not null,
  current_question int not null default 0,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz default now(),
  started_at timestamptz
);

alter table battle_rooms add column if not exists config jsonb not null default '{}'::jsonb;

create table if not exists battle_players (
  id uuid primary key default gen_random_uuid(),
  room_code text references battle_rooms(room_code) on delete cascade,
  player_name text not null,
  score int not null default 0,
  hits int not null default 0,
  answers jsonb not null default '[]'::jsonb,
  joined_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(room_code, player_name)
);

alter table battle_rooms enable row level security;
alter table battle_players enable row level security;

drop policy if exists "public read rooms" on battle_rooms;
drop policy if exists "public insert rooms" on battle_rooms;
drop policy if exists "public update rooms" on battle_rooms;
drop policy if exists "public delete rooms" on battle_rooms;
drop policy if exists "public read players" on battle_players;
drop policy if exists "public insert players" on battle_players;
drop policy if exists "public update players" on battle_players;
drop policy if exists "public delete players" on battle_players;

create policy "public read rooms" on battle_rooms for select using (true);
create policy "public insert rooms" on battle_rooms for insert with check (true);
create policy "public update rooms" on battle_rooms for update using (true);
create policy "public delete rooms" on battle_rooms for delete using (true);

create policy "public read players" on battle_players for select using (true);
create policy "public insert players" on battle_players for insert with check (true);
create policy "public update players" on battle_players for update using (true);
create policy "public delete players" on battle_players for delete using (true);

do $$
begin
  alter publication supabase_realtime add table battle_rooms;
exception
  when duplicate_object then null;
end $$;

do $$
begin
  alter publication supabase_realtime add table battle_players;
exception
  when duplicate_object then null;
end $$;
