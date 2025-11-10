/**
 * Client for Verdant AI service
 */
import { supabase } from './supabase';

const AI_SERVICE_URL = process.env.EXPO_PUBLIC_AI_SERVICE_URL || 'http://localhost:8000';

export interface GenerateScheduleParams {
  user_id: string;
  garden_id: string;
  schedule_name: string;
  start_date: string; // ISO date string
}

export interface ScheduleTask {
  week_index: number;
  title: string;
  description?: string;
  plant_catalog_id?: string;
  due_date?: string;
}

export interface GenerateScheduleResponse {
  schedule_id: string;
  diagram?: string;
  tasks: ScheduleTask[];
}

export interface ReviseFeedbackParams {
  schedule_id: string;
  task_id?: string;
  text: string;
  mood?: string;
  photos?: string[];
}

export interface ReviseScheduleResponse {
  ok: boolean;
  message: string;
  updated_tasks: string[];
}

/**
 * Generate a new planting schedule
 */
export async function generateSchedule(
  params: GenerateScheduleParams
): Promise<GenerateScheduleResponse> {
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch(`${AI_SERVICE_URL}/ai/generate_schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token || ''}`,
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate schedule');
  }

  return response.json();
}

/**
 * Submit feedback and revise schedule
 */
export async function reviseSchedule(
  params: ReviseFeedbackParams
): Promise<ReviseScheduleResponse> {
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch(`${AI_SERVICE_URL}/ai/revise_schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token || ''}`,
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to revise schedule');
  }

  return response.json();
}
