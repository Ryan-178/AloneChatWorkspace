'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { MessageSquare, Bot, FolderOpen, ListTodo, Puzzle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Logo } from '@/components/common/logo'

const navItems = [
  { href: '/chat', label: '聊天', icon: MessageSquare },
  { href: '/agent', label: 'Agent', icon: Bot },
  { href: '/workspace', label: '工作区', icon: FolderOpen },
  { href: '/tasks', label: '任务', icon: ListTodo },
  { href: '/skills', label: 'Skills', icon: Puzzle },
  { href: '/settings', label: '设置', icon: Settings },
]

export function MobileNav() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t bg-background md:hidden">
      {navItems.map(({ href, label, icon: Icon }) => {
        const isActive = pathname.startsWith(href)
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex flex-col items-center gap-1 px-3 py-2 text-xs transition-colors',
              isActive
                ? 'text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Icon className="h-5 w-5" />
            <span>{label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
