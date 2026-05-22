"use client"

import type { ToolInfo } from "@/types/tool";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Terminal,
  FileText,
  GitBranch,
  Globe,
  Code,
  Wrench,
} from "lucide-react";

interface ToolsPanelProps {
  tools: ToolInfo[];
  enabledTools: string[];
  onToggle: (toolName: string, enabled: boolean) => void;
}

const categoryIcons = {
  shell: Terminal,
  file: FileText,
  git: GitBranch,
  web: Globe,
  code: Code,
  general: Wrench,
};

const categoryColors = {
  shell: "bg-yellow-500",
  file: "bg-blue-500",
  git: "bg-green-500",
  web: "bg-purple-500",
  code: "bg-cyan-500",
  general: "bg-gray-500",
};

const permissionColors = {
  read: "bg-green-100 text-green-800",
  write: "bg-yellow-100 text-yellow-800",
  execute: "bg-orange-100 text-orange-800",
  dangerous: "bg-red-100 text-red-800",
};

export function ToolsPanel({ tools, enabledTools, onToggle }: ToolsPanelProps) {
  const groupedTools = tools.reduce((acc, tool) => {
    const category = tool.category || "general";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(tool);
    return acc;
  }, {} as Record<string, ToolInfo[]>);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="h-5 w-5" />
          工具面板 / Tools Panel
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          {Object.entries(groupedTools).map(([category, categoryTools]) => {
            const Icon = categoryIcons[category as keyof typeof categoryIcons] || Wrench;
            const color = categoryColors[category as keyof typeof categoryColors] || "bg-gray-500";

            return (
              <div key={category} className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1 rounded ${color}`}>
                    <Icon className="h-4 w-4 text-white" />
                  </div>
                  <span className="font-medium capitalize">{category}</span>
                  <Badge variant="outline" className="ml-auto">
                    {categoryTools.length}
                  </Badge>
                </div>

                <div className="space-y-2 pl-6">
                  {categoryTools.map((tool) => {
                    const isEnabled = enabledTools.includes(tool.name);
                    const permColor = permissionColors[tool.permission_level as keyof typeof permissionColors] || "bg-gray-100";

                    return (
                      <div
                        key={tool.name}
                        className="flex items-center justify-between p-2 rounded-lg border bg-card"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm">{tool.name}</span>
                            <Badge className={permColor}>
                              {tool.permission_level}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground truncate">
                            {tool.description}
                          </p>
                        </div>
                        <Switch
                          checked={isEnabled}
                          onCheckedChange={(checked) => onToggle(tool.name, checked)}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
