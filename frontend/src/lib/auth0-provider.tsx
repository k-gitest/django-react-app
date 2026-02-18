import { Auth0Provider as Auth0ProviderBase } from '@auth0/auth0-react'
import type { ReactNode } from 'react'
import { VITE_AUTH0_DOMAIN, VITE_AUTH0_CLIENT_ID, VITE_AUTH0_AUDIENCE } from '@/lib/constants';

interface Props {
  children: ReactNode
}

export function Auth0Provider({ children }: Props) {
  return (
    <Auth0ProviderBase
      domain={VITE_AUTH0_DOMAIN!}
      clientId={VITE_AUTH0_CLIENT_ID!}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: VITE_AUTH0_AUDIENCE,
        scope: 'openid profile email',
      }}
      useRefreshTokens={true}
      cacheLocation="localstorage"
    >
      {children}
    </Auth0ProviderBase>
  )
}