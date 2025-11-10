/**
 * Verdant v2 - Main Application Entry Point
 */
import React, { useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSession } from './src/hooks/useSession';
import SignInScreen from './src/features/auth/SignInScreen';
import GardenWizard from './src/features/garden/GardenWizard';
import ScheduleScreen from './src/features/schedule/ScheduleScreen';
import FeedbackSheet from './src/features/schedule/FeedbackSheet';

const queryClient = new QueryClient();

function AppContent() {
  const { session, loading: sessionLoading, user } = useSession();
  const [currentGarden, setCurrentGarden] = useState<string | null>(null);
  const [currentSchedule, setCurrentSchedule] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackTaskId, setFeedbackTaskId] = useState<string | undefined>();

  // Loading state
  if (sessionLoading) {
    return (
      <View className="flex-1 items-center justify-center bg-white">
        <ActivityIndicator size="large" color="#3aba6f" />
      </View>
    );
  }

  // Not authenticated
  if (!session || !user) {
    return <SignInScreen />;
  }

  // Show feedback sheet
  if (showFeedback && currentSchedule) {
    return (
      <FeedbackSheet
        scheduleId={currentSchedule}
        taskId={feedbackTaskId}
        onClose={() => {
          setShowFeedback(false);
          setFeedbackTaskId(undefined);
        }}
        onSuccess={() => {
          setShowFeedback(false);
          setFeedbackTaskId(undefined);
          // Schedule screen will reload automatically
        }}
      />
    );
  }

  // Show schedule if exists
  if (currentSchedule) {
    return (
      <ScheduleScreen
        scheduleId={currentSchedule}
        onProvideFeedback={(taskId) => {
          setFeedbackTaskId(taskId);
          setShowFeedback(true);
        }}
      />
    );
  }

  // Show garden wizard if no garden
  if (!currentGarden) {
    return (
      <GardenWizard
        userId={user.id}
        onComplete={(gardenId) => {
          setCurrentGarden(gardenId);
          // In a full app, you'd navigate to schedule generation
          // For now, this demonstrates the flow
        }}
      />
    );
  }

  // Default: show a placeholder (in full app, this would be the home/navigation screen)
  return (
    <View className="flex-1 items-center justify-center bg-white px-6">
      <View className="text-center">
        <View className="text-4xl mb-4">🌱</View>
        <View className="text-2xl font-bold text-gray-900 mb-2">
          Garden Created!
        </View>
        <View className="text-gray-600">
          Next: Generate your first schedule
        </View>
      </View>
    </View>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
