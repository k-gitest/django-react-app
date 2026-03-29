import { describe, it, expect, vi, beforeEach } from 'vitest';

/* =========================
   テスト対象
========================= */
import {
  fetchMeGraphQL,
  loginServiceGraphQL,
  signupServiceGraphQL,
  refreshTokenServiceGraphQL,
  logoutServiceGraphQL,
} from '@/features/auth/services/implementations/auth-service-graphql';

/* =========================
   モック対象
========================= */
import { gqlRequest, gqlMutation } from '@/lib/graphql-client';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

vi.mock('@/lib/graphql-client', () => ({
  gqlRequest: vi.fn(),
  gqlMutation: vi.fn(),
}));

// GraphQLクエリ・ミューテーション定数はモック不要（gqlRequest/gqlMutationをモックするため）
vi.mock('@/graphql/queries/user', () => ({
  GET_ME: 'GET_ME',
}));

vi.mock('@/graphql/mutations/user', () => ({
  REGISTER: 'REGISTER',
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
}));

/* =========================
   モック参照
========================= */

const mockGqlRequest = gqlRequest as ReturnType<typeof vi.fn>;
const mockGqlMutation = gqlMutation as ReturnType<typeof vi.fn>;

/* =========================
   ダミーデータ
========================= */

// GraphQL側のUserType形式（スネークケースではなくキャメルケース）
const mockGraphQLUser = {
  id: '1',           // GraphQLはID型なので文字列
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  isStaff: false,
};

// graphqlUserToUserInfoで変換後のUserInfo形式（auth-service.tsが扱う統一型）
const expectedUserInfo = {
  id: 1,             // Number変換される
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

const mockAccount = {
  email: 'test@example.com',
  password: 'password',
};

/* =========================
   テスト本体
========================= */

describe('auth-service-graphql', () => {

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* --------------------
     fetchMeGraphQL
  -------------------- */

  describe('fetchMeGraphQL', () => {
    it('gqlRequestを呼び、GraphQL UserType → UserInfo に変換して返す', async () => {
      mockGqlRequest.mockResolvedValue({ me: mockGraphQLUser });

      const result = await fetchMeGraphQL();

      expect(mockGqlRequest).toHaveBeenCalledWith('GET_ME');
      expect(result).toEqual(expectedUserInfo);
    });

    it('data.meがnullのとき エラーをスローする', async () => {
      mockGqlRequest.mockResolvedValue({ me: null });

      await expect(fetchMeGraphQL()).rejects.toThrow(
        'ユーザー情報が取得できませんでした'
      );
    });

    it('gqlRequestが失敗したとき エラーをスローする', async () => {
      mockGqlRequest.mockRejectedValue(new Error('Network error'));

      await expect(fetchMeGraphQL()).rejects.toThrow('Network error');
    });
  });

  /* --------------------
     loginServiceGraphQL
  -------------------- */

  describe('loginServiceGraphQL', () => {
    it('LoginInputを組み立ててgqlMutationを呼び、UserInfoを返す', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'AuthPayload',
        user: mockGraphQLUser,
      });

      const result = await loginServiceGraphQL(mockAccount);

      expect(mockGqlMutation).toHaveBeenCalledWith(
        'LOGIN',
        {
          input: {
            email: 'test@example.com',
            password: 'password',
          },
        },
        'login'
      );
      expect(result).toEqual(expectedUserInfo);
    });

    it('__typenameがAuthPayload以外のとき エラーをスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'ValidationError',
        message: 'Invalid credentials',
      });

      await expect(loginServiceGraphQL(mockAccount)).rejects.toThrow(
        'ログインに失敗しました'
      );
    });

    it('gqlMutationが失敗したとき エラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Auth error'));

      await expect(loginServiceGraphQL(mockAccount)).rejects.toThrow('Auth error');
    });
  });

  /* --------------------
     signupServiceGraphQL
  -------------------- */

  describe('signupServiceGraphQL', () => {
    it('RegisterInputを組み立ててgqlMutationを呼び、UserInfoを返す', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'AuthPayload',
        user: mockGraphQLUser,
      });

      const result = await signupServiceGraphQL(mockAccount);

      // signupはpassword1/2ではなくpassword/passwordConfirmで送る
      expect(mockGqlMutation).toHaveBeenCalledWith(
        'REGISTER',
        {
          input: {
            email: 'test@example.com',
            password: 'password',
            passwordConfirm: 'password',
            firstName: '',
            lastName: '',
          },
        },
        'register'
      );
      expect(result).toEqual(expectedUserInfo);
    });

    it('__typenameがAuthPayload以外のとき エラーをスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'ValidationError',
        message: 'Email already exists',
      });

      await expect(signupServiceGraphQL(mockAccount)).rejects.toThrow(
        'サインアップに失敗しました'
      );
    });

    it('gqlMutationが失敗したとき エラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Registration error'));

      await expect(signupServiceGraphQL(mockAccount)).rejects.toThrow(
        'Registration error'
      );
    });
  });

  /* --------------------
     refreshTokenServiceGraphQL
  -------------------- */

  describe('refreshTokenServiceGraphQL', () => {
    it('Cookie認証互換のダミー値 { access: "" } を返す', async () => {
      // gqlRequest/gqlMutationは呼ばない（ダミー実装）
      const result = await refreshTokenServiceGraphQL();

      expect(result).toEqual({ access: '' });
      expect(mockGqlRequest).not.toHaveBeenCalled();
      expect(mockGqlMutation).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     logoutServiceGraphQL
  -------------------- */

  describe('logoutServiceGraphQL', () => {
    it('LOGOUTミューテーションを呼ぶ', async () => {
      mockGqlMutation.mockResolvedValue(undefined);

      await logoutServiceGraphQL();

      expect(mockGqlMutation).toHaveBeenCalledWith(
        'LOGOUT',
        undefined,
        'logout'
      );
    });

    it('戻り値はundefined', async () => {
      mockGqlMutation.mockResolvedValue(undefined);

      await expect(logoutServiceGraphQL()).resolves.toBeUndefined();
    });

    it('gqlMutationが失敗したとき エラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Logout error'));

      await expect(logoutServiceGraphQL()).rejects.toThrow('Logout error');
    });
  });

  /* --------------------
     graphqlUserToUserInfo（型変換の検証）
  -------------------- */

  describe('graphqlUserToUserInfo（型変換の境界値）', () => {
    it('idが文字列でも Numberに変換される', async () => {
      mockGqlRequest.mockResolvedValue({
        me: { ...mockGraphQLUser, id: '999' },
      });

      const result = await fetchMeGraphQL();

      expect(result.id).toBe(999);
      expect(typeof result.id).toBe('number');
    });

    it('firstName/lastNameがnullのとき first_name/last_nameはundefinedになる', async () => {
      mockGqlRequest.mockResolvedValue({
        me: {
          ...mockGraphQLUser,
          firstName: null,
          lastName: null,
        },
      });

      const result = await fetchMeGraphQL();

      expect(result.first_name).toBeUndefined();
      expect(result.last_name).toBeUndefined();
    });

    it('isStaffがtrueのとき is_staffもtrueになる', async () => {
      mockGqlRequest.mockResolvedValue({
        me: { ...mockGraphQLUser, isStaff: true },
      });

      const result = await fetchMeGraphQL();

      expect(result.is_staff).toBe(true);
    });
  });
});