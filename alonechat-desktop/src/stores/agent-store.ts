import { create } from 'zustand';
import { sessionApi, modeApi } from '@/lib/api';
import { gatewayWs } from '@/lib/websocket';
import { generateId } from '@/lib/utils';
import type { AgentMessage, AgentSession, AgentMode, InteractionMode, InteractionModeConfig } from '@/types';

interface AgentStore {
  mode: AgentMode;
  interactionMode: InteractionMode;
  interactionModeConfig: InteractionModeConfig | null;
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
  switchInteractionMode: (mode: InteractionMode) => Promise<void>;
  cycleInteractionMode: () => void;
  sendMessage: (content: string) => void;
  addMessage: (message: Omit<AgentMessage, 'id' | 'created_at' | 'session_id'>) => void;
  clearMessages: () => void;
  connect: (token: string) => Promise<void>;
  disconnect: () => void;
}

const defaultInteractionModeConfig: InteractionModeConfig = {
  mode: 'agent',
  auto_approve_tools: false,
  require_confirmation: ['shell', 'file_write', 'file_delete'],
  allowed_tools: [],
  description: '默认交互模式，工具执行需审批 / Default interaction mode, tool execution requires approval',
  icon: '🤖',
  color: 'green',
};

export const useAgentStore = create<AgentStore>((set, get) => ({
  mode: 'MTC',
  interactionMode: 'agent',
  interactionModeConfig: defaultInteractionModeConfig,
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
    const { mode, interactionMode } = get();
    const session = await sessionApi.create({ title, mode, interaction_mode: interactionMode });
    set((state) => ({
      sessions: [session, ...state.sessions],
      session,
      messages: [],
    }));
    return session;
  },

  selectSession: (session: AgentSession) => {
    set({ 
      session, 
      messages: [], 
      mode: session.mode,
      interactionMode: session.interaction_mode || 'agent',
    });
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

  switchInteractionMode: async (mode: InteractionMode) => {
    const modeConfigs: Record<InteractionMode, InteractionModeConfig> = {
      plan: {
        mode: 'plan',
        auto_approve_tools: false,
        require_confirmation: [],
        allowed_tools: ['read', 'search', 'list', 'file_read', 'file_search'],
        description: '只读探索模式，无工具执行 / Read-only exploration mode, no tool execution',
        icon: '🔍',
        color: 'blue',
      },
      agent: {
        mode: 'agent',
        auto_approve_tools: false,
        require_confirmation: ['shell', 'file_write', 'file_delete', 'file_edit'],
        allowed_tools: [],
        description: '默认交互模式，工具执行需审批 / Default interaction mode, tool execution requires approval',
        icon: '🤖',
        color: 'green',
      },
      yolo: {
        mode: 'yolo',
        auto_approve_tools: true,
        require_confirmation: [],
        allowed_tools: [],
        description: '自动批准模式，信任工作区 / Auto-approve mode, trust workspace',
        icon: '🚀',
        color: 'yellow',
      },
    };

    try {
      set({ 
        interactionMode: mode,
        interactionModeConfig: modeConfigs[mode],
      });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to switch interaction mode' });
    }
  },

  cycleInteractionMode: () => {
    const { interactionMode, switchInteractionMode } = get();
    const modeOrder: InteractionMode[] = ['plan', 'agent', 'yolo'];
    const currentIndex = modeOrder.indexOf(interactionMode);
    const nextIndex = (currentIndex + 1) % modeOrder.length;
    switchInteractionMode(modeOrder[nextIndex]);
  },

  sendMessage: (content: string) => {
    const { session, mode, interactionMode } = get();
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
      interaction_mode: interactionMode,
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
