"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

export default function HomePage() {
  const router = useRouter()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (token) {
      router.push("/chat")
    }
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      if (isLogin) {
        const res = await api.auth.login({ email, password })
        localStorage.setItem("token", res.access_token)
        router.push("/chat")
      } else {
        await api.auth.register({ email, password, display_name: displayName })
        const res = await api.auth.login({ email, password })
        localStorage.setItem("token", res.access_token)
        router.push("/chat")
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 p-4">
      <div className="w-full max-w-sm space-y-6 rounded-xl bg-card p-8 shadow">
        <div className="text-center">
          <h1 className="text-2xl font-bold">{isLogin ? "登录" : "注册"}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {isLogin ? "欢迎回来" : "创建新账户"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="text-sm font-medium">昵称</label>
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                placeholder="请输入昵称"
              />
            </div>
          )}
          <div>
            <label className="text-sm font-medium">邮箱</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="请输入邮箱"
            />
          </div>
          <div>
            <label className="text-sm font-medium">密码</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="请输入密码"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" className="w-full cursor-pointer" disabled={loading}>
            {loading ? "请稍候..." : isLogin ? "登录" : "注册"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          {isLogin ? "还没有账户？" : "已有账户？"}
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="ml-1 text-primary hover:underline cursor-pointer"
          >
            {isLogin ? "立即注册" : "立即登录"}
          </button>
        </p>
      </div>
    </div>
  )
}
