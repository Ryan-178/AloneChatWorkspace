"use client"

import { useState, useEffect } from "react"
import { DocumentEditor } from "./document-editor"
import { SpreadsheetEditor } from "./spreadsheet-editor"
import { PresentationEditor } from "./presentation-editor"
import { getLocalFile } from "@/lib/file-store"

interface OfficeAreaProps {
  fileId: number
  fileType: "document" | "spreadsheet" | "presentation"
  onBack: () => void
}

export function OfficeArea({ fileId, fileType, onBack }: OfficeAreaProps) {
  const [loading, setLoading] = useState(true)
  const [exists, setExists] = useState(false)

  useEffect(() => {
    let mounted = true
    async function load() {
      const file = await getLocalFile(fileId)
      if (mounted) {
        setExists(!!file)
        setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [fileId])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!exists) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        文件不存在或已被删除
      </div>
    )
  }

  if (fileType === "document") {
    return <DocumentEditor fileId={fileId} onBack={onBack} />
  }

  if (fileType === "spreadsheet") {
    return <SpreadsheetEditor fileId={fileId} onBack={onBack} />
  }

  if (fileType === "presentation") {
    return <PresentationEditor fileId={fileId} onBack={onBack} />
  }

  return (
    <div className="flex h-full items-center justify-center text-muted-foreground">
      不支持的文件类型
    </div>
  )
}
