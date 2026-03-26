import {
  fetchMe,
  loginService,
  signupService,
  refreshTokenService,
  logoutService,
} from '@/features/auth/services/auth-service'

import { mockUser } from '@tests/mocks/auth.handlers'

describe('auth-service', () => {
  describe('fetchMe', () => {
    it('ユーザー情報を返す', async () => {
      const result = await fetchMe()
      expect(result).toEqual(mockUser)
    })
  })

  describe('loginService', () => {
    it('ログイン成功時にUserInfoを返す', async () => {
      const result = await loginService({
        email: 'test@example.com',
        password: 'password',
      })
      expect(result).toEqual(mockUser)
    })
  })

  describe('signupService', () => {
    it('サインアップ成功時にUserInfoを返す', async () => {
      const result = await signupService({
        email: 'test@example.com',
        password: 'password',
      })
      expect(result).toEqual(mockUser)
    })
  })

  describe('refreshTokenService', () => {
    it('新しいアクセストークンを返す', async () => {
      const result = await refreshTokenService('dummy-refresh-token')
      expect(result).toEqual({ access: 'new-access-token' })
    })
  })

  describe('logoutService', () => {
    it('正常にログアウトできる', async () => {
      await expect(logoutService()).resolves.toBeUndefined()
    })
  })
})