"use client";

import { skillApi } from "@/lib/api";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Wrench, Search, Play, Download } from "lucide-react";
import type { Skill } from "@/types";

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async (category?: string, query?: string) => {
    setIsLoading(true);
    try {
      const response = await skillApi.list(category, query);
      setSkills(response.skills);
      setCategories(response.categories);
    } catch (error) {
      console.error("Failed to load skills:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    loadSkills(selectedCategory || undefined, query || undefined);
  };

  const handleCategorySelect = (category: string | null) => {
    setSelectedCategory(category);
    loadSkills(category || undefined, searchQuery || undefined);
  };

  return (
    <div className="p-6 h-full overflow-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Skills 市场 / Skills Marketplace</h1>
        <p className="text-muted-foreground text-sm">
          浏览和执行可用的 Skills / Browse and execute available skills
        </p>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索 Skills... / Search skills..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        <Button
          variant={selectedCategory === null ? "default" : "outline"}
          size="sm"
          onClick={() => handleCategorySelect(null)}
        >
          全部 / All
        </Button>
        {categories.map((category) => (
          <Button
            key={category}
            variant={selectedCategory === category ? "default" : "outline"}
            size="sm"
            onClick={() => handleCategorySelect(category)}
          >
            {category}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">加载中...</div>
      ) : skills.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg mb-2">暂无 Skills / No skills found</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {skills.map((skill) => (
            <Card key={skill.name}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Wrench className="h-4 w-4" />
                    {skill.name}
                  </CardTitle>
                  {skill.is_installed ? (
                    <Badge variant="secondary">已安装</Badge>
                  ) : (
                    <Badge variant="outline">未安装</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                  {skill.description}
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1 gap-1">
                    <Play className="h-3 w-3" />
                    执行
                  </Button>
                  {!skill.is_installed && (
                    <Button size="sm" variant="ghost" className="gap-1">
                      <Download className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
