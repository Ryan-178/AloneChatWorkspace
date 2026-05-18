import { create } from 'zustand';
import { sessionApi, modeApi } from '@/lib/api';
import { gatewayWs } from '@/lib/websocket';
import { generateId } from '@/lib/utils';
import type { AgentMessage, AgentSession, AgentMode } from '@/types';

interface AgentStore {
  mode: AgentMode;
  session: AgentSession | null;
  sessions: AgentSession[];
  messages: AgentMessage[];
  isThinking: boolean;
  currentTool: string | null;
  isLoading: boolean;
  error: string | null;

  fetchSessions: () => Promise<void>;
  createSession: (title?: string) => Promise<AgentSession>;
  selectSession: (session: AgentSession) => void;
  deleteSession: (sessionId: string) => Promise<void>;
  switchMode: (mode: AgentMode) => Promise<void>;
  sendMessage: (content: string) => void;
  addMessage: (message: Omit<AgentMessage, 'id' | 'created_at' | 'session_id'>) => void;
  clearMessages: () => void;
  connect: (token: string) => Promise<void>;
  disconnect: () => void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  mode: 'MTC',
  session: null,
  sessions: [],
  messages: [],
  isThinking: false,
  currentTool: null,
  isLoading: false,
  error: null,

  fetchSessions: async () => {
    set({ isLoading: true });
    try {
      const response = await sessionApi.list();
      set({ sessions: response.sessions, isLoading: false });
    } catch (error) {
      set({ isLoading: false, error: error instanceof Error ? error.message : 'Failed to fetch sessions' });
    }
  },

  createSession: async (title?: string) => {
    const { mode } = get();
    const session = await sessionApi.create({ title, mode });
    set((state) => ({
      sessions: [session, ...state.sessions],
      session,
      messages: [],
    }));
    return session;
  },

  selectSession: (session: AgentSession) => {
    set({ session, messages: [], mode: session.mode });
  },

  deleteSession: async (sessionId: string) => {
    await sessionApi.delete(sessionId);
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== sessionId),
      session: state.session?.id === sessionId ? null : state.session,
    }));
  },

  switchMode: async (mode: AgentMode) => {
    try {
      await modeApi.switch(mode);
      set({ mode });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to switch mode' });
    }
  },

  sendMessage: (content: string) => {
    const { session, mode } = get();
    if (!session) return;

    get().addMessage({
      role: 'user',
      type: 'text',
      content,
    });

    gatewayWs.send({
      type: 'message',
      session_id: session.id,
      mode,
      body: content,
    });

    set({ isThinking: true });
  },

  addMessage: (message) => {
    const { session } = get();
    const fullMessage: AgentMessage = {
      ...message,
      id: generateId(),
      session_id: session?.id || '',
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, fullMessage],
    }));

    if (message.type === 'final' || message.type === 'error') {
      set({ isThinking: false, currentTool: null });
    }
  },

  clearMessages: () => set({ messages: [] }),

  connect: async (token: string) => {
    const { session } = get();
    await gatewayWs.connect(token, session?.id);

    gatewayWs.onMessage('agent_thinking', (msg) => {
      get().addMessage({
        role: 'assistant',
        type: 'thinking',
        content: msg.content as string,
        metadata: msg.metadata,
      });
    });

    gatewayWs.onMessage('agent_acting', (msg) => {
      const metadata = msg.metadata;
      set({ currentTool: metadata?.tool_name as string || null });
      get().addMessage({
        role: 'assistant',
        type: 'acting',
        content: '',
        metadata,
      });
    });

    gatewayWs.onMessage('agent_observation', (msg) => {
      get().addMessage({
        role: 'assistant',
        type: 'observation',
        content: msg.content as string,
        metadata: msg.metadata,
      });
    });

    gatewayWs.onMessage('agent_final', (msg) => {
      get().addMessage({
        role: 'assistant',
        type: 'final',
        content: msg.content as string,
      });
    });

    gatewayWs.onMessage('agent_error', (msg) => {
      get().addMessage({
        role: 'assistant',
        type: 'error',
        content: msg.content as string,
      });
    });
  },

  disconnect: () => {
    gatewayWs.disconnect();
  },
}));
