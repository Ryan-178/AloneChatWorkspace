"use client";

import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Moon, Sun, Monitor, Save } from "lucide-react";
import { useTheme } from "next-themes";
import { useState } from "react";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user } = useAuthStore();
  const [apiKey, setApiKey] = useState("");

  const themes = [
    { value: "light", icon: Sun, label: "浅色 / Light" },
    { value: "dark", icon: Moon, label: "深色 / Dark" },
    { value: "system", icon: Monitor, label: "系统 / System" },
  ] as const;

  return (
    <div className="p-6 h-full overflow-auto max-w-2xl">
      <h1 className="text-2xl font-semibold mb-6">设置 / Settings</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">外观 / Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            选择应用的主题模式 / Choose the application theme mode
          </p>
          <div className="flex gap-2">
            {themes.map((t) => {
              const Icon = t.icon;
              return (
                <Button
                  key={t.value}
                  variant={theme === t.value ? "default" : "outline"}
                  className="gap-2"
                  onClick={() => setTheme(t.value)}
                >
                  <Icon className="h-4 w-4" />
                  {t.label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">API 配置 / API Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              API Key
            </label>
            <div className="flex gap-2">
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="输入 API Key / Enter API Key"
                className="flex-1"
              />
              <Button className="gap-2">
                <Save className="h-4 w-4" />
                保存
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {user && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">账户 / Account</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <p>
                <span className="text-muted-foreground">用户名:</span> {user.username}
              </p>
              <p>
                <span className="text-muted-foreground">邮箱:</span> {user.email}
              </p>
              <p>
                <span className="text-muted-foreground">ID:</span>{" "}
                <code className="text-xs bg-muted px-1 rounded">{user.id}</code>
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
