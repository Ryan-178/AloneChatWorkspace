import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { tauriApi } from '@/lib/tauri';
import type { Workspace } from '@/types';

interface WorkspaceStore {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isLoading: boolean;
  error: string | null;

  addWorkspace: (path: string) => Promise<void>;
  removeWorkspace: (path: string) => void;
  setCurrentWorkspace: (workspace: Workspace | null) => void;
  refreshFiles: () => Promise<void>;
  toggleExpand: (path: string) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>()(
  persist(
    (set, get) => ({
      workspaces: [],
      currentWorkspace: null,
      isLoading: false,
      error: null,

      addWorkspace: async (path: string) => {
        set({ isLoading: true });
        try {
          const files = await tauriApi.file.listDirectory(path);
          const name = path.split(/[/\\]/).pop() || path;
          const workspace: Workspace = {
            path,
            name,
            files,
            isExpanded: true,
          };
          set((state) => ({
            workspaces: [...state.workspaces, workspace],
            isLoading: false,
          }));
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to add workspace',
          });
        }
      },

      removeWorkspace: (path: string) => {
        set((state) => ({
          workspaces: state.workspaces.filter((w) => w.path !== path),
          currentWorkspace: state.currentWorkspace?.path === path ? null : state.currentWorkspace,
        }));
      },

      setCurrentWorkspace: (workspace: Workspace | null) => {
        set({ currentWorkspace: workspace });
      },

      refreshFiles: async () => {
        const { currentWorkspace } = get();
        if (!currentWorkspace) return;

        try {
          const files = await tauriApi.file.listDirectory(currentWorkspace.path);
          const updated = { ...currentWorkspace, files };
          set((state) => ({
            currentWorkspace: updated,
            workspaces: state.workspaces.map((w) =>
              w.path === currentWorkspace.path ? updated : w
            ),
          }));
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to refresh files' });
        }
      },

      toggleExpand: (path: string) => {
        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.path === path ? { ...w, isExpanded: !w.isExpanded } : w
          ),
        }));
      },
    }),
    {
      name: 'alonechat-workspaces',
      partialize: (state) => ({
        workspaces: state.workspaces.map((w) => ({ ...w, files: [] })),
      }),
    }
  )
);
