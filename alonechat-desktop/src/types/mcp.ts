export type MCPServerStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface MCPServer {
  id: string;
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  status: MCPServerStatus;
  description?: string;
  created_at: number;
  last_connected?: number;
  error?: string;
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  server_id: string;
  server_name: string;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
  server_id: string;
}

export interface MCPToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  error?: string;
  duration_ms?: number;
}
