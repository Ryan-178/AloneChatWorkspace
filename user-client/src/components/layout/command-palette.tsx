'use client'

import { useEffect, useState } from 'react'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { useUIStore } from '@/stores/ui-store'
import { useRouter } from 'next/navigation'
import {
  MessageSquare,
  Bot,
  FolderOpen,
  ListTodo,
  Puzzle,
  Settings,
  Moon,
  Sun,
  Monitor,
} from 'lucide-react'

const pages = [
  { href: '/chat', label: '聊天', icon: MessageSquare, group: '页面' },
  { href: '/agent', label: 'Agent', icon: Bot, group: '页面' },
  { href: '/workspace', label: '工作区', icon: FolderOpen, group: '页面' },
  { href: '/tasks', label: '任务', icon: ListTodo, group: '页面' },
  { href: '/skills', label: 'Skills', icon: Puzzle, group: '页面' },
  { href: '/settings', label: '设置', icon: Settings, group: '页面' },
]

const themes = [
  { value: 'light', label: '浅色主题', icon: Sun, group: '主题' },
  { value: 'dark', label: '深色主题', icon: Moon, group: '主题' },
  { value: 'system', label: '系统主题', icon: Monitor, group: '主题' },
]

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, setTheme } = useUIStore()
  const router = useRouter()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setCommandPaletteOpen(!commandPaletteOpen)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [commandPaletteOpen, setCommandPaletteOpen])

  const handleThemeChange = (value: string) => {
    setTheme(value as 'light' | 'dark' | 'system')
    
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    
    if (value === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(value)
    }
    
    setCommandPaletteOpen(false)
  }

  return (
    <CommandDialog open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen}>
      <CommandInput placeholder="搜索命令或页面..." />
      <CommandList>
        <CommandEmpty>未找到结果</CommandEmpty>
        
        <CommandGroup heading="页面">
          {pages.map(({ href, label, icon: Icon }) => (
            <CommandItem
              key={href}
              onSelect={() => {
                router.push(href)
                setCommandPaletteOpen(false)
              }}
              className="cursor-pointer"
            >
              <Icon className="mr-2 h-4 w-4" />
              {label}
            </CommandItem>
          ))}
        </CommandGroup>
        
        <CommandSeparator />
        
        <CommandGroup heading="主题">
          {themes.map(({ value, label, icon: Icon }) => (
            <CommandItem
              key={value}
              onSelect={() => handleThemeChange(value)}
              className="cursor-pointer"
            >
              <Icon className="mr-2 h-4 w-4" />
              {label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
