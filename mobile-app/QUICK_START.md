# Quick Start - Getting the Mobile App Running

The mobile app has NativeWind (Tailwind CSS) configuration that can cause issues. Here's how to get it working quickly:

## Option 1: Simplified App (No Dependencies)

Use the simplified version that doesn't require Supabase/API setup:

```bash
cd mobile-app

# Backup original App.tsx
mv App.tsx App.full.tsx

# Use simplified version
cp App.simple.tsx App.tsx

# Clear cache and start
rm -rf node_modules/.cache
npm start

# Press 'w' for web or 'i' for iOS simulator
```

This shows a welcome screen and confirms the app works.

## Option 2: Fix NativeWind Issues

If you want the full app with all features:

### Step 1: Install Missing Dependencies

```bash
cd mobile-app
npm install @babel/runtime
npm install react-native-web react-dom
npm install postcss
```

### Step 2: Clear All Caches

```bash
# Clear npm cache
rm -rf node_modules/.cache

# Clear Metro bundler cache
npx expo start --clear

# Or completely reset
rm -rf node_modules
npm install
npx expo start --clear
```

### Step 3: Use the Full App

```bash
# Restore full version if you backed it up
mv App.full.tsx App.tsx

# Or keep the current App.tsx
npm start
```

## Option 3: Run Without NativeWind

Remove NativeWind temporarily:

### Update App.tsx

Replace all `className="..."` with inline styles:

```tsx
// Instead of:
<View className="flex-1 bg-white">

// Use:
<View style={{ flex: 1, backgroundColor: 'white' }}>
```

### Update babel.config.js

```js
module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [],  // Remove nativewind/babel
  };
};
```

## Troubleshooting

### Error: "Use process(css).then(cb) to work with async plugins"

**Solution:** This is a PostCSS/NativeWind issue.

1. Make sure `postcss.config.js` exists (already created)
2. Try removing `node_modules` and reinstalling:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

### Error: "Cannot find module '@babel/runtime'"

**Solution:**
```bash
npm install @babel/runtime
```

### Web shows JSON instead of app

**Solution:**
1. Make sure `web/index.html` exists (already created)
2. Update `app.json` to specify web bundler:
   ```json
   "web": {
     "bundler": "metro"
   }
   ```
3. Restart with `npx expo start --clear`

### iOS Simulator crashes

**Solution:**
1. Use the simplified App.tsx first to confirm Expo works
2. Then gradually add features back
3. Check logs with: `npx react-native log-ios`

## Recommended Approach

**For quick testing:**
```bash
# Use simplified version
cp App.simple.tsx App.tsx
npm start
# Press 'i' for iOS simulator
```

**For full development:**
```bash
# Set up Supabase first (see LOCAL_DEVELOPMENT.md)
# Then use full App.tsx with proper .env configuration
```

## Current Status

✅ **Simplified App.tsx** - Ready to use, no configuration needed
⚠️ **Full App.tsx** - Requires:
  - Supabase project setup
  - `.env` file with credentials
  - NativeWind properly configured

## Next Steps After Getting It Working

1. **Confirm it works:**
   ```bash
   npm start
   # See the welcome screen on iOS/web
   ```

2. **Set up Supabase:**
   - Follow `LOCAL_DEVELOPMENT.md`
   - Create `.env` file
   - Run migration SQL

3. **Switch to full app:**
   ```bash
   mv App.tsx App.simple.tsx
   mv App.full.tsx App.tsx
   npm start
   ```

4. **Test authentication:**
   - Should see Sign In screen
   - Create test account
   - Complete garden wizard

## Still Having Issues?

1. Check Node version: `node --version` (should be 18+)
2. Check Expo version: `npx expo --version`
3. Try: `npx expo-doctor` to diagnose issues
4. Clear everything:
   ```bash
   rm -rf node_modules package-lock.json .expo
   npm install
   npx expo start --clear
   ```

Good luck! 🌱
