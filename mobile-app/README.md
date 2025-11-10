# Verdant Mobile App (React Native + Expo)

Smart garden planning mobile app with AI-powered schedules and weather integration.

## Features

- 🔐 **Authentication**: Email/Password + Google OAuth via Supabase
- 🌱 **Garden Wizard**: Interactive setup with location permissions
- 🗺️ **Garden Map**: Visual grid-based layout editor
- 📅 **Schedule Management**: Week-by-week task tracking with progress
- 💬 **AI Feedback**: Submit observations and get adaptive schedule revisions
- 🌤️ **Weather Integration**: Location-aware forecasting
- 📱 **Native**: True mobile experience with offline caching

## Tech Stack

- **Framework**: React Native (Expo SDK 50)
- **Styling**: NativeWind (Tailwind CSS for RN)
- **State**: React Query + React Context
- **Auth**: Supabase Auth
- **Storage**: MMKV (fast, encrypted)
- **Location**: expo-location

## Prerequisites

- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator
- Expo Go app (for physical device testing)

## Setup

### 1. Install Dependencies

```bash
cd mobile-app
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000
```

**Important:**
- Use your Supabase **anon key** (not service role!)
- For local development, AI service URL can be `http://localhost:8000`
- For physical devices, use your computer's IP: `http://192.168.1.x:8000`

### 3. Run Development Server

```bash
npm start
```

This opens Expo Dev Tools. Choose:
- **Scan QR code** with Expo Go app (iOS/Android)
- Press **`i`** for iOS Simulator
- Press **`a`** for Android Emulator
- Press **`w`** for web (limited support)

## Project Structure

```
src/
├── api/
│   ├── supabase.ts          # Supabase client setup
│   └── ai-service.ts        # AI service API client
├── components/
│   └── GardenGrid.tsx       # Reusable garden map component
├── features/
│   ├── auth/
│   │   └── SignInScreen.tsx # Authentication UI
│   ├── garden/
│   │   └── GardenWizard.tsx # Garden setup flow
│   └── schedule/
│       ├── ScheduleScreen.tsx  # Main schedule view
│       └── FeedbackSheet.tsx   # Feedback submission
├── hooks/
│   └── useSession.ts        # Auth state hook
└── types/
    └── database.ts          # TypeScript types for Supabase
```

## Key Screens

### SignInScreen

- Email/password authentication
- Google OAuth (native redirect)
- Sign up flow with email confirmation
- Auto-login on app restart (persisted session)

### GardenWizard

**Step 1: Garden Details**
- Name, dimensions (rows × cols)
- Optional total area (m²)
- Location permission for weather

**Step 2: Goals**
- Number of people to feed
- Volume/calorie targets
- Additional needs (free text)
- Urgency level (1-5)

### ScheduleScreen

**Tasks View:**
- Grouped by week
- Checkbox to mark complete
- Quick feedback button per task

**Progress View:**
- Visual progress bar (% complete)
- Weekly breakdown
- Global feedback button

### FeedbackSheet

- Mood selector (5 emoji options)
- Free text input
- Helpful examples
- Submits to AI service → updates schedule

## Authentication Flow

```
1. App loads → useSession hook checks for existing session
2. No session → Show SignInScreen
3. User signs in → Supabase returns JWT
4. JWT stored in MMKV (encrypted)
5. Session persists across app restarts
6. All API calls include JWT in Authorization header
```

## Data Flow

```
Mobile App (Anon Key + RLS)
    ↓
Supabase (Postgres + Auth + RLS)
    ↑
AI Service (Service Role Key)
    ↓
Claude API
```

**Security:**
- Mobile app never has service role key
- RLS policies enforce data isolation
- All writes go through Supabase client (respects RLS)
- AI service reads user data using service key (trusted)

## Location Permissions

**iOS** (Info.plist):
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Verdant needs your location to provide weather forecasts for your garden.</string>
```

**Android** (app.json):
```json
"android": {
  "permissions": [
    "ACCESS_FINE_LOCATION",
    "ACCESS_COARSE_LOCATION"
  ]
}
```

Permissions requested in `GardenWizard` via `expo-location`.

## NativeWind (Tailwind) Usage

```tsx
import { View, Text } from 'react-native';

// Use className prop (just like web Tailwind)
<View className="flex-1 bg-white px-6 py-4">
  <Text className="text-2xl font-bold text-gray-900 mb-2">
    Hello Verdant
  </Text>
</View>
```

**Custom Colors:**
- `verdant-{shade}`: Green theme colors
- `charcoal-{shade}`: Dark neutral colors

Defined in `tailwind.config.js`.

## Building for Production

### EAS Build (Recommended)

```bash
# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Configure
eas build:configure

# Build iOS
eas build --platform ios --profile production

# Build Android
eas build --platform android --profile production

# Submit to App Store
eas submit --platform ios

# Submit to Play Store
eas submit --platform android
```

### Environment Variables for Production

Create `.env.production`:
```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EXPO_PUBLIC_AI_SERVICE_URL=https://your-production-ai-service.com
```

EAS will use this file when building with `--profile production`.

## Testing

### Type Checking

```bash
npx tsc --noEmit
```

### Linting

```bash
npx eslint src/
```

### Manual Testing Checklist

- [ ] Sign up with email
- [ ] Sign in with email
- [ ] Sign in with Google
- [ ] Complete garden wizard
- [ ] Grant location permission
- [ ] Generate schedule (calls AI service)
- [ ] Toggle task status
- [ ] Submit feedback
- [ ] App restart (session persists)

## Troubleshooting

### "Unable to resolve module 'react-native-url-polyfill'"

This is required for Supabase in React Native. Install:
```bash
npm install react-native-url-polyfill
```

Import in `src/api/supabase.ts`:
```ts
import 'react-native-url-polyfill/auto';
```

### "Google Sign In not working"

1. Enable Google OAuth in Supabase Dashboard
2. Add OAuth redirect URIs:
   - Development: `exp://127.0.0.1:19000`
   - Production: `com.verdant.app://auth/callback`
3. Ensure Google Client ID is configured
4. Test on real device (may not work in simulator)

### "Location permission denied"

- iOS: Check Info.plist has usage description
- Android: Check app.json has permissions
- Test on real device (simulator may not have location)

### "AI Service connection failed"

- Check `EXPO_PUBLIC_AI_SERVICE_URL` is correct
- For physical devices, use computer IP (not localhost)
- Ensure AI service is running
- Check firewall allows connections on port 8000

### "Session not persisting"

- MMKV storage requires expo-dev-client (not Expo Go)
- Build with EAS or expo-dev-client for full persistence
- Expo Go has limited storage capabilities

## Development Tips

### Hot Reloading

Expo supports hot module replacement. Changes to React components reload instantly. For native module changes, restart the app.

### Debugging

**Expo Dev Tools:**
- Press `m` to open developer menu
- Enable "Debug Remote JS" (opens Chrome DevTools)
- Use `console.log()` liberally

**React Native Debugger:**
Better alternative to Chrome DevTools:
```bash
brew install --cask react-native-debugger
```

**Supabase Debugging:**
- Check Supabase Dashboard → Authentication → Users
- View table data in Dashboard → Table Editor
- Check RLS policies in Dashboard → Authentication → Policies

### Performance

- Use `React.memo()` for expensive components
- Avoid inline functions in render (use `useCallback`)
- Lazy load screens with `React.lazy()`
- Optimize images with `expo-image`

## Deployment Checklist

Before releasing to app stores:

- [ ] Update version in `app.json`
- [ ] Set production environment variables
- [ ] Test on physical iOS device
- [ ] Test on physical Android device
- [ ] Configure Google OAuth redirect URIs
- [ ] Set up push notification certificates
- [ ] Configure app icons and splash screens
- [ ] Test sign up, sign in, schedule generation
- [ ] Verify RLS policies (users can't see others' data)
- [ ] Run type checking and linting
- [ ] Build with EAS
- [ ] Submit to TestFlight/Internal Testing
- [ ] Gather feedback from beta testers
- [ ] Submit to App Store / Play Store

## Resources

- **Expo Docs**: https://docs.expo.dev
- **Supabase React Native**: https://supabase.com/docs/guides/getting-started/tutorials/with-expo-react-native
- **NativeWind**: https://nativewind.dev
- **React Navigation**: https://reactnavigation.org
- **EAS Build**: https://docs.expo.dev/build/introduction

## Support

For issues specific to the mobile app:
1. Check this README
2. Check main project `VERDANT_V2_README.md`
3. Review Expo docs
4. Open an issue in the repo

---

**Happy gardening! 🌱**
