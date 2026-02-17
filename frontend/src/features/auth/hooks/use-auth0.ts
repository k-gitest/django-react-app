import { useAuth0 } from '@auth0/auth0-react'

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    loginWithRedirect,
    logout,
    getAccessTokenSilently,
  } = useAuth0()

  return {
    user,
    isAuthenticated,
    isLoading,
    signIn: () => loginWithRedirect(),
    signOut: () => logout({ 
      logoutParams: { returnTo: window.location.origin } 
    }),
    getAccessToken: () => getAccessTokenSilently(),
  }
}