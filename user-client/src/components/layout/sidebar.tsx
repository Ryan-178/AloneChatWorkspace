'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import {
  MessageSquare,
  Bot,
  FolderOpen,
  ListTodo,
  Puzzle,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Logo } from '@/components/common/logo'
import { ThemeToggle } from '@/components/common/theme-toggle'
import { LanguageSwitcher } from '@/components/common/language-switcher'
import { useUIStore } from '@/stores/ui-store'
import { useAuthStore } from '@/stores/auth-store'

const navItems = [
  { href: '/chat', labelKey: 'chat', icon: MessageSquare },
  { href: '/agent', labelKey: 'agent', icon: Bot },
  { href: '/workspace', labelKey: 'workspace', icon: FolderOpen },
  { href: '/tasks', labelKey: 'tasks', icon: ListTodo },
  { href: '/skills', labelKey: 'skills', icon: Puzzle },
]

const bottomNavItems = [
  { href: '/settings', labelKey: 'settings', icon: Settings },
]

export function Sidebar() {
  const t = useTranslations('nav')
  const pathname = usePathname()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const { user } = useAuthStore()

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-14 items-center justify-between px-4 border-b border-sidebar-border">
        {!sidebarCollapsed && <Logo />}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="h-8 w-8"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2 py-4">
        <nav className="space-y-1">
          {navItems.map(({ href, labelKey, icon: Icon }) => {
            const isActive = pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors cursor-pointer',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && <span>{t(labelKey)}</span>}
              </Link>
            )
          })}
        </nav>
      </ScrollArea>

      <Separator className="mx-2" />

      <div className="p-2 space-y-1">
        {bottomNavItems.map(({ href, labelKey, icon: Icon }) => {
          const isActive = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors cursor-pointer',
                isActive
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>{t(labelKey)}</span>}
            </Link>
          )
        })}

        {!sidebarCollapsed && (
          <div className="flex items-center justify-between px-3 py-2">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
        )}

        {!sidebarCollapsed && user?.username && (
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm font-medium truncate">{user.username}</span>
          </div>
        )}
      </div>
    </aside>
  )
}
