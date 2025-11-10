# Verdant v1 → v2 Migration Guide

This guide helps you migrate from the Flask/SQLAlchemy version to the new Supabase + React Native + Claude version.

## Overview

**What's changing:**
- Frontend: HTML/CSS/JS → React Native (Expo) mobile app
- Backend: Flask + SQLAlchemy → Supabase + FastAPI
- AI: Rule-based scheduling → Claude 3.5 Sonnet
- Auth: App-local → Supabase Auth (Email + Google OAuth)
- Weather: OpenWeather (keyed) → Open-Meteo (free)

## Migration Strategy

### Option 1: Fresh Start (Recommended)

**Best for:** Most users, new deployments

1. **Users**: Have users create new accounts in the mobile app
2. **Gardens**: Users recreate gardens via the wizard
3. **Schedules**: Generate new schedules with Claude (better than old ones!)
4. **Historical data**: Keep old database as reference only

**Pros:**
- Clean start with improved architecture
- No data transformation issues
- Users get immediate benefit of new AI

**Cons:**
- Users must sign up again
- Old schedules not directly accessible

### Option 2: Partial Migration

**Best for:** Organizations with many users, critical historical data

1. **Export** old database to CSV
2. **Import** produce requests and basic user info
3. **Users** sign up and get matched to imported goals
4. **Historical** schedules stored as notes/diagrams

**Pros:**
- Preserves user goals and preferences
- Can reference old schedules

**Cons:**
- More complex migration script
- Still requires new gardens/schedules

## Step-by-Step Migration

### Phase 1: Setup New Infrastructure (Week 1)

1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com
   # Create new project
   # Note: Project URL, anon key, service_role key
   ```

2. **Run Schema Migration**
   ```bash
   # In Supabase SQL Editor:
   # Copy/paste contents of supabase/migrations/001_initial_schema.sql
   # Execute
   ```

3. **Configure Auth Providers**
   - Enable Email (automatic)
   - Enable Google OAuth:
     - Get Google Client ID/Secret
     - Add redirect URIs for mobile app

4. **Deploy AI Service**
   ```bash
   # Choose: Render, Fly.io, or Cloud Run
   # See ai-service/README.md for instructions
   ```

5. **Configure Mobile App**
   ```bash
   cd mobile-app
   cp .env.example .env
   # Fill in Supabase credentials + AI service URL
   ```

### Phase 2: Data Export (Week 1)

1. **Export Old Data**
   ```bash
   cd scripts
   export OLD_DATABASE_URL="sqlite:///path/to/app.db"
   python migrate_to_supabase.py --export-only
   # Creates CSV files
   ```

2. **Review Exported Data**
   - `export_users.csv`: Usernames, contact info
   - `export_produce_requests.csv`: Goals, preferences
   - `export_schedules.csv`: Historical schedules

3. **Communicate to Users**
   - Email blast: "We're upgrading to a mobile app!"
   - Include: Migration date, benefits, sign-up instructions
   - Offer: Support for questions

### Phase 3: Pilot Testing (Week 2)

1. **Internal Testing**
   - Have 2-3 team members sign up
   - Complete full flow: wizard → generate → feedback
   - Fix any bugs

2. **Beta Testing**
   - Invite 5-10 friendly users
   - Gather feedback via TestFlight/Internal Testing
   - Iterate based on feedback

3. **Performance Testing**
   - Test Claude API latency
   - Check Supabase RLS performance
   - Verify weather caching works

### Phase 4: User Migration (Week 3)

**Option A: Fresh Start**

1. **Announce Migration**
   - Set date (e.g., next Monday)
   - Provide mobile app links
   - Include quick start guide

2. **Migration Day**
   - Turn off old Flask app (read-only mode)
   - Email users with sign-up link
   - Provide support channel (Slack, email)

3. **Onboarding**
   - Users sign up → complete wizard → generate schedule
   - Monitor sign-up success rate
   - Help users who struggle

**Option B: Gradual Migration**

1. **Dual Operation**
   - Keep Flask app running (read-only)
   - Launch mobile app in parallel
   - Let users transition at own pace

2. **Migration Incentives**
   - Early adopters: Featured user spotlight
   - Gamification: "First 100 users get..."
   - Value prop: Show new features

3. **Sunset Old App**
   - After 4 weeks, announce shutdown
   - Final reminder emails
   - Archive old database

### Phase 5: Post-Migration (Week 4+)

1. **Monitor Metrics**
   - Sign-up rate
   - Schedule generation success rate
   - Feedback submission rate
   - App crash rate

2. **User Support**
   - Respond to issues promptly
   - FAQ document based on common questions
   - Video tutorials for complex features

3. **Iterate**
   - Add requested features
   - Fix bugs
   - Improve AI prompts based on feedback

## Data Mapping

### Users

**Old (Flask):**
```python
User(
  id=1,
  username="john",
  password="hashed",
  role="user",
  phone_number="+1234567890",
  org_email="john@org.com"
)
```

**New (Supabase):**
```sql
-- auth.users (managed by Supabase)
id: uuid (auto-generated)
email: "john@org.com"
...

-- public.profiles
id: uuid (references auth.users)
username: "john"
role: "user"
phone_number: "+1234567890"
org_email: "john@org.com"
```

**Migration:**
- Users must sign up with their `org_email`
- After sign-up, populate `profiles` table
- Old passwords NOT migrated (security)

### ProduceRequest → produce_requests

**Old:**
```python
ProduceRequest(
  id=1,
  user_id=1,
  num_people=4,
  volume_goal=20.0,
  calorie_goal=5000.0,
  additional_needs="leafy greens",
  urgency=3
)
```

**New:**
```sql
produce_requests(
  id: uuid,
  owner_id: uuid,
  num_people: 4,
  volume_goal: 20.0,
  calorie_goal: 5000.0,
  additional_needs: "leafy greens",
  urgency: 3
)
```

**Migration:**
- Map `user_id` → `owner_id` (after user signs up)
- Can import this data if you have user mapping

### SavedSchedule → schedules + schedule_tasks

**Old:**
```python
SavedSchedule(
  id=1,
  user_id=1,
  name="Spring 2024",
  diagram="ASCII art...",
  schedule_json='[{"crop": "Tomatoes", ...}]'
)
```

**New:**
```sql
schedules(
  id: uuid,
  owner_id: uuid,
  garden_id: uuid,
  name: "Spring 2024",
  start_date: "2024-03-01",
  diagram: "ASCII art..."
)

schedule_tasks(
  id: uuid,
  schedule_id: uuid,
  week_index: 0,
  title: "Plant Tomatoes",
  due_date: "2024-03-01",
  status: "done"
)
```

**Migration:**
- Parse `schedule_json` into individual `schedule_tasks` rows
- Estimate `week_index` from order
- Calculate `due_date` from `start_date + week_index*7`
- Store old `diagram` as-is for reference

## Migration Script Usage

The provided script (`scripts/migrate_to_supabase.py`) is a **starting point**.

**What it does:**
- Exports old data to CSV
- Shows user mapping (old ID → new UUID)
- Creates produce_requests in Supabase

**What it doesn't do:**
- Create actual auth.users (requires Admin API or manual sign-up)
- Create gardens (users must use wizard)
- Fully parse and import schedules (too complex to automate)

**How to extend:**

1. **User Creation:**
   ```python
   # Use Supabase Admin API
   response = supabase.auth.admin.create_user({
       "email": user['org_email'],
       "password": "TempPassword123!",  # Force reset
       "email_confirm": True
   })
   ```

2. **Garden Creation:**
   ```python
   # Create default gardens for imported users
   garden = supabase.table('gardens').insert({
       'owner_id': new_user_id,
       'name': 'Imported Garden',
       'rows': 4,
       'cols': 8
   }).execute()
   ```

3. **Schedule Parsing:**
   ```python
   import json
   schedule_json = json.loads(old_schedule['schedule_json'])
   # Parse each entry, create tasks
   ```

## Testing the Migration

**Pre-Migration Checklist:**

- [ ] Supabase schema deployed
- [ ] AI service deployed and responding
- [ ] Mobile app built (TestFlight/Internal Track)
- [ ] Google OAuth configured
- [ ] Email templates customized (Supabase Auth)
- [ ] Migration script tested on staging data
- [ ] Backup of old database created

**During Migration:**

- [ ] Monitor sign-up rate (dashboard)
- [ ] Check Supabase error logs
- [ ] Test schedule generation (sample users)
- [ ] Verify RLS policies work
- [ ] Monitor Claude API usage/costs

**Post-Migration:**

- [ ] Survey users (satisfaction, issues)
- [ ] Check app store ratings
- [ ] Review crash reports (Sentry, etc.)
- [ ] Optimize slow queries (Supabase Dashboard)

## Rollback Plan

If critical issues arise:

1. **Immediate:**
   - Re-enable old Flask app
   - Announce temporary rollback
   - Disable new app sign-ups

2. **Investigation:**
   - Identify root cause
   - Fix in staging
   - Re-test

3. **Retry:**
   - Announce new migration date
   - Apply fixes
   - Migrate again

**Data Safety:**
- Keep old database backup for 90 days
- Supabase has point-in-time recovery
- Test restore process before migration

## Communication Templates

### Pre-Migration Email

```
Subject: Exciting Update: Verdant is Going Mobile! 🌱

Hi [User],

We're thrilled to announce a major upgrade to Verdant!

What's New:
• Mobile app (iOS + Android)
• AI-powered schedules (smarter than ever)
• Weather integration
• Real-time progress tracking
• Interactive garden map

Migration Details:
• Date: [Monday, March 1st]
• Action Required: Sign up in the new app
• Your data: Gardens and schedules will be fresh (better AI!)

Download Links:
• iOS: [TestFlight link]
• Android: [Play Store Internal Track]

Questions? Reply to this email or join our Slack channel.

Happy gardening!
The Verdant Team
```

### Migration Day Email

```
Subject: Verdant v2 is Live! Download Now

Hi [User],

The new Verdant app is officially live!

What to Do:
1. Download the app ([iOS] [Android])
2. Sign up with your email: [user@example.com]
3. Complete the garden wizard
4. Generate your first AI schedule

Need Help?
• Video tutorial: [link]
• FAQ: [link]
• Support: support@verdant.com

The old web app is now in read-only mode and will be shut down on [March 31st].

Let's grow together!
The Verdant Team
```

## FAQ

**Q: Will my old schedules be available?**
A: Historical schedules can be viewed in the old app (read-only). The new AI will generate better schedules based on your current garden.

**Q: Do I have to pay for the new app?**
A: Same pricing as before. [Or: Free during beta!]

**Q: What if I don't have a smartphone?**
A: We're planning a web version for Q3 2025. In the meantime, the old app remains in read-only mode.

**Q: My garden setup is complex. Can the wizard handle it?**
A: Yes! The wizard supports custom dimensions and existing plants. For very complex setups, contact support for assisted onboarding.

**Q: How do I cancel my account?**
A: Settings → Account → Delete Account. This removes all your data permanently.

## Success Metrics

Track these to measure migration success:

- **Sign-up Rate**: % of old users who sign up (target: 60%+)
- **Completion Rate**: % who complete wizard (target: 80%+)
- **Schedule Generation**: % who generate schedule (target: 70%+)
- **Retention**: % still active after 30 days (target: 50%+)
- **Satisfaction**: NPS score (target: 40+)

## Timeline Summary

| Week | Phase | Key Milestones |
|------|-------|----------------|
| 1 | Setup | Supabase, AI service, mobile app configured |
| 2 | Testing | Internal + beta testing complete |
| 3 | Migration | Users migrate, support active |
| 4+ | Stabilize | Monitor metrics, iterate on feedback |

## Conclusion

Migrating from v1 to v2 is a **reboot**, not a simple upgrade. The new architecture is fundamentally different and superior. Embrace the fresh start!

**Benefits of this approach:**
- ✅ Modern, mobile-first UX
- ✅ True AI (not rule-based)
- ✅ Scalable architecture (Supabase + serverless AI)
- ✅ Lower maintenance (no manual auth, backups, etc.)
- ✅ Extensible (easy to add new features)

Good luck with your migration! 🚀
