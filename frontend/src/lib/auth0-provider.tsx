import { Auth0Provider } from '@auth0/auth0-react'
import type { ReactNode } from 'react'

const domain = import.meta.env.VITE_AUTH0_DOMAIN
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID
const audience = import.meta.env.VITE_AUTH0_AUDIENCE

interface Props {
  children: ReactNode
}

export function AuthProvider({ children }: Props) {
  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin + '/auth/callback',
        audience: audience,
      }}
    >
      {children}
    </Auth0Provider>
  )
}