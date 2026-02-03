/** API client for waza backend */

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
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
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

export async function createEval(data: { name: string; skill: string; yaml_content: string }): Promise<import('../types').Eval> {
  return request('/evals', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteEval(id: string): Promise<void> {
  await request(`/evals/${id}`, { method: 'DELETE' });
}

// Runs
export async function listRuns(evalId?: string): Promise<import('../types').Run[]> {
  const params = evalId ? `?eval_id=${evalId}` : '';
  return request(`/runs${params}`);
}

export async function getRun(id: string): Promise<import('../types').Run> {
  return request(`/runs/${id}`);
}

export async function startRun(evalId: string, options?: { model?: string; executor?: string }): Promise<import('../types').Run> {
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
