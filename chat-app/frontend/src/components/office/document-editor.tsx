"use client"

import { useEffect, useState, useCallback } from "react"
import { useEditor, EditorContent } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TextAlign from "@tiptap/extension-text-align"
import Highlight from "@tiptap/extension-highlight"
import Placeholder from "@tiptap/extension-placeholder"
import { OfficeLayout } from "./office-layout"
import { DocumentToolbar } from "./document-toolbar"
import { getLocalFile, updateLocalFileContent, updateLocalFileName } from "@/lib/file-store"

interface DocumentEditorProps {
  fileId: number
  onBack: () => void
}

export function DocumentEditor({ fileId, onBack }: DocumentEditorProps) {
  const [title, setTitle] = useState("未命名文档")
  const [saving, setSaving] = useState(false)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      Highlight,
      Placeholder.configure({ placeholder: "开始输入内容..." }),
    ],
    content: "",
    editorProps: {
      attributes: {
        class: "prose prose-sm max-w-none focus:outline-none min-h-[800px] p-8",
      },
    },
    onUpdate: ({ editor }) => {
      handleSave(editor.getJSON())
    },
  })

  useEffect(() => {
    let mounted = true
    async function load() {
      const file = await getLocalFile(fileId)
      if (!file || !mounted) return
      setTitle(file.filename)
      const content = file.content
      if (content && editor) {
        if (typeof content === "string") {
          editor.commands.setContent(content)
        } else if (content.paragraphs) {
          const html = paragraphsToHtml(content.paragraphs)
          editor.commands.setContent(html)
        } else {
          editor.commands.setContent(content)
        }
      }
    }
    load()
    return () => { mounted = false }
  }, [fileId, editor])

  const handleSave = useCallback(
    async (jsonContent: any) => {
      setSaving(true)
      await updateLocalFileContent(fileId, jsonContent)
      setTimeout(() => setSaving(false), 300)
    },
    [fileId]
  )

  const handleTitleChange = useCallback(
    async (newTitle: string) => {
      setTitle(newTitle)
      await updateLocalFileName(fileId, newTitle)
    },
    [fileId]
  )

  const handleExport = useCallback(() => {
    if (!editor) return
    const html = editor.getHTML()
    const blob = new Blob([html], { type: "text/html" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = title.replace(/\.docx$/, ".html")
    a.click()
    URL.revokeObjectURL(url)
  }, [editor, title])

  if (!editor) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        加载中...
      </div>
    )
  }

  return (
    <OfficeLayout
      fileId={fileId}
      fileType="document"
      title={title}
      onTitleChange={handleTitleChange}
      onBack={onBack}
      onSave={() => handleSave(editor.getJSON())}
      onExport={handleExport}
      saving={saving}
      toolbar={<DocumentToolbar editor={editor} />}
    >
      <div className="w-[21cm] min-h-[29.7cm] bg-white shadow-lg">
        <EditorContent editor={editor} />
      </div>
    </OfficeLayout>
  )
}

function paragraphsToHtml(paragraphs: any[]): string {
  return paragraphs
    .map((p) => {
      const align = p.alignment ? ` style="text-align:${p.alignment}"` : ""
      const runs = p.runs
        .map((r: any) => {
          let tag = "span"
          let styles = ""
          if (r.bold) styles += "font-weight:bold;"
          if (r.italic) styles += "font-style:italic;"
          if (r.underline) styles += "text-decoration:underline;"
          if (r.font_size) styles += `font-size:${r.font_size}pt;`
          const styleAttr = styles ? ` style="${styles}"` : ""
          return `<${tag}${styleAttr}>${escapeHtml(r.text)}</${tag}>`
        })
        .join("")
      const tag = p.style?.startsWith("Heading") ? `h${p.style.replace("Heading ", "")}` : "p"
      return `<${tag}${align}>${runs || escapeHtml(p.text)}</${tag}>`
    })
    .join("")
}

function escapeHtml(text: string): string {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}
