# Running Both Web App and Mobile App Simultaneously

This guide explains how to run both the **original Flask web app (v1)** and the **new React Native mobile app (v2)** at the same time during the transition period.

## Architecture Overview

```
Verdant v1 (Flask Web App)
├── Port: 5000 (default)
├── Database: SQLite (app.db)
├── Tech: Flask, SQLAlchemy, Jinja2
└── Users: Web browser access

Verdant v2 (Mobile App + AI Service)
├── Mobile App: Expo (port 8081)
├── AI Service: FastAPI (port 8000)
├── Database: Supabase (cloud)
└── Users: iOS/Android native apps
```

## Quick Start (Run Everything)

### Terminal 1: Flask Web App (v1)

```bash
# Navigate to project root
cd /path/to/Verdant

# Activate virtual environment (if you have one)
# source venv/bin/activate

# Install Flask dependencies (if not already installed)
pip install flask flask-sqlalchemy pandas

# Run Flask app
python app.py
```

**Expected output:**
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

**Access:** http://localhost:5000

### Terminal 2: AI Service (v2)

```bash
# Navigate to AI service
cd /path/to/Verdant/ai-service

# Activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env (see LOCAL_DEVELOPMENT.md)
cp .env.example .env
# Edit .env with your Supabase + Anthropic credentials

# Run AI service
cd src
python main.py
```

**Expected output:**
```
INFO:     Database client initialized
INFO:     Claude service initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access:** http://localhost:8000

### Terminal 3: Mobile App (v2)

```bash
# Navigate to mobile app
cd /path/to/Verdant/mobile-app

# Install dependencies (first time only)
npm install

# Configure .env
cp .env.example .env
# Edit .env with your credentials

# Start Expo
npm start
```

**Expected output:**
```
› Metro waiting on exp://10.90.71.18:8081
› Scan the QR code above with Expo Go
```

**Access:** Scan QR code with phone or press 'w' for web

## Port Reference

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Flask Web App | 5000 | http://localhost:5000 | Original web interface |
| AI Service | 8000 | http://localhost:8000 | Claude + Supabase API |
| Metro Bundler | 8081 | exp://x.x.x.x:8081 | React Native bundler |

## Running Web Version of Mobile App

The mobile app can also run in a web browser:

```bash
cd mobile-app
npm start

# Then press 'w' for web
# Or run directly:
npm run web
```

This opens http://localhost:8081 in your browser with the React Native app rendered for web.

**Note:** Some features may not work in web mode:
- Location permissions (no native GPS)
- MMKV storage (falls back to localStorage)
- Some native components may render differently

## Which App to Use When

### Use Flask Web App (v1) for:
- ✅ Existing users who are comfortable with it
- ✅ Quick testing of old schedules
- ✅ No Supabase/API keys needed
- ✅ Simpler setup (just SQLite)
- ❌ No AI-powered schedules
- ❌ No mobile native features
- ❌ Rule-based scheduling only

### Use Mobile App (v2) for:
- ✅ AI-powered schedules with Claude
- ✅ Weather integration
- ✅ Progress tracking
- ✅ Feedback loop
- ✅ Native mobile experience
- ✅ Modern UI with Tailwind
- ❌ Requires Supabase + Anthropic setup
- ❌ More complex architecture

### Use Web Version of Mobile App for:
- ✅ Testing mobile app without a phone
- ✅ Desktop access to v2 features
- ✅ Quick debugging during development
- ⚠️ Some features may not work (location, etc.)

## Development Workflow

### Scenario 1: Developing v2 Features

```bash
# Terminal 1: AI Service (always needed for v2)
cd ai-service/src && python main.py

# Terminal 2: Mobile App
cd mobile-app && npm start

# Flask app not needed
```

### Scenario 2: Testing Migration

```bash
# Terminal 1: Flask Web App
python app.py

# Terminal 2: AI Service
cd ai-service/src && python main.py

# Terminal 3: Mobile App
cd mobile-app && npm start

# Compare features side-by-side
```

### Scenario 3: Production-like Testing

```bash
# Deploy AI service to Render/Fly.io
# Build mobile app with EAS
# Keep Flask app on existing server (read-only)

# Users can choose which version to use
```

## Sharing Data Between v1 and v2

**Important:** v1 and v2 use **different databases**:
- v1: SQLite (`app.db`)
- v2: Supabase (cloud Postgres)

They do **NOT** share data automatically.

### To migrate data from v1 to v2:

```bash
cd scripts
export OLD_DATABASE_URL="sqlite:///path/to/app.db"
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."

python migrate_to_supabase.py
```

See `MIGRATION_GUIDE.md` for full instructions.

### To reference old schedules in v2:

Users can:
1. View old schedules in Flask app (read-only)
2. Manually recreate gardens in mobile app
3. Generate new AI schedules (better than old ones!)

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000
# or
netstat -ano | grep 5000

# Kill the process
kill -9 <PID>

# Or use different port
flask run --port 5001
```

### Can't Access Flask App from Phone

The Flask app runs on `127.0.0.1` (localhost only). To access from phone:

```python
# Edit app.py
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')  # Add host='0.0.0.0'
```

Then access via `http://YOUR_COMPUTER_IP:5000`

### Mobile App Can't Connect to AI Service

If testing on physical device:

```bash
# In mobile-app/.env
EXPO_PUBLIC_AI_SERVICE_URL=http://YOUR_COMPUTER_IP:8000

# NOT http://localhost:8000 (won't work from phone)
```

### Browser Shows "Can't reach this page" for Web App

Make sure Flask is running:
```bash
python app.py
# Should show: * Running on http://127.0.0.1:5000
```

Then visit: http://localhost:5000 (or http://127.0.0.1:5000)

## Production Deployment Options

### Option 1: Parallel Deployment (Recommended)

```
Old System (v1):
├── Flask app on existing server
├── Keep running for 60 days
└── Set to read-only mode

New System (v2):
├── AI Service on Render/Fly.io
├── Mobile app via TestFlight/Play Store
└── Full feature set
```

**Migration:**
- Email users with new app links
- Keep old app accessible
- Gradual migration over 30-60 days
- Sunset old app after majority migrated

### Option 2: Immediate Cutover

```
Old System (v1):
└── Shut down immediately

New System (v2):
└── Full replacement
```

**Only recommended if:**
- Small user base (<50)
- Users are tech-savvy
- Can provide migration support

### Option 3: Feature Flagging

Add a feature flag to Flask app:

```python
# app.py
USE_NEW_SYSTEM = os.getenv("USE_V2", "false").lower() == "true"

@app.route("/generate_schedule", methods=["GET", "POST"])
def generate_schedule_view():
    if USE_NEW_SYSTEM:
        # Redirect to mobile app deep link
        return redirect("verdant://generate-schedule")
    else:
        # Old logic
        return render_template("schedule_form.html")
```

## Monitoring Both Apps

### Flask App (v1)

```bash
# Check if running
curl http://localhost:5000/health

# View logs
tail -f flask.log

# Check database
sqlite3 app.db "SELECT COUNT(*) FROM user;"
```

### AI Service (v2)

```bash
# Check if running
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "ok",
#   "service": "verdant-ai",
#   "database": "connected",
#   "ai": "connected"
# }

# View logs (shows in terminal)
```

### Mobile App (v2)

```bash
# Metro bundler status
# Look for "Metro waiting on exp://..."

# Test on web
open http://localhost:8081

# Check Expo DevTools
# Automatically opens at http://localhost:19002
```

## Cost Comparison

### v1 (Flask)
- Hosting: $5-10/month (VPS)
- Database: $0 (SQLite)
- APIs: $0
- **Total: ~$10/month**

### v2 (Mobile + AI)
- Hosting (AI service): $7/month (Render Starter)
- Database (Supabase): $0 (Free tier) or $25/month (Pro)
- Claude API: ~$0.50 per 100 schedules
- App Store fees: $99/year (iOS) + $25 one-time (Android)
- **Total: ~$30-60/month + app fees**

**Cost savings:**
- Free tier Supabase covers most small deployments
- Claude costs only when generating schedules
- Render free tier for AI service during development

## FAQ

**Q: Can I use the same database for both apps?**
A: No. v1 uses SQLite, v2 uses Supabase. They're architecturally different. Use the migration script to move data.

**Q: Do I need to run both forever?**
A: No. Run both during transition (30-60 days), then sunset v1.

**Q: Can I access v2 from a desktop browser?**
A: Yes! Run `npm run web` in mobile-app directory. But some native features won't work.

**Q: Which is better for production?**
A: v2 is superior (AI, weather, mobile-native). v1 is simpler if you don't want cloud dependencies.

**Q: Can I keep Flask app but use Claude AI?**
A: Yes! Call the AI service from Flask instead of rule-based scheduling. But you'd still need Supabase or add API endpoints to Flask.

**Q: What if I just want a web app, no mobile?**
A: Consider Next.js instead of React Native. Or run `npm run web` for mobile-app (works but not optimal for web-only).

## Summary

**To run everything locally:**

1. **Flask Web** (Terminal 1): `python app.py` → http://localhost:5000
2. **AI Service** (Terminal 2): `cd ai-service/src && python main.py` → http://localhost:8000
3. **Mobile App** (Terminal 3): `cd mobile-app && npm start` → Scan QR or press 'w'

**For production:**
- Deploy AI service to cloud (Render/Fly.io)
- Build mobile app with EAS
- Keep or sunset Flask app based on user needs

**Recommendation:**
- Start with parallel deployment
- Migrate users gradually
- Sunset v1 after 60 days

Happy developing! 🌱
