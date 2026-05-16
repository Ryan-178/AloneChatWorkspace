'use client'

import { useTranslations } from 'next-intl'
import { Plus, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/common/empty-state'
import { MessageSquare } from 'lucide-react'

export default function ChatPage() {
  const t = useTranslations('chat')
  
  return (
    <div className="flex h-full">
      <aside className="w-80 border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder={t('searchPlaceholder')} className="pl-9" />
            </div>
            <Button size="icon" variant="outline">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-auto p-2">
          <EmptyState
            icon={<MessageSquare className="h-8 w-8 text-muted-foreground" />}
            title={t('noConversations')}
            description={t('startNew')}
            action={
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                {t('newChat')}
              </Button>
            }
          />
        </div>
      </aside>
      <main className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<MessageSquare className="h-12 w-12 text-muted-foreground" />}
            title={t('selectConversation')}
            description={t('selectOrNew')}
          />
        </div>
      </main>
    </div>
  )
}
