"use client"

import { useEffect, useState } from "react";
import { Command } from "cmdk";
import { useUIStore } from "@/stores/ui-store";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  Wrench,
  FolderOpen,
  Settings,
  Zap,
  LayoutDashboard,
} from "lucide-react";

const commands = [
  { id: "home", icon: LayoutDashboard, label: "主页 / Home", href: "/" },
  { id: "agent", icon: MessageSquare, label: "Agent 对话", href: "/agent" },
  { id: "tasks", icon: Zap, label: "任务管理", href: "/tasks" },
  { id: "skills", icon: Wrench, label: "Skills 市场", href: "/skills" },
  { id: "workspace", icon: FolderOpen, label: "工作区", href: "/workspace" },
  { id: "settings", icon: Settings, label: "设置", href: "/settings" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  if (!mounted) return null;

  return (
    <Command.Dialog
      open={commandPaletteOpen}
      onOpenChange={setCommandPaletteOpen}
      className="rounded-lg border bg-background shadow-md"
    >
      <Command.Input
        placeholder="搜索命令... / Search commands..."
        className="w-full px-4 py-3 text-sm outline-none border-b"
      />
      <Command.List className="max-h-[300px] overflow-y-auto p-2">
        <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
          未找到结果 / No results found.
        </Command.Empty>

        <Command.Group heading="导航 / Navigation">
          {commands.map((cmd) => (
            <Command.Item
              key={cmd.id}
              value={cmd.label}
              onSelect={() => {
                router.push(cmd.href);
                setCommandPaletteOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer aria-selected:bg-muted"
            >
              <cmd.icon className="h-4 w-4" />
              <span>{cmd.label}</span>
            </Command.Item>
          ))}
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  );
}
