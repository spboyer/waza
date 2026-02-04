/** API client for waza backend */

import type { Task } from '../types';

const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `API error: ${response.status} ${response.statusText}`);
  }

  // Handle empty responses (like DELETE)
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text);
}

// Health
export async function getHealth(): Promise<{ status: string; version: string }> {
  return request('/health');
}

// Evals
export async function listEvals(): Promise<import('../types').Eval[]> {
  return request('/evals');
}

export async function getEval(id: string): Promise<import('../types').Eval> {
  return request(`/evals/${id}`);
}

export async function createEval(data: { name: string; content: string }): Promise<import('../types').Eval> {
  return request('/evals', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateEval(id: string, content: string): Promise<import('../types').Eval> {
  return request(`/evals/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function deleteEval(id: string): Promise<void> {
  await request(`/evals/${id}`, { method: 'DELETE' });
}

// Tasks
export async function listTasks(evalId: string): Promise<Task[]> {
  return request(`/evals/${evalId}/tasks`);
}

export async function getTask(evalId: string, taskId: string): Promise<Task> {
  return request(`/evals/${evalId}/tasks/${taskId}`);
}

export async function createTask(evalId: string, data: { name: string; content: string }): Promise<Task> {
  return request(`/evals/${evalId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateTask(evalId: string, taskId: string, content: string): Promise<Task> {
  return request(`/evals/${evalId}/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function duplicateTask(evalId: string, taskId: string): Promise<Task> {
  return request(`/evals/${evalId}/tasks/${taskId}/duplicate`, {
    method: 'POST',
  });
}

export async function deleteTask(evalId: string, taskId: string): Promise<void> {
  await request(`/evals/${evalId}/tasks/${taskId}`, { method: 'DELETE' });
}

// Skills / Generate
export interface GeneratePreview {
  skill_name: string;
  description: string;
  triggers: string[];
  triggers_count: number;
  eval_yaml_preview: string;
  tasks_count: number;
  tasks_preview: { name: string; content: string }[];
}

export interface GenerateResult {
  eval_id: string;
  skill_name: string;
  triggers_count: number;
  tasks_created: string[];
  message: string;
}

export async function generatePreview(skillUrl: string): Promise<GeneratePreview> {
  return request('/skills/generate-preview', {
    method: 'POST',
    body: JSON.stringify({ skill_url: skillUrl }),
  });
}

export async function generateEval(skillUrl: string, name?: string, assist?: boolean): Promise<GenerateResult> {
  return request('/skills/generate', {
    method: 'POST',
    body: JSON.stringify({ skill_url: skillUrl, name, assist }),
  });
}

// Runs
export async function listRuns(evalId?: string): Promise<import('../types').Run[]> {
  const params = evalId ? `?eval_id=${evalId}` : '';
  return request(`/runs${params}`);
}

export async function getRun(id: string): Promise<import('../types').Run> {
  return request(`/runs/${id}`);
}

export async function startRun(evalId: string, options?: { model?: string; executor?: string }): Promise<{ run_id: string; status: string }> {
  return request('/runs', {
    method: 'POST',
    body: JSON.stringify({ eval_id: evalId, ...options }),
  });
}

export async function stopRun(id: string): Promise<void> {
  await request(`/runs/${id}/stop`, { method: 'POST' });
}

// SSE stream for run progress
export function streamRun(runId: string, onProgress: (data: import('../types').RunProgress | import('../types').RunResults) => void): () => void {
  const eventSource = new EventSource(`${BASE_URL}/runs/${runId}/stream`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onProgress(data);
  };

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => eventSource.close();
}

// Config
export async function getConfig(): Promise<import('../types').Config> {
  return request('/config');
}

export async function updateConfig(data: Partial<import('../types').Config>): Promise<import('../types').Config> {
  return request('/config', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// Auth
export async function getUser(): Promise<import('../types').User | null> {
  try {
    return await request('/auth/user');
  } catch {
    return null;
  }
}
