'use client'

import { useTranslations } from 'next-intl'
import { Settings as SettingsIcon, User, Bell, Palette, Key } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/common/theme-toggle'

export default function SettingsPage() {
  const t = useTranslations('settings')
  
  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-semibold mb-6">{t('title')}</h1>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {t('profile.title')}
            </CardTitle>
            <CardDescription>
              {t('profile.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">{t('profile.username')}</Label>
                <Input id="username" placeholder={t('profile.username')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">{t('profile.email')}</Label>
                <Input id="email" type="email" placeholder={t('profile.email')} />
              </div>
            </div>
            <Button>{t('profile.save')}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              {t('appearance.title')}
            </CardTitle>
            <CardDescription>
              {t('appearance.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t('appearance.theme')}</Label>
                <p className="text-sm text-muted-foreground">
                  {t('appearance.themeDescription')}
                </p>
              </div>
              <ThemeToggle />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              {t('api.title')}
            </CardTitle>
            <CardDescription>
              {t('api.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="apiKey">{t('api.key')}</Label>
              <Input id="apiKey" type="password" placeholder="sk-..." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="apiBase">{t('api.baseUrl')}</Label>
              <Input id="apiBase" placeholder="https://api.openai.com/v1" />
            </div>
            <Button>{t('api.save')}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              {t('notifications.title')}
            </CardTitle>
            <CardDescription>
              {t('notifications.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t('notifications.desktop')}</Label>
                <p className="text-sm text-muted-foreground">
                  {t('notifications.desktopDescription')}
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t('notifications.sound')}</Label>
                <p className="text-sm text-muted-foreground">
                  {t('notifications.soundDescription')}
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
