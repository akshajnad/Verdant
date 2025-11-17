# Local Development Guide

This guide will help you run Verdant v2 locally on your machine for development and testing.

## Prerequisites

- Python 3.11+ (for AI service)
- Node.js 18+ (for mobile app)
- Supabase account (free tier is fine)
- Anthropic API key (Claude)

## Quick Start (5 minutes)

### 1. Set up Supabase

```bash
# 1. Go to https://supabase.com and create a free account
# 2. Create a new project
# 3. Wait for the database to initialize (~2 minutes)
# 4. Go to SQL Editor and paste the contents of:
#    supabase/migrations/001_initial_schema.sql
# 5. Click "Run" to create all tables
# 6. Go to Settings → API and copy:
#    - Project URL
#    - anon public key
#    - service_role key (keep this secret!)
```

### 2. Get Anthropic API Key

```bash
# 1. Go to https://console.anthropic.com
# 2. Sign up or log in
# 3. Go to API Keys
# 4. Create a new key
# 5. Copy it (starts with sk-ant-...)
```

### 3. Run the AI Service

```bash
# Navigate to AI service directory
cd ai-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=eyJhbG...  (service role, not anon!)
# ANTHROPIC_API_KEY=sk-ant-...

# Run the server
cd src
python main.py
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/ai-service/src']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Database client initialized
INFO:     Claude service initialized
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test it:**
- Open browser to http://localhost:8000
- You should see:
  ```json
  {
    "service": "Verdant AI Service",
    "version": "2.0.0",
    "status": "running",
    "configuration": "configured",
    ...
  }
  ```
- Visit http://localhost:8000/docs for interactive API documentation

### 4. Run the Mobile App

```bash
# In a NEW terminal window

# Navigate to mobile app directory
cd mobile-app

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# EXPO_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
# EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...  (anon key, not service role!)
# EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000

# For physical devices, replace localhost with your computer's IP:
# EXPO_PUBLIC_AI_SERVICE_URL=http://192.168.1.x:8000

# Start Expo
npm start
```

**Expected output:**
```
› Metro waiting on exp://192.168.1.x:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

› Press a │ open Android
› Press i │ open iOS simulator
› Press w │ open web

› Press j │ open debugger
› Press r │ reload app
› Press m │ toggle menu
```

**Test it:**
- Scan QR code with Expo Go app (iOS/Android)
- OR press 'i' for iOS Simulator
- OR press 'a' for Android Emulator
- App should load and show Sign In screen

## Common Issues

### AI Service says "Missing environment variables"

**Symptom:**
```
http://localhost:8000/ shows:
{
  "warning": "Missing environment variables: SUPABASE_URL, ..."
}
```

**Solution:**
1. Make sure you created `.env` file in `ai-service/` directory
2. Check the file has correct credentials (not the `.env.example` placeholders)
3. Restart the server (`Ctrl+C` then `python main.py` again)

### Mobile app can't connect to AI service

**Symptom:**
```
Network request failed
or
Connection refused
```

**Solution:**

If testing on physical device:
1. Make sure your phone and computer are on the same WiFi network
2. Find your computer's IP address:
   - Mac: System Preferences → Network
   - Windows: `ipconfig` in Command Prompt
   - Linux: `ip addr show`
3. Update `.env`:
   ```
   EXPO_PUBLIC_AI_SERVICE_URL=http://192.168.1.x:8000
   ```
4. Restart Expo (`Ctrl+C` then `npm start`)

If testing on simulator/emulator:
- iOS Simulator: Use `http://localhost:8000`
- Android Emulator: Use `http://10.0.2.2:8000`

### Supabase RLS errors

**Symptom:**
```
new row violates row-level security policy
```

**Solution:**
1. Make sure you ran the full migration SQL (includes RLS policies)
2. Check you're using the correct keys:
   - AI service: **service_role** key
   - Mobile app: **anon** key
3. Verify user is authenticated before calling protected endpoints

### Claude API errors

**Symptom:**
```
authentication_error: invalid x-api-key
or
rate_limit_error: ...
```

**Solution:**
1. Check your `ANTHROPIC_API_KEY` is correct
2. Verify your API key has credits: https://console.anthropic.com/settings/billing
3. Check rate limits (free tier has limits)

## Development Workflow

### Making changes to AI Service

```bash
# The server auto-reloads when you save files
# Just edit files in ai-service/src/ and save
# Check terminal for any errors
```

### Making changes to Mobile App

```bash
# Expo has hot reloading
# Just save your files and the app updates automatically
# For some changes you may need to shake device → Reload
```

### Testing API endpoints

Use the interactive docs at http://localhost:8000/docs

Example: Test schedule generation
1. Click "POST /ai/generate_schedule"
2. Click "Try it out"
3. Edit the JSON request:
   ```json
   {
     "user_id": "your-user-uuid",
     "garden_id": "your-garden-uuid",
     "schedule_name": "Test Schedule",
     "start_date": "2025-03-01"
   }
   ```
4. Click "Execute"
5. See response with generated schedule

### Viewing Supabase data

1. Go to https://app.supabase.com
2. Select your project
3. Click "Table Editor" in sidebar
4. Browse your tables:
   - `profiles` - user data
   - `gardens` - garden configurations
   - `schedules` - generated schedules
   - `schedule_tasks` - individual tasks
   - `schedule_feedback` - user feedback

## Next Steps

Once you have everything running:

1. **Create a test account**
   - Open mobile app
   - Sign up with email
   - Verify email (check Supabase Auth → Users)

2. **Complete garden wizard**
   - Fill in garden details
   - Grant location permission (if on device)
   - Set your goals

3. **Generate a schedule**
   - Click "Generate Schedule"
   - Wait 5-10 seconds for Claude
   - View your personalized schedule!

4. **Test feedback**
   - Mark a few tasks complete
   - Submit feedback (e.g., "It rained heavily")
   - See how Claude adapts the schedule

## Debugging Tips

### Enable debug logging (AI Service)

Edit `ai-service/src/main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    ...
)
```

### Enable debug mode (Mobile App)

In Expo:
- Shake device → "Debug Remote JS"
- Opens Chrome DevTools
- See console.log() output

### Check Supabase logs

1. Go to Supabase Dashboard
2. Click "Logs" → "Postgres Logs"
3. See all database queries in real-time

### Monitor Claude API usage

1. Go to https://console.anthropic.com/settings/usage
2. See API calls and token usage
3. Each schedule generation uses ~500-2000 tokens

## Environment Variables Reference

### AI Service (.env)

```bash
# Required
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...  # ⚠️ Keep secret!
ANTHROPIC_API_KEY=sk-ant-...         # ⚠️ Keep secret!

# Optional
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

### Mobile App (.env)

```bash
# Required
EXPO_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...  # ✅ Safe to expose
EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000

# Note: EXPO_PUBLIC_ prefix makes it available in app
# Only use this prefix for non-sensitive data!
```

## Performance Tips

1. **Weather caching**: Weather is cached for 24 hours. First schedule generation is slower.

2. **Claude response time**: Typically 3-10 seconds. Can't speed this up (it's the API).

3. **Database queries**: Already indexed. Should be fast (<100ms).

4. **Mobile app**: Use React Query for caching. Already configured.

## Security Notes

**⚠️ NEVER commit `.env` files to git!**

Already in `.gitignore`, but double check:
```bash
# Should show nothing
git status | grep .env
```

**Service vs Anon keys:**
- **Service role key**: Full database access, bypasses RLS. Only for server!
- **Anon key**: Limited access, respects RLS. Safe for mobile app.

**In production:**
- Use environment variables (not .env files)
- Rotate keys regularly
- Enable IP restrictions on Supabase
- Use HTTPS only

## Getting Help

If you're stuck:

1. Check this guide first
2. Read the main `VERDANT_V2_README.md`
3. Check component README files:
   - `ai-service/README.md`
   - `mobile-app/README.md`
4. Review error messages carefully
5. Check Supabase logs
6. Open an issue on GitHub

## Useful Commands

```bash
# AI Service
cd ai-service
source venv/bin/activate
python src/main.py                    # Run server
pip install -r requirements.txt       # Install deps
pip list                              # Show installed packages

# Mobile App
cd mobile-app
npm start                             # Start Expo
npm install                           # Install deps
npm ls                               # Show installed packages
npx expo-doctor                      # Check for issues

# Git
git status                           # Check status
git pull                             # Get latest changes
git checkout -b feature/my-feature   # New branch

# Supabase CLI (optional)
npx supabase init                    # Initialize
npx supabase db push                 # Push migrations
npx supabase db reset                # Reset database
```

Happy coding! 🌱
