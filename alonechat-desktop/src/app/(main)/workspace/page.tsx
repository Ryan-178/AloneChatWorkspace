"use client";

import { useWorkspaceStore } from "@/stores/workspace-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Plus, RefreshCw, Folder, File } from "lucide-react";
import { cn } from "@/lib/utils";

export default function WorkspacePage() {
  const {
    workspaces,
    currentWorkspace,
    addWorkspace,
    removeWorkspace,
    setCurrentWorkspace,
    refreshFiles,
    toggleExpand,
  } = useWorkspaceStore();

  const handleAddWorkspace = async () => {
    const path = prompt("输入工作区路径 / Enter workspace path:");
    if (path) {
      await addWorkspace(path);
    }
  };

  return (
    <div className="p-6 h-full overflow-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">工作区 / Workspace</h1>
          <p className="text-muted-foreground text-sm">
            管理项目文件和目录 / Manage project files and directories
          </p>
        </div>
        <Button onClick={handleAddWorkspace} className="gap-2">
          <Plus className="h-4 w-4" />
          添加工作区 / Add Workspace
        </Button>
      </div>

      {workspaces.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <FolderOpen className="h-16 w-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-2">暂无工作区 / No workspaces</p>
          <p className="text-sm mb-4">添加一个工作区开始管理文件</p>
          <Button onClick={handleAddWorkspace} variant="outline">
            添加工作区 / Add Workspace
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {workspaces.map((workspace) => (
            <Card
              key={workspace.path}
              className={cn(
                "cursor-pointer transition-colors",
                currentWorkspace?.path === workspace.path &&
                  "border-primary bg-primary/5"
              )}
              onClick={() => setCurrentWorkspace(workspace)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <FolderOpen className="h-4 w-4" />
                    {workspace.name}
                  </CardTitle>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={(e) => {
                        e.stopPropagation();
                        refreshFiles();
                      }}
                    >
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeWorkspace(workspace.path);
                      }}
                    >
                      <Plus className="h-3 w-3 rotate-45" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground mb-2 truncate">
                  {workspace.path}
                </p>
                <div className="text-xs text-muted-foreground">
                  {workspace.files.length} 项目 / items
                </div>
                {workspace.files.length > 0 && (
                  <div className="mt-2 space-y-1 max-h-32 overflow-auto">
                    {workspace.files.slice(0, 10).map((file) => (
                      <div
                        key={file}
                        className="flex items-center gap-1 text-xs text-muted-foreground"
                      >
                        <File className="h-3 w-3" />
                        {file}
                      </div>
                    ))}
                    {workspace.files.length > 10 && (
                      <p className="text-xs text-muted-foreground">
                        +{workspace.files.length - 10} 更多...
                      </p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
