-- =====================================================
-- Verdant v2 - Initial Supabase Schema Migration
-- =====================================================
-- This migration creates all tables for the Verdant v2 rewrite
-- replacing the Flask/SQLAlchemy models with Supabase tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "moddatetime" SCHEMA extensions;

-- =====================================================
-- 1) PROFILES TABLE (extends auth.users)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  role TEXT DEFAULT 'user',
  phone_number TEXT,
  org_email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update timestamp trigger
CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- =====================================================
-- 2) GARDENS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS public.gardens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'My Garden',
  area_m2 NUMERIC CHECK (area_m2 >= 0),
  rows INT DEFAULT 4 CHECK (rows >= 1),
  cols INT DEFAULT 8 CHECK (cols >= 1),
  location_lat NUMERIC,
  location_lon NUMERIC,
  location_accuracy_m NUMERIC,
  timezone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER set_gardens_updated_at
  BEFORE UPDATE ON public.gardens
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- =====================================================
-- 3) GARDEN CELLS (per-cell plant placement)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.garden_cells (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  garden_id UUID NOT NULL REFERENCES public.gardens(id) ON DELETE CASCADE,
  r INT NOT NULL,
  c INT NOT NULL,
  plant_catalog_id UUID,
  label TEXT,
  CONSTRAINT unique_cell UNIQUE (garden_id, r, c)
);

-- =====================================================
-- 4) PLANT CATALOG (static database of supported plants)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.plant_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  common_name TEXT NOT NULL,
  scientific_name TEXT,
  spacing_cm INT,
  cycle_weeks INT,
  water_need TEXT CHECK (water_need IN ('low','medium','high')),
  sun_requirement TEXT CHECK (sun_requirement IN ('shade','partial','full')),
  kcal_per_100g NUMERIC,
  notes TEXT
);

-- =====================================================
-- 5) PLANT INSTANCES (actual plantings in gardens)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.plant_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  garden_id UUID NOT NULL REFERENCES public.gardens(id) ON DELETE CASCADE,
  plant_catalog_id UUID NOT NULL REFERENCES public.plant_catalog(id),
  cell_r INT,
  cell_c INT,
  started_on DATE,
  weeks_grown INT DEFAULT 0,
  meta JSONB
);

-- =====================================================
-- 6) PRODUCE REQUESTS (maps old ProduceRequest model)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.produce_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  num_people INT DEFAULT 0,
  volume_goal NUMERIC DEFAULT 0,
  calorie_goal NUMERIC DEFAULT 0,
  additional_needs TEXT DEFAULT '',
  shelter_notes TEXT DEFAULT '',
  urgency INT DEFAULT 1,
  status TEXT DEFAULT 'new',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 7) SCHEDULES (normalized version of SavedSchedule)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  garden_id UUID NOT NULL REFERENCES public.gardens(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  start_date DATE NOT NULL,
  is_favorite BOOLEAN DEFAULT FALSE,
  diagram TEXT,
  version INT DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER set_schedules_updated_at
  BEFORE UPDATE ON public.schedules
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- =====================================================
-- 8) SCHEDULE TASKS (atomic steps from AI)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.schedule_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES public.schedules(id) ON DELETE CASCADE,
  week_index INT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  plant_catalog_id UUID REFERENCES public.plant_catalog(id),
  due_date DATE,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','in_progress','done','skipped')),
  notes TEXT
);

-- =====================================================
-- 9) SCHEDULE FEEDBACK (user → AI feedback loop)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.schedule_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES public.schedules(id) ON DELETE CASCADE,
  task_id UUID REFERENCES public.schedule_tasks(id) ON DELETE CASCADE,
  submitted_at TIMESTAMPTZ DEFAULT NOW(),
  mood TEXT,
  text TEXT NOT NULL,
  photos JSONB,
  ai_response TEXT
);

-- =====================================================
-- 10) WEATHER CACHE (avoid redundant API calls)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.weather_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  garden_id UUID NOT NULL REFERENCES public.gardens(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  provider TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT unique_weather_cache UNIQUE (garden_id, date, provider)
);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gardens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.garden_cells ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plant_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.produce_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schedule_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.schedule_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weather_cache ENABLE ROW LEVEL SECURITY;

-- Profiles: users can only access their own profile
CREATE POLICY "profiles_self_access"
  ON public.profiles FOR ALL
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

-- Gardens: users own their gardens
CREATE POLICY "own_gardens"
  ON public.gardens FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- Garden cells: access through garden ownership
CREATE POLICY "own_cells"
  ON public.garden_cells FOR ALL
  USING (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  )
  WITH CHECK (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  );

-- Plant instances: access through garden ownership
CREATE POLICY "own_plant_instances"
  ON public.plant_instances FOR ALL
  USING (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  )
  WITH CHECK (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  );

-- Produce requests: users own their requests
CREATE POLICY "own_produce_requests"
  ON public.produce_requests FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- Schedules: users own their schedules
CREATE POLICY "own_schedules"
  ON public.schedules FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- Schedule tasks: access through schedule ownership
CREATE POLICY "own_tasks"
  ON public.schedule_tasks FOR ALL
  USING (
    schedule_id IN (SELECT id FROM public.schedules WHERE owner_id = auth.uid())
  )
  WITH CHECK (
    schedule_id IN (SELECT id FROM public.schedules WHERE owner_id = auth.uid())
  );

-- Feedback: access through schedule ownership
CREATE POLICY "own_feedback"
  ON public.schedule_feedback FOR ALL
  USING (
    schedule_id IN (SELECT id FROM public.schedules WHERE owner_id = auth.uid())
  )
  WITH CHECK (
    schedule_id IN (SELECT id FROM public.schedules WHERE owner_id = auth.uid())
  );

-- Weather cache: access through garden ownership
CREATE POLICY "own_weather"
  ON public.weather_cache FOR ALL
  USING (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  )
  WITH CHECK (
    garden_id IN (SELECT id FROM public.gardens WHERE owner_id = auth.uid())
  );

-- =====================================================
-- SEED DATA: Common plants for the catalog
-- =====================================================
INSERT INTO public.plant_catalog (common_name, scientific_name, spacing_cm, cycle_weeks, water_need, sun_requirement, kcal_per_100g, notes) VALUES
  ('Tomatoes', 'Solanum lycopersicum', 60, 10, 'medium', 'full', 18, 'Requires staking or cages'),
  ('Potatoes', 'Solanum tuberosum', 30, 12, 'medium', 'full', 77, 'Hill soil as plants grow'),
  ('Carrots', 'Daucus carota', 5, 10, 'medium', 'full', 41, 'Loose soil required for straight roots'),
  ('Lettuce', 'Lactuca sativa', 20, 6, 'high', 'partial', 15, 'Quick growing, succession plant'),
  ('Kale', 'Brassica oleracea', 40, 8, 'medium', 'partial', 49, 'Cold hardy, harvest outer leaves'),
  ('Onions', 'Allium cepa', 10, 14, 'medium', 'full', 40, 'Long growing season'),
  ('Bell Peppers', 'Capsicum annuum', 45, 12, 'medium', 'full', 20, 'Warm season crop'),
  ('Zucchini', 'Cucurbita pepo', 90, 8, 'high', 'full', 17, 'Prolific producer'),
  ('Corn', 'Zea mays', 30, 10, 'medium', 'full', 86, 'Plant in blocks for pollination'),
  ('Beans', 'Phaseolus vulgaris', 10, 8, 'medium', 'full', 31, 'Bush or pole varieties'),
  ('Spinach', 'Spinacia oleracea', 15, 6, 'high', 'partial', 23, 'Cool season crop'),
  ('Radishes', 'Raphanus sativus', 5, 4, 'medium', 'full', 16, 'Very fast growing')
ON CONFLICT DO NOTHING;

-- =====================================================
-- INDEXES for performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_gardens_owner ON public.gardens(owner_id);
CREATE INDEX IF NOT EXISTS idx_garden_cells_garden ON public.garden_cells(garden_id);
CREATE INDEX IF NOT EXISTS idx_schedules_owner ON public.schedules(owner_id);
CREATE INDEX IF NOT EXISTS idx_schedules_garden ON public.schedules(garden_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_schedule ON public.schedule_tasks(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_due_date ON public.schedule_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_feedback_schedule ON public.schedule_feedback(schedule_id);
CREATE INDEX IF NOT EXISTS idx_weather_cache_garden_date ON public.weather_cache(garden_id, date);

-- =====================================================
-- COMMENTS for documentation
-- =====================================================
COMMENT ON TABLE public.profiles IS 'User profile data extending auth.users';
COMMENT ON TABLE public.gardens IS 'Garden configurations with location and dimensions';
COMMENT ON TABLE public.garden_cells IS 'Individual cells in the garden grid';
COMMENT ON TABLE public.plant_catalog IS 'Static catalog of supported plant species';
COMMENT ON TABLE public.plant_instances IS 'Actual planted crops in gardens';
COMMENT ON TABLE public.produce_requests IS 'User requests for produce planning';
COMMENT ON TABLE public.schedules IS 'AI-generated planting schedules';
COMMENT ON TABLE public.schedule_tasks IS 'Individual tasks within a schedule';
COMMENT ON TABLE public.schedule_feedback IS 'User feedback for AI adaptation';
COMMENT ON TABLE public.weather_cache IS 'Cached weather forecast data';
