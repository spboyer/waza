/** Types for waza API */

export interface Eval {
  id: string;
  name: string;
  skill: string;
  task_count: number;
  created_at: string;
  updated_at: string;
  path?: string;
  content?: Record<string, unknown>;
  raw?: string;
  last_run?: Run;
}

export interface Task {
  id: string;
  name: string;
  prompt?: string;
  graders?: string[];
  path?: string;
  content?: Record<string, unknown>;
  raw?: string;
}

export interface Run {
  id: string;
  eval_id?: string;
  eval_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  timestamp?: string;
  completed_at?: string;
  model?: string;
  executor?: string;
  pass_rate?: number;
  score?: number;
  duration_ms?: number;
  error?: string;
  results?: RunResults;
  progress?: RunProgress;
}

export interface RunResults {
  total_tasks: number;
  passed: number;
  failed: number;
  pass_rate: number;
  tasks: TaskResult[];
  suggestions?: string;
}

export interface TaskResult {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'error';
  score: number;
  trials: Trial[];
}

export interface Trial {
  trial_id: number;
  status: string;
  score: number;
  duration_ms: number;
  output?: string;
  error?: string;
  transcript?: TranscriptEntry[];
  grader_results?: Record<string, GraderResult>;
}

export interface TranscriptEntry {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  timestamp?: string;
}

export interface GraderResult {
  passed: boolean;
  score: number;
  message: string;
}

export interface RunProgress {
  current_task: number;
  total_tasks: number;
  current_trial: number;
  total_trials: number;
  message: string;
}

export interface Config {
  model: string;
  executor: string;
  theme: 'light' | 'dark';
}

export interface User {
  login: string;
  name: string;
  avatar_url: string;
}
