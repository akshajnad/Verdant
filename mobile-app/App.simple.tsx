/**
 * Verdant v2 - Main Application Entry Point (Simplified without NativeWind)
 */
import React, { useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';

const queryClient = new QueryClient();

function AppContent() {
  return (
    <View style={styles.container}>
      <Text style={styles.emoji}>🌱</Text>
      <Text style={styles.title}>Welcome to Verdant v2</Text>
      <Text style={styles.subtitle}>AI-Powered Garden Planning</Text>
      <ActivityIndicator size="large" color="#3aba6f" style={styles.loader} />
      <Text style={styles.info}>
        Setting up your garden experience...
      </Text>
      <Text style={styles.note}>
        Note: Full authentication and features require Supabase configuration.
        See LOCAL_DEVELOPMENT.md for setup instructions.
      </Text>
    </View>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <StatusBar style="auto" />
    </QueryClientProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1b1b1b',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 32,
    textAlign: 'center',
  },
  loader: {
    marginVertical: 24,
  },
  info: {
    fontSize: 14,
    color: '#888888',
    textAlign: 'center',
    marginBottom: 16,
  },
  note: {
    fontSize: 12,
    color: '#aaaaaa',
    textAlign: 'center',
    maxWidth: 400,
    lineHeight: 18,
  },
});
