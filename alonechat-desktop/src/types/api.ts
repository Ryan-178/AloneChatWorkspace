export type GatewayMessageType =
  | 'connected'
  | 'disconnected'
  | 'task_progress'
  | 'agent_thinking'
  | 'agent_acting'
  | 'agent_observation'
  | 'agent_final'
  | 'agent_error'
  | 'artifact_update'
  | 'mode_switch'
  | 'skill_execution'
  | 'message'
  | 'error'
  | 'heartbeat'
  | 'subscribed'
  | 'unsubscribed'
  | 'pong';

export interface GatewayMessage {
  type: GatewayMessageType;
  content?: unknown;
  timestamp?: string;
  metadata?: Record<string, unknown>;
}

export interface WebSocketState {
  connected: boolean;
  connectionId: string | null;
  subscriptions: string[];
  lastHeartbeat: number | null;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
