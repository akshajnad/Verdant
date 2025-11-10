/**
 * Feedback Sheet - Submit feedback to AI for schedule revision
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { reviseSchedule } from '../../api/ai-service';

interface FeedbackSheetProps {
  scheduleId: string;
  taskId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

const MOODS = [
  { value: 'excited', emoji: '😊', label: 'Excited' },
  { value: 'satisfied', emoji: '🙂', label: 'Satisfied' },
  { value: 'neutral', emoji: '😐', label: 'Neutral' },
  { value: 'concerned', emoji: '😟', label: 'Concerned' },
  { value: 'frustrated', emoji: '😤', label: 'Frustrated' },
];

export default function FeedbackSheet({
  scheduleId,
  taskId,
  onClose,
  onSuccess,
}: FeedbackSheetProps) {
  const [text, setText] = useState('');
  const [mood, setMood] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!text.trim()) {
      Alert.alert('Error', 'Please enter your feedback');
      return;
    }

    setLoading(true);
    try {
      const response = await reviseSchedule({
        schedule_id: scheduleId,
        task_id: taskId,
        text: text.trim(),
        mood: mood || undefined,
      });

      Alert.alert(
        'Feedback Received',
        response.message || 'Your schedule has been updated based on your feedback!',
        [{ text: 'OK', onPress: onSuccess }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message);
      setLoading(false);
    }
  }

  return (
    <View className="flex-1 bg-white">
      <ScrollView className="flex-1 px-6 py-6">
        {/* Header */}
        <View className="mb-6">
          <Text className="text-2xl font-bold text-gray-900 mb-2">
            Provide Feedback
          </Text>
          <Text className="text-gray-600">
            Share your experience and we'll adapt your schedule accordingly
          </Text>
        </View>

        {/* Mood Selection */}
        <View className="mb-6">
          <Text className="text-sm font-medium text-gray-700 mb-3">
            How are things going?
          </Text>
          <View className="flex-row justify-between">
            {MOODS.map((m) => (
              <Pressable
                key={m.value}
                className={`items-center p-3 rounded-xl border-2 ${
                  mood === m.value ? 'border-verdant bg-verdant-50' : 'border-gray-200'
                }`}
                onPress={() => setMood(m.value)}
              >
                <Text className="text-2xl mb-1">{m.emoji}</Text>
                <Text className="text-xs text-gray-600">{m.label}</Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Feedback Text */}
        <View className="mb-6">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Tell us more
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl p-4 min-h-[120px]"
            value={text}
            onChangeText={setText}
            placeholder="e.g., It's been raining heavily, my plants are waterlogged..."
            multiline
            textAlignVertical="top"
            editable={!loading}
          />
          <Text className="text-xs text-gray-500 mt-2">
            Be specific about challenges, observations, or questions
          </Text>
        </View>

        {/* Examples */}
        <View className="bg-gray-50 rounded-xl p-4 mb-6">
          <Text className="text-sm font-semibold text-gray-900 mb-2">
            Example feedback:
          </Text>
          <Text className="text-xs text-gray-600 mb-1">
            • "Heavy rain this week, should I delay planting?"
          </Text>
          <Text className="text-xs text-gray-600 mb-1">
            • "Tomatoes are growing faster than expected"
          </Text>
          <Text className="text-xs text-gray-600">
            • "Too busy, need simpler maintenance tasks"
          </Text>
        </View>
      </ScrollView>

      {/* Action Buttons */}
      <View className="px-6 py-4 border-t border-gray-200">
        <View className="flex-row">
          <Pressable
            className="flex-1 border border-gray-300 rounded-xl py-4 mr-2"
            onPress={onClose}
            disabled={loading}
          >
            <Text className="text-gray-700 text-center font-semibold">
              Cancel
            </Text>
          </Pressable>
          <Pressable
            className={`flex-1 bg-verdant rounded-xl py-4 ml-2 ${
              loading ? 'opacity-50' : ''
            }`}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text className="text-white text-center font-semibold">
                Submit Feedback
              </Text>
            )}
          </Pressable>
        </View>
      </View>
    </View>
  );
}
