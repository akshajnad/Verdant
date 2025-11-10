/**
 * Schedule Screen - View and manage planting schedule
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { supabase } from '../../api/supabase';

interface Task {
  id: string;
  week_index: number;
  title: string;
  description?: string;
  due_date: string;
  status: 'pending' | 'in_progress' | 'done' | 'skipped';
}

interface ScheduleScreenProps {
  scheduleId: string;
  onProvideFeedback: (taskId?: string) => void;
}

export default function ScheduleScreen({
  scheduleId,
  onProvideFeedback,
}: ScheduleScreenProps) {
  const [loading, setLoading] = useState(true);
  const [schedule, setSchedule] = useState<any>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [view, setView] = useState<'list' | 'progress'>('list');

  useEffect(() => {
    loadSchedule();
  }, [scheduleId]);

  async function loadSchedule() {
    try {
      // Fetch schedule
      const { data: schedData, error: schedError } = await supabase
        .from('schedules')
        .select('*')
        .eq('id', scheduleId)
        .single();

      if (schedError) throw schedError;
      setSchedule(schedData);

      // Fetch tasks
      const { data: tasksData, error: tasksError } = await supabase
        .from('schedule_tasks')
        .select('*')
        .eq('schedule_id', scheduleId)
        .order('week_index');

      if (tasksError) throw tasksError;
      setTasks(tasksData || []);
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  }

  async function toggleTaskStatus(taskId: string, currentStatus: string) {
    const newStatus = currentStatus === 'done' ? 'pending' : 'done';

    try {
      const { error } = await supabase
        .from('schedule_tasks')
        .update({ status: newStatus })
        .eq('id', taskId);

      if (error) throw error;

      // Update local state
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      );
    } catch (error: any) {
      Alert.alert('Error', error.message);
    }
  }

  function getCurrentWeek(): number {
    if (!schedule) return 0;
    const startDate = new Date(schedule.start_date);
    const today = new Date();
    const diffTime = today.getTime() - startDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return Math.floor(diffDays / 7);
  }

  function getProgress(): { completed: number; total: number; percent: number } {
    const currentWeek = getCurrentWeek();
    const relevantTasks = tasks.filter((t) => t.week_index <= currentWeek);
    const completed = relevantTasks.filter((t) => t.status === 'done').length;
    const total = relevantTasks.length;
    const percent = total > 0 ? (completed / total) * 100 : 0;
    return { completed, total, percent };
  }

  if (loading) {
    return (
      <View className="flex-1 items-center justify-center bg-white">
        <ActivityIndicator size="large" color="#3aba6f" />
      </View>
    );
  }

  const progress = getProgress();
  const currentWeek = getCurrentWeek();

  function renderProgressView() {
    return (
      <View className="p-6">
        <Text className="text-2xl font-bold text-gray-900 mb-2">
          Progress
        </Text>
        <Text className="text-gray-600 mb-6">
          Week {currentWeek} of your schedule
        </Text>

        {/* Progress Bar */}
        <View className="bg-gray-200 rounded-full h-8 mb-4 overflow-hidden">
          <View
            className="bg-verdant h-full items-center justify-center"
            style={{ width: `${progress.percent}%` }}
          >
            <Text className="text-white font-bold text-xs">
              {Math.round(progress.percent)}%
            </Text>
          </View>
        </View>

        <View className="flex-row justify-between mb-6">
          <Text className="text-gray-600">
            {progress.completed} of {progress.total} tasks completed
          </Text>
        </View>

        {/* Weekly Breakdown */}
        <Text className="text-lg font-bold text-gray-900 mb-4">
          By Week
        </Text>
        {Array.from({ length: Math.max(...tasks.map((t) => t.week_index)) + 1 }).map((_, weekIdx) => {
          const weekTasks = tasks.filter((t) => t.week_index === weekIdx);
          const weekDone = weekTasks.filter((t) => t.status === 'done').length;
          const weekTotal = weekTasks.length;

          return (
            <View
              key={weekIdx}
              className="flex-row items-center justify-between mb-3 p-3 bg-gray-50 rounded-lg"
            >
              <Text className="font-semibold text-gray-900">
                Week {weekIdx}
              </Text>
              <Text className="text-gray-600">
                {weekDone}/{weekTotal} done
              </Text>
            </View>
          );
        })}

        {/* Feedback Button */}
        <Pressable
          className="bg-verdant rounded-xl py-4 mt-6"
          onPress={() => onProvideFeedback()}
        >
          <Text className="text-white text-center font-semibold text-base">
            Provide Feedback
          </Text>
        </Pressable>
      </View>
    );
  }

  function renderListView() {
    // Group tasks by week
    const tasksByWeek: { [key: number]: Task[] } = {};
    tasks.forEach((task) => {
      if (!tasksByWeek[task.week_index]) {
        tasksByWeek[task.week_index] = [];
      }
      tasksByWeek[task.week_index].push(task);
    });

    return (
      <ScrollView className="flex-1 px-6 py-4">
        {Object.entries(tasksByWeek).map(([weekStr, weekTasks]) => {
          const week = parseInt(weekStr);
          const isCurrentWeek = week === currentWeek;

          return (
            <View key={week} className="mb-6">
              <View className="flex-row items-center mb-3">
                <Text className={`text-lg font-bold ${isCurrentWeek ? 'text-verdant' : 'text-gray-900'}`}>
                  Week {week}
                </Text>
                {isCurrentWeek && (
                  <View className="ml-2 bg-verdant px-2 py-1 rounded-full">
                    <Text className="text-white text-xs font-bold">Current</Text>
                  </View>
                )}
              </View>

              {weekTasks.map((task) => (
                <View
                  key={task.id}
                  className="bg-white border border-gray-200 rounded-xl p-4 mb-3"
                >
                  <View className="flex-row items-start justify-between mb-2">
                    <View className="flex-1 mr-2">
                      <Text className="text-base font-semibold text-gray-900">
                        {task.title}
                      </Text>
                      {task.description && (
                        <Text className="text-sm text-gray-600 mt-1">
                          {task.description}
                        </Text>
                      )}
                      <Text className="text-xs text-gray-500 mt-2">
                        Due: {new Date(task.due_date).toLocaleDateString()}
                      </Text>
                    </View>

                    {/* Status Toggle */}
                    <Pressable
                      className={`w-8 h-8 rounded-full items-center justify-center ${
                        task.status === 'done' ? 'bg-verdant' : 'bg-gray-200'
                      }`}
                      onPress={() => toggleTaskStatus(task.id, task.status)}
                    >
                      {task.status === 'done' && (
                        <Text className="text-white font-bold">✓</Text>
                      )}
                    </Pressable>
                  </View>

                  <Pressable
                    className="mt-2"
                    onPress={() => onProvideFeedback(task.id)}
                  >
                    <Text className="text-verdant text-sm font-medium">
                      Add feedback →
                    </Text>
                  </Pressable>
                </View>
              ))}
            </View>
          );
        })}
      </ScrollView>
    );
  }

  return (
    <View className="flex-1 bg-white">
      {/* Header */}
      <View className="px-6 pt-6 pb-4 border-b border-gray-200">
        <Text className="text-2xl font-bold text-gray-900 mb-1">
          {schedule?.name || 'Schedule'}
        </Text>
        <Text className="text-gray-600">
          Started {new Date(schedule?.start_date).toLocaleDateString()}
        </Text>
      </View>

      {/* View Toggle */}
      <View className="flex-row px-6 py-3 border-b border-gray-200">
        <Pressable
          className={`flex-1 py-2 mr-2 rounded-lg ${
            view === 'list' ? 'bg-verdant' : 'bg-gray-100'
          }`}
          onPress={() => setView('list')}
        >
          <Text
            className={`text-center font-semibold ${
              view === 'list' ? 'text-white' : 'text-gray-700'
            }`}
          >
            Tasks
          </Text>
        </Pressable>
        <Pressable
          className={`flex-1 py-2 ml-2 rounded-lg ${
            view === 'progress' ? 'bg-verdant' : 'bg-gray-100'
          }`}
          onPress={() => setView('progress')}
        >
          <Text
            className={`text-center font-semibold ${
              view === 'progress' ? 'text-white' : 'text-gray-700'
            }`}
          >
            Progress
          </Text>
        </Pressable>
      </View>

      {/* Content */}
      {view === 'list' ? renderListView() : renderProgressView()}
    </View>
  );
}
