import {
  fetchMe,
  loginService,
  signupService,
  refreshTokenService,
  logoutService,
} from '@/features/auth/services/auth-service'

import { mockUser, mockToken } from '@tests/mocks/auth.handlers'

describe('auth-service', () => {
  it('fetchMe', async () => {
    const result = await fetchMe()
    expect(result).toEqual(mockUser)
  })

  it('loginService', async () => {
    const result = await loginService({
      email: 'test@example.com',
      password: 'password',
    })
    expect(result).toEqual(mockToken)
  })

  it('signupService', async () => {
    const result = await signupService({
      email: 'test@example.com',
      password: 'password',
    })
    expect(result).toEqual(mockToken)
  })

  it('refreshTokenService', async () => {
    const result = await refreshTokenService()
    expect(result).toEqual({ access: 'new-access-token' })
  })

  it('logoutService', async () => {
    await expect(logoutService()).resolves.toBeUndefined()
  })
})
