"use client"

import type { ToolApprovalRequest } from "@/types/tool";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertTriangle, Check, X, Eye } from "lucide-react";
import { useState } from "react";

interface ToolApprovalCardProps {
  request: ToolApprovalRequest;
  onApprove: (remember: boolean) => void;
  onReject: () => void;
  onPreview?: () => void;
}

const dangerLevelColors = {
  safe: "bg-green-100 text-green-800 border-green-200",
  moderate: "bg-yellow-100 text-yellow-800 border-yellow-200",
  dangerous: "bg-red-100 text-red-800 border-red-200",
};

export function ToolApprovalCard({
  request,
  onApprove,
  onReject,
  onPreview,
}: ToolApprovalCardProps) {
  const [remember, setRemember] = useState(false);

  const isDangerous = request.permission_level === "dangerous";
  const dangerLevel = isDangerous
    ? "dangerous"
    : request.permission_level === "execute"
    ? "moderate"
    : "safe";

  return (
    <Card className={`border-2 ${isDangerous ? "border-red-500" : "border-yellow-500"}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            {isDangerous ? (
              <AlertTriangle className="h-5 w-5 text-red-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
            工具执行请求 / Tool Execution Request
          </CardTitle>
          <Badge className={dangerLevelColors[dangerLevel]}>
            {request.permission_level}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">工具:</span>
          <code className="px-2 py-1 bg-muted rounded font-mono">
            {request.tool_name}
          </code>
        </div>

        <div>
          <span className="text-muted-foreground text-sm">参数:</span>
          <ScrollArea className="h-[150px] mt-2 rounded-lg border bg-muted/50 p-2">
            <pre className="text-xs font-mono">
              {JSON.stringify(request.params, null, 2)}
            </pre>
          </ScrollArea>
        </div>

        {isDangerous && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
            <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
            <div className="text-sm text-red-800">
              <p className="font-medium">警告 / Warning</p>
              <p>此操作可能不可逆，请谨慎批准。</p>
              <p>This operation may be irreversible. Approve with caution.</p>
            </div>
          </div>
        )}

        <div className="flex items-center space-x-2">
          <Checkbox
            id="remember"
            checked={remember}
            onCheckedChange={(checked) => setRemember(checked as boolean)}
          />
          <label
            htmlFor="remember"
            className="text-sm text-muted-foreground cursor-pointer"
          >
            记住此选择 / Remember this choice
          </label>
        </div>
      </CardContent>

      <CardFooter className="flex justify-end gap-2">
        {onPreview && (
          <Button variant="outline" onClick={onPreview}>
            <Eye className="h-4 w-4 mr-2" />
            预览 / Preview
          </Button>
        )}
        <Button variant="destructive" onClick={onReject}>
          <X className="h-4 w-4 mr-2" />
          拒绝 / Reject
        </Button>
        <Button onClick={() => onApprove(remember)}>
          <Check className="h-4 w-4 mr-2" />
          批准 / Approve
        </Button>
      </CardFooter>
    </Card>
  );
}

interface BatchApprovalCardProps {
  requests: ToolApprovalRequest[];
  onApproveAll: () => void;
  onRejectAll: () => void;
  onReviewIndividual: () => void;
}

export function BatchApprovalCard({
  requests,
  onApproveAll,
  onRejectAll,
  onReviewIndividual,
}: BatchApprovalCardProps) {
  const dangerousCount = requests.filter(
    (r) => r.permission_level === "dangerous"
  ).length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-500" />
          批量工具审批 / Batch Tool Approval
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">
          共 {requests.length} 个工具请求待审批
        </p>
        {dangerousCount > 0 && (
          <p className="text-red-500 text-sm mt-2">
            其中 {dangerousCount} 个为危险操作
          </p>
        )}
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" onClick={onReviewIndividual}>
          逐个审查 / Review Individual
        </Button>
        <Button variant="destructive" onClick={onRejectAll}>
          全部拒绝 / Reject All
        </Button>
        <Button onClick={onApproveAll}>
          全部批准 / Approve All
        </Button>
      </CardFooter>
    </Card>
  );
}
