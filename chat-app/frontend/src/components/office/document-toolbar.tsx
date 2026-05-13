"use client"

import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  List,
  ListOrdered,
  Quote,
  Undo,
  Redo,
  Heading1,
  Heading2,
  Heading3,
} from "lucide-react"
import { Button } from "@/components/ui/button"

interface DocumentToolbarProps {
  editor: any
}

export function DocumentToolbar({ editor }: DocumentToolbarProps) {
  if (!editor) return null

  const groups = [
    {
      items: [
        { icon: Undo, action: () => editor.chain().focus().undo().run(), active: false },
        { icon: Redo, action: () => editor.chain().focus().redo().run(), active: false },
      ],
    },
    {
      items: [
        { icon: Bold, action: () => editor.chain().focus().toggleBold().run(), active: editor.isActive("bold") },
        { icon: Italic, action: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive("italic") },
        { icon: Underline, action: () => editor.chain().focus().toggleUnderline().run(), active: editor.isActive("underline") },
        { icon: Strikethrough, action: () => editor.chain().focus().toggleStrike().run(), active: editor.isActive("strike") },
      ],
    },
    {
      items: [
        { icon: AlignLeft, action: () => editor.chain().focus().setTextAlign("left").run(), active: editor.isActive({ textAlign: "left" }) },
        { icon: AlignCenter, action: () => editor.chain().focus().setTextAlign("center").run(), active: editor.isActive({ textAlign: "center" }) },
        { icon: AlignRight, action: () => editor.chain().focus().setTextAlign("right").run(), active: editor.isActive({ textAlign: "right" }) },
        { icon: AlignJustify, action: () => editor.chain().focus().setTextAlign("justify").run(), active: editor.isActive({ textAlign: "justify" }) },
      ],
    },
    {
      items: [
        { icon: List, action: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive("bulletList") },
        { icon: ListOrdered, action: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive("orderedList") },
        { icon: Quote, action: () => editor.chain().focus().toggleBlockquote().run(), active: editor.isActive("blockquote") },
      ],
    },
    {
      items: [
        { icon: Heading1, action: () => editor.chain().focus().toggleHeading({ level: 1 }).run(), active: editor.isActive("heading", { level: 1 }) },
        { icon: Heading2, action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(), active: editor.isActive("heading", { level: 2 }) },
        { icon: Heading3, action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(), active: editor.isActive("heading", { level: 3 }) },
      ],
    },
  ]

  return (
    <div className="flex items-center gap-1 px-3 py-1.5">
      {groups.map((group, gi) => (
        <div key={gi} className="flex items-center gap-0.5">
          {group.items.map((item, ii) => (
            <Button
              key={ii}
              variant={item.active ? "secondary" : "ghost"}
              size="icon"
              className="h-7 w-7"
              onClick={item.action}
            >
              <item.icon className="h-3.5 w-3.5" />
            </Button>
          ))}
          {gi < groups.length - 1 && <div className="w-px h-5 bg-border mx-1" />}
        </div>
      ))}
    </div>
  )
}
