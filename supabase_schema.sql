-- Execute this in the Supabase SQL Editor

-- 1. Create Subjects Table (Engineering Classes)
create table public.subjects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  code text not null,
  description text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Create Resources Table
create table public.resources (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  type text not null check (type in ('video', 'pdf', 'note', 'github', 'textbook', 'pyq', 'link')),
  url text not null,
  description text,
  author_name text not null,
  subject_id uuid references public.subjects(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Create Bookmarks/Saved Table
create table public.saved_resources (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  resource_id uuid references public.resources(id) on delete cascade not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, resource_id)
);

-- Enable Row Level Security (RLS)
alter table public.subjects enable row level security;
alter table public.resources enable row level security;
alter table public.saved_resources enable row level security;

-- Policies for Subjects (Everyone can read, only authenticated can create)
create policy "Subjects are viewable by everyone" on public.subjects for select using (true);
create policy "Authenticated users can create subjects" on public.subjects for insert with check (auth.role() = 'authenticated');

-- Policies for Resources
create policy "Resources are viewable by everyone" on public.resources for select using (true);
create policy "Users can create resources" on public.resources for insert with check (auth.uid() = user_id);
create policy "Users can update their own resources" on public.resources for update using (auth.uid() = user_id);
create policy "Users can delete their own resources" on public.resources for delete using (auth.uid() = user_id);

-- Policies for Saved Resources
create policy "Users can view their own saved resources" on public.saved_resources for select using (auth.uid() = user_id);
create policy "Users can save resources" on public.saved_resources for insert with check (auth.uid() = user_id);
create policy "Users can unsave resources" on public.saved_resources for delete using (auth.uid() = user_id);
