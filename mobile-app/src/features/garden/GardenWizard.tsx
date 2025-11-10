/**
 * Garden Setup Wizard
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as Location from 'expo-location';
import { supabase } from '../../api/supabase';

interface GardenWizardProps {
  userId: string;
  onComplete: (gardenId: string) => void;
}

export default function GardenWizard({ userId, onComplete }: GardenWizardProps) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Garden data
  const [name, setName] = useState('My Garden');
  const [rows, setRows] = useState('4');
  const [cols, setCols] = useState('8');
  const [area, setArea] = useState('');
  const [location, setLocation] = useState<{ lat: number; lon: number; accuracy: number } | null>(null);

  // Goals
  const [numPeople, setNumPeople] = useState('');
  const [volumeGoal, setVolumeGoal] = useState('');
  const [calorieGoal, setCalorieGoal] = useState('');
  const [additionalNeeds, setAdditionalNeeds] = useState('');
  const [urgency, setUrgency] = useState('3');

  async function requestLocation() {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location access is required for weather forecasts');
        setLoading(false);
        return;
      }

      const loc = await Location.getCurrentPositionAsync({});
      setLocation({
        lat: loc.coords.latitude,
        lon: loc.coords.longitude,
        accuracy: loc.coords.accuracy || 0,
      });
      Alert.alert('Success', 'Location captured!');
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    setLoading(true);
    try {
      // 1. Create garden
      const { data: garden, error: gardenError } = await supabase
        .from('gardens')
        .insert({
          owner_id: userId,
          name,
          rows: parseInt(rows) || 4,
          cols: parseInt(cols) || 8,
          area_m2: parseFloat(area) || null,
          location_lat: location?.lat,
          location_lon: location?.lon,
          location_accuracy_m: location?.accuracy,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        })
        .select()
        .single();

      if (gardenError) throw gardenError;

      // 2. Create produce request (goals)
      if (numPeople || volumeGoal || calorieGoal) {
        const { error: requestError } = await supabase
          .from('produce_requests')
          .insert({
            owner_id: userId,
            num_people: parseInt(numPeople) || 0,
            volume_goal: parseFloat(volumeGoal) || 0,
            calorie_goal: parseFloat(calorieGoal) || 0,
            additional_needs: additionalNeeds,
            urgency: parseInt(urgency) || 3,
          });

        if (requestError) throw requestError;
      }

      // 3. Complete wizard
      Alert.alert('Success', 'Garden created!');
      onComplete(garden.id);
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  }

  function renderStep1() {
    return (
      <View>
        <Text className="text-2xl font-bold text-gray-900 mb-2">
          Garden Details
        </Text>
        <Text className="text-gray-600 mb-6">
          Tell us about your garden space
        </Text>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Garden Name
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={name}
            onChangeText={setName}
            placeholder="My Garden"
          />
        </View>

        <View className="flex-row mb-4">
          <View className="flex-1 mr-2">
            <Text className="text-sm font-medium text-gray-700 mb-2">Rows</Text>
            <TextInput
              className="border border-gray-300 rounded-xl px-4 py-3"
              value={rows}
              onChangeText={setRows}
              keyboardType="number-pad"
              placeholder="4"
            />
          </View>
          <View className="flex-1 ml-2">
            <Text className="text-sm font-medium text-gray-700 mb-2">Columns</Text>
            <TextInput
              className="border border-gray-300 rounded-xl px-4 py-3"
              value={cols}
              onChangeText={setCols}
              keyboardType="number-pad"
              placeholder="8"
            />
          </View>
        </View>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Total Area (m²) - Optional
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={area}
            onChangeText={setArea}
            keyboardType="decimal-pad"
            placeholder="e.g., 20"
          />
        </View>

        <View className="bg-verdant-50 border border-verdant-200 rounded-xl p-4 mb-6">
          <Text className="text-sm font-medium text-verdant-900 mb-2">
            Location for Weather
          </Text>
          <Text className="text-sm text-verdant-700 mb-3">
            {location
              ? `📍 Location captured (±${Math.round(location.accuracy)}m)`
              : 'Location not set'}
          </Text>
          <Pressable
            className="bg-verdant rounded-lg py-2"
            onPress={requestLocation}
            disabled={loading}
          >
            <Text className="text-white text-center font-semibold">
              {location ? 'Update Location' : 'Enable Location'}
            </Text>
          </Pressable>
        </View>

        <Pressable
          className="bg-verdant rounded-xl py-4"
          onPress={() => setStep(2)}
        >
          <Text className="text-white text-center text-base font-semibold">
            Next: Goals
          </Text>
        </Pressable>
      </View>
    );
  }

  function renderStep2() {
    return (
      <View>
        <Text className="text-2xl font-bold text-gray-900 mb-2">
          Your Goals
        </Text>
        <Text className="text-gray-600 mb-6">
          Help us understand what you want to grow
        </Text>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Number of People to Feed
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={numPeople}
            onChangeText={setNumPeople}
            keyboardType="number-pad"
            placeholder="e.g., 4"
          />
        </View>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Volume Goal (kg/week) - Optional
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={volumeGoal}
            onChangeText={setVolumeGoal}
            keyboardType="decimal-pad"
            placeholder="e.g., 10"
          />
        </View>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Calorie Goal (kcal/week) - Optional
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={calorieGoal}
            onChangeText={setCalorieGoal}
            keyboardType="number-pad"
            placeholder="e.g., 5000"
          />
        </View>

        <View className="mb-4">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Additional Needs
          </Text>
          <TextInput
            className="border border-gray-300 rounded-xl px-4 py-3"
            value={additionalNeeds}
            onChangeText={setAdditionalNeeds}
            placeholder="e.g., leafy greens, root vegetables"
            multiline
            numberOfLines={3}
          />
        </View>

        <View className="mb-6">
          <Text className="text-sm font-medium text-gray-700 mb-2">
            Urgency (1-5): {urgency}
          </Text>
          <View className="flex-row justify-between">
            {[1, 2, 3, 4, 5].map((val) => (
              <Pressable
                key={val}
                className={`w-12 h-12 rounded-full items-center justify-center ${
                  urgency === String(val) ? 'bg-verdant' : 'bg-gray-200'
                }`}
                onPress={() => setUrgency(String(val))}
              >
                <Text
                  className={`font-bold ${
                    urgency === String(val) ? 'text-white' : 'text-gray-700'
                  }`}
                >
                  {val}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        <View className="flex-row">
          <Pressable
            className="flex-1 border border-gray-300 rounded-xl py-4 mr-2"
            onPress={() => setStep(1)}
          >
            <Text className="text-gray-700 text-center font-semibold">
              Back
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
                Create Garden
              </Text>
            )}
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <ScrollView className="flex-1 bg-white px-6 py-8">
      {step === 1 ? renderStep1() : renderStep2()}
    </ScrollView>
  );
}
