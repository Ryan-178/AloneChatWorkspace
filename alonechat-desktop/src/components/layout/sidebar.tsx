"use client"

import { useUIStore } from "@/stores/ui-store";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  PanelLeftClose,
  PanelLeft,
  MessageSquare,
  Wrench,
  FolderOpen,
  Settings,
  Zap,
  LayoutDashboard,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "主页 / Home" },
  { href: "/agent", icon: MessageSquare, label: "Agent" },
  { href: "/tasks", icon: Zap, label: "任务 / Tasks" },
  { href: "/skills", icon: Wrench, label: "Skills" },
  { href: "/workspace", icon: FolderOpen, label: "工作区 / Workspace" },
  { href: "/settings", icon: Settings, label: "设置 / Settings" },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar, sidebarWidth } = useUIStore();
  const pathname = usePathname();

  if (!sidebarOpen) {
    return (
      <div className="w-14 border-r flex flex-col items-center py-4 gap-2">
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          <PanelLeft className="h-4 w-4" />
        </Button>
        <Separator className="w-8" />
        {navItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <Button
              variant={pathname === item.href ? "secondary" : "ghost"}
              size="icon"
              className="h-10 w-10"
            >
              <item.icon className="h-4 w-4" />
            </Button>
          </Link>
        ))}
      </div>
    );
  }

  return (
    <div
      className="border-r flex flex-col"
      style={{ width: sidebarWidth }}
    >
      <div className="p-3 flex items-center justify-between border-b">
        <span className="font-semibold text-sm">AloneChat</span>
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <nav className="p-2 space-y-1">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href}>
              <Button
                variant={pathname === item.href ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start gap-2",
                  pathname === item.href && "bg-primary/10 text-primary"
                )}
              >
                <item.icon className="h-4 w-4" />
                <span className="text-sm">{item.label}</span>
              </Button>
            </Link>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}
