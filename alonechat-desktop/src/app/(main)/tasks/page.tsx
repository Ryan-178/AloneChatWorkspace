"use client";

import { useTaskStore } from "@/stores/task-store";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import type { Task, TaskStatus } from "@/types";

const statusConfig: Record<
  TaskStatus,
  { icon: typeof Clock; color: string; label: string }
> = {
  pending: { icon: Clock, color: "text-muted-foreground", label: "等待中" },
  running: { icon: Loader2, color: "text-primary", label: "运行中" },
  completed: { icon: CheckCircle, color: "text-green-500", label: "已完成" },
  failed: { icon: XCircle, color: "text-destructive", label: "失败" },
  cancelled: { icon: XCircle, color: "text-muted-foreground", label: "已取消" },
};

function TaskCard({ task }: { task: Task }) {
  const config = statusConfig[task.status];
  const StatusIcon = config.icon;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{task.description}</CardTitle>
          <Badge variant={task.status === "running" ? "default" : "secondary"}>
            <StatusIcon
              className={`h-3 w-3 mr-1 ${task.status === "running" && "animate-spin"}`}
            />
            {config.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-xs text-muted-foreground">
          <p>
            进度: {task.progress}%
            {task.progress > 0 && task.progress < 100 && (
              <span className="ml-2 inline-block h-1.5 w-24 bg-muted rounded overflow-hidden">
                <span
                  className="block h-full bg-primary"
                  style={{ width: `${task.progress}%` }}
                />
              </span>
            )}
          </p>
          <p>
            创建: {new Date(task.created_at).toLocaleString("zh-CN")}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function TasksPage() {
  const { tasks, isLoading, fetchTasks, createTask, cancelTask } = useTaskStore();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleCreateTask = async () => {
    await createTask("新任务示例 / Example new task");
  };

  return (
    <div className="p-6 h-full overflow-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">任务管理 / Tasks</h1>
          <p className="text-muted-foreground text-sm">
            管理和监控后台任务 / Manage and monitor background tasks
          </p>
        </div>
        <Button onClick={handleCreateTask} className="gap-2">
          <Plus className="h-4 w-4" />
          新建任务 / New Task
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg mb-2">暂无任务 / No tasks</p>
          <p className="text-sm">点击上方按钮创建新任务</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
