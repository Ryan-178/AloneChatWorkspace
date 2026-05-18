export interface User {
  id: string;
  username: string;
  email: string;
  created_at: number;
  updated_at: number;
  metadata?: Record<string, unknown>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
