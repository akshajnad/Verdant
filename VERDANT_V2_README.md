# Verdant v2 - Complete Rewrite Documentation

> **Full-stack rewrite from Flask/SQLAlchemy to React Native (Expo) + Supabase + Claude AI**

---

## 🌟 What's New in v2

### Architecture Changes

**Frontend:**
- ✅ **React Native (Expo)** mobile app replaces HTML/CSS/JS web interface
- ✅ **NativeWind (Tailwind)** for modern, responsive styling
- ✅ **Native location permissions** for accurate weather integration
- ✅ **Offline-first** with MMKV storage
- ✅ **Google OAuth** + Email/Password authentication

**Backend:**
- ✅ **Supabase** (Postgres + Auth + RLS) replaces SQLAlchemy
- ✅ **FastAPI AI Service** with **Claude 3.5 Sonnet** replaces rule-based scheduling
- ✅ **Open-Meteo** weather API (no key required) replaces OpenWeather
- ✅ **Row Level Security (RLS)** for data isolation
- ✅ **Service role key** server-side only (mobile uses anon key + RLS)

### New Features

1. **Interactive Garden Map** - Visual grid-based garden layout editor
2. **Progress Tracking** - Week-by-week completion tracking with percentages
3. **Location-Aware Weather** - Automatic weather forecasting based on garden location
4. **AI Feedback Loop** - Submit observations and Claude adapts your schedule
5. **Personalized Schedules** - Claude considers your goals, space, weather, and existing plants
6. **Multi-Week Planning** - 12+ week schedules with soil prep, planting, care, and harvest

---

## 📁 Project Structure

```
Verdant/
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql    # Complete Supabase schema
│
├── ai-service/                       # FastAPI AI Service
│   ├── src/
│   │   ├── main.py                   # FastAPI app
│   │   ├── models/schemas.py         # Pydantic models
│   │   ├── services/
│   │   │   ├── claude.py             # Claude integration
│   │   │   └── weather.py            # Weather API
│   │   └── utils/database.py         # Supabase client
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── mobile-app/                       # React Native (Expo)
│   ├── src/
│   │   ├── api/
│   │   │   ├── supabase.ts           # Supabase client
│   │   │   └── ai-service.ts         # AI service client
│   │   ├── components/
│   │   │   └── GardenGrid.tsx        # Garden map component
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   └── SignInScreen.tsx  # Auth UI
│   │   │   ├── garden/
│   │   │   │   └── GardenWizard.tsx  # Garden setup
│   │   │   └── schedule/
│   │   │       ├── ScheduleScreen.tsx
│   │   │       └── FeedbackSheet.tsx
│   │   └── hooks/
│   │       └── useSession.ts         # Auth hook
│   ├── App.tsx
│   ├── package.json
│   ├── .env.example
│   └── README.md
│
├── scripts/
│   └── migrate_to_supabase.py        # Data migration tool
│
├── app.py                            # [LEGACY] Old Flask app
├── templates/                        # [LEGACY] Old templates
└── VERDANT_V2_README.md             # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Supabase Account** → [supabase.com](https://supabase.com)
- **Anthropic API Key** → [anthropic.com](https://console.anthropic.com)
- **Python 3.11+** (for AI service)
- **Node.js 18+** (for mobile app)
- **Expo CLI** → `npm install -g expo-cli`

### 1. Setup Supabase

```bash
# 1. Create a new Supabase project at https://supabase.com

# 2. Run the schema migration
# Copy contents of supabase/migrations/001_initial_schema.sql
# Paste into Supabase SQL Editor and execute

# 3. Enable Auth Providers
# Go to Authentication → Providers
# Enable: Email, Google OAuth
# For Google: Add redirect URIs for your Expo app

# 4. Copy your credentials
# Project Settings → API
# Copy: Project URL, anon key, service_role key
```

### 2. Setup AI Service

```bash
cd ai-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_SERVICE_ROLE_KEY=eyJ...
#   ANTHROPIC_API_KEY=sk-ant-...

# Run development server
cd src
python main.py

# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 3. Setup Mobile App

```bash
cd mobile-app

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   EXPO_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
#   EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJ...
#   EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000

# Start Expo
npm start

# Scan QR code with Expo Go app (iOS/Android)
# Or press 'i' for iOS simulator, 'a' for Android emulator
```

---

## 🔐 Authentication Flow

1. User opens app → sees Sign In/Sign Up screen
2. User signs up with email/password or Google OAuth
3. Supabase creates user in `auth.users` table
4. App auto-creates profile in `public.profiles` table
5. User proceeds to Garden Wizard
6. All subsequent API calls use Supabase JWT (anon key + RLS)

**Security:**
- Mobile app uses **anon key** (safe to expose)
- AI service uses **service role key** (server-only)
- RLS policies ensure users only see their own data
- No secrets in mobile app code

---

## 🌱 User Journey

### First Time Setup

1. **Sign In** → Create account (email or Google)
2. **Garden Wizard**:
   - Name your garden
   - Set dimensions (rows × cols)
   - Optionally enter total area (m²)
   - Grant location permission for weather
3. **Set Goals**:
   - Number of people to feed
   - Volume/calorie targets
   - Additional needs (e.g., "leafy greens")
   - Urgency level (1-5)
4. **Generate Schedule** → Calls AI service → Claude creates personalized plan

### Using the App

**Schedule Screen:**
- **Tasks View**: Grouped by week with checkboxes
- **Progress View**: Visual progress bar + weekly breakdown
- **Add Feedback**: Submit observations for any task

**Feedback Loop:**
1. User submits feedback (e.g., "Heavy rain all week")
2. AI service analyzes with Claude
3. Schedule tasks updated/rescheduled automatically
4. User sees revised plan immediately

---

## 🧠 AI Service Details

### Endpoints

**`POST /ai/generate_schedule`**

Creates a new planting schedule.

Request:
```json
{
  "user_id": "uuid",
  "garden_id": "uuid",
  "schedule_name": "Spring 2025",
  "start_date": "2025-03-01"
}
```

Response:
```json
{
  "schedule_id": "uuid",
  "diagram": "ASCII garden layout",
  "tasks": [
    {
      "week_index": 0,
      "title": "Prepare soil in rows 0-1",
      "description": "Turn compost into top 6 inches...",
      "plant_catalog_id": null,
      "due_date": "2025-03-01"
    }
  ]
}
```

**`POST /ai/revise_schedule`**

Revises schedule based on user feedback.

Request:
```json
{
  "schedule_id": "uuid",
  "task_id": "uuid",
  "text": "It's been raining heavily, plants are waterlogged",
  "mood": "concerned"
}
```

Response:
```json
{
  "ok": true,
  "message": "Schedule updated to account for excess rain...",
  "updated_tasks": ["task-uuid-1", "task-uuid-2"]
}
```

### Claude Prompt Strategy

The AI service builds rich context for Claude:

- **Garden layout**: Dimensions, existing plants, available space
- **User goals**: People, volume, calories, preferences
- **Weather forecast**: 14-day forecast with rain/temp patterns
- **Plant catalog**: Spacing, cycle time, water/sun needs
- **Growth stage**: Current week in schedule

Claude returns **structured JSON** with:
- Week-by-week tasks (soil prep → planting → care → harvest)
- Specific locations (e.g., "Row 0, Columns 0-3")
- Weather-aware timing (avoid frost, schedule watering around rain)
- Companion planting suggestions
- Maintenance reminders

---

## 📊 Database Schema (Supabase)

### Core Tables

**`profiles`** - User profile data
- Extends `auth.users`
- Fields: username, role, phone_number, org_email

**`gardens`** - Garden configurations
- Fields: owner_id, name, rows, cols, area_m2, location_lat/lon, timezone

**`garden_cells`** - Grid cell assignments
- Fields: garden_id, r, c, plant_catalog_id, label

**`plant_catalog`** - Supported plants (seeded)
- Fields: common_name, spacing_cm, cycle_weeks, water_need, sun_requirement, kcal_per_100g

**`schedules`** - AI-generated schedules
- Fields: owner_id, garden_id, name, start_date, diagram, version

**`schedule_tasks`** - Individual tasks
- Fields: schedule_id, week_index, title, description, due_date, status

**`schedule_feedback`** - User feedback
- Fields: schedule_id, task_id, text, mood, ai_response

**`weather_cache`** - Cached weather data
- Fields: garden_id, date, provider, payload (JSONB)

All tables have **RLS enabled** with policies checking `auth.uid()`.

---

## 🔄 Data Migration

To migrate from the old Flask app:

```bash
cd scripts

# Set environment variables
export OLD_DATABASE_URL="sqlite:///path/to/app.db"
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."

# Run migration
python migrate_to_supabase.py
```

**Important:**
- Users must sign up again (old passwords are not migrated)
- Gardens must be recreated via the wizard
- Old schedules serve as historical reference
- Consider this a **fresh start** with imported goals

---

## 🚢 Deployment

### AI Service

**Render:**
```bash
# 1. Connect repo in Render dashboard
# 2. Set build command: pip install -r ai-service/requirements.txt
# 3. Set start command: cd ai-service/src && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
# 4. Add environment variables
```

**Fly.io:**
```bash
fly launch
fly secrets set SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... ANTHROPIC_API_KEY=...
fly deploy
```

**Cloud Run:**
```bash
gcloud run deploy verdant-ai \
  --source ai-service \
  --region us-central1 \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,ANTHROPIC_API_KEY=...
```

### Mobile App

**EAS Build:**
```bash
cd mobile-app

# Install EAS CLI
npm install -g eas-cli

# Configure
eas build:configure

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

**Environment Variables:**
- Set production URLs in `.env.production`
- Use EAS Secrets for sensitive values

---

## 🧪 Testing

### AI Service

```bash
# Unit tests
pytest ai-service/tests/

# Test Claude integration (requires API key)
pytest ai-service/tests/test_claude.py -v

# Load testing
locust -f ai-service/tests/load_test.py
```

### Mobile App

```bash
# Type checking
npx tsc --noEmit

# Linting
npx eslint src/

# E2E tests (requires Detox setup)
npm run test:e2e
```

### Manual Testing Checklist

- [ ] Sign up with email
- [ ] Sign in with Google
- [ ] Complete garden wizard with location
- [ ] Generate schedule (verify Claude returns valid JSON)
- [ ] Toggle task completion
- [ ] Submit feedback with different moods
- [ ] Verify schedule updates after feedback
- [ ] Check RLS (try accessing another user's data)

---

## 🐛 Troubleshooting

### "Missing Supabase environment variables"

Ensure `.env` files exist and contain valid credentials:
```bash
# AI service
ai-service/.env

# Mobile app
mobile-app/.env
```

### "Failed to fetch weather"

- Check garden has location_lat/lon set
- Verify Open-Meteo API is accessible
- Check network connectivity

### "Claude returned invalid JSON"

- Claude occasionally returns markdown-wrapped JSON
- AI service includes error handling and retries
- Check `ANTHROPIC_API_KEY` is valid
- Review prompt in `services/claude.py`

### "Schedule generation slow"

- First call is slowest (fetches weather, calls Claude)
- Weather is cached for 24 hours
- Claude calls take 3-10 seconds (streaming not implemented yet)
- Consider adding loading states

### RLS Policy Errors

- Verify user is authenticated (`auth.uid()` is not null)
- Check policy definitions in migration SQL
- Use Supabase Dashboard → Authentication → Policies to debug

---

## 📈 Future Enhancements

### v2.1 - Polish
- [ ] Push notifications for upcoming tasks
- [ ] Photo upload for feedback (Supabase Storage)
- [ ] Calendar integration (iOS/Android native)
- [ ] Dark mode

### v2.2 - Collaboration
- [ ] Multi-garden support per user
- [ ] Sharing gardens with other users
- [ ] Role-based permissions (admin, editor, viewer)

### v2.3 - Intelligence
- [ ] Plant health photo recognition (Claude vision)
- [ ] Historical yield tracking
- [ ] Crop rotation suggestions
- [ ] Pest/disease identification

### v2.4 - Scale
- [ ] Offline queueing (background sync)
- [ ] Multi-language support (i18n)
- [ ] Community sharing (public schedules)
- [ ] Marketplace integration (seed suppliers)

---

## 📚 Additional Resources

- **Supabase Docs**: https://supabase.com/docs
- **Expo Docs**: https://docs.expo.dev
- **Claude API**: https://docs.anthropic.com
- **NativeWind**: https://nativewind.dev
- **Open-Meteo**: https://open-meteo.com/en/docs

---

## 👥 Contributing

This is a full rewrite. Key architectural decisions:

1. **Mobile-first**: Native app provides better UX for location, photos, notifications
2. **Supabase**: Reduces backend code, RLS is simpler than custom auth
3. **Claude**: Far superior to rule-based scheduling, adapts to feedback
4. **Normalized schema**: Tasks as separate rows enable granular tracking

If contributing:
- Follow TypeScript/Python typing conventions
- Add tests for new features
- Update this README with new endpoints/screens

---

## 📝 License

Same as original Verdant project.

---

## 🙏 Acknowledgments

- Original Verdant Flask app team
- Supabase for amazing developer experience
- Anthropic for Claude API
- Expo team for React Native tooling

---

**Questions?** Open an issue or check individual README files in `ai-service/` and `mobile-app/`.
