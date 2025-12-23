import { http, HttpResponse } from 'msw'
import type { TokenResponse, UserInfo } from '@/features/auth/types/auth'

export const mockUser: UserInfo = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
}

export const mockToken: TokenResponse = {
  access: 'access-token',
  refresh: 'refresh-token',
}

export const authHandlers = [
  http.get(`**/auth/user/`, () =>
    HttpResponse.json(mockUser, { status: 200 })
  ),

  http.post(`**/auth/login/`, () =>
    HttpResponse.json(mockToken, { status: 200 })
  ),

  http.post(`**/auth/registration/`, () =>
    HttpResponse.json(mockToken, { status: 201 })
  ),

  http.post(`**/auth/token/refresh/`, () =>
    HttpResponse.json({ access: 'new-access-token' }, { status: 200 })
  ),

  http.post(`**/auth/logout/`, () =>
    HttpResponse.json(null, { status: 204 })
  ),
]
