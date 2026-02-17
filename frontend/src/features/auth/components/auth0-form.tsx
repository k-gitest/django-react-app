import { useAuth } from '@/features/auth/hooks/use-auth0'
import { Button } from '@/components/ui/button'

export function LoginButton() {
  const { isAuthenticated, signIn, signOut, user } = useAuth()

  if (isAuthenticated) {
    return (
      <div className="flex items-center gap-4">
        <span>{user?.email}</span>
        <Button onClick={signOut}>ログアウト</Button>
      </div>
    )
  }

  return <Button onClick={signIn}>ログイン</Button>
}