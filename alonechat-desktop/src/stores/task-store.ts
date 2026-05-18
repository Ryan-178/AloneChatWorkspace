import { create } from 'zustand';
import { taskApi } from '@/lib/api';
import { gatewayWs } from '@/lib/websocket';
import type { Task, TaskStatus, TaskPriority, TaskProgress } from '@/types';

interface TaskStore {
  tasks: Task[];
  currentTask: Task | null;
  isLoading: boolean;
  error: string | null;

  fetchTasks: (status?: TaskStatus) => Promise<void>;
  createTask: (description: string, priority?: TaskPriority) => Promise<Task>;
  cancelTask: (taskId: string) => Promise<void>;
  setCurrentTask: (task: Task | null) => void;
  updateTaskProgress: (progress: TaskProgress) => void;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,

  fetchTasks: async (status?: TaskStatus) => {
    set({ isLoading: true });
    try {
      const response = await taskApi.list(status);
      set({ tasks: response.tasks, isLoading: false });
    } catch (error) {
      set({ isLoading: false, error: error instanceof Error ? error.message : 'Failed to fetch tasks' });
    }
  },

  createTask: async (description: string, priority: TaskPriority = 'medium') => {
    const task = await taskApi.create({ description, priority });
    set((state) => ({
      tasks: [task, ...state.tasks],
      currentTask: task,
    }));

    gatewayWs.subscribe(`task:${task.id}`);

    return task;
  },

  cancelTask: async (taskId: string) => {
    await taskApi.cancel(taskId);
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
      currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
    }));
  },

  setCurrentTask: (task: Task | null) => {
    set({ currentTask: task });
    if (task) {
      gatewayWs.subscribe(`task:${task.id}`);
    }
  },

  updateTaskProgress: (progress: TaskProgress) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === progress.task_id
          ? { ...t, status: progress.status, progress: progress.progress }
          : t
      ),
      currentTask:
        state.currentTask?.id === progress.task_id
          ? { ...state.currentTask, status: progress.status, progress: progress.progress }
          : state.currentTask,
    }));
  },
}));

gatewayWs.onMessage('task_progress', (msg) => {
  const progress = msg.content as TaskProgress;
  useTaskStore.getState().updateTaskProgress(progress);
});
