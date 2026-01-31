/**
 * GraphQL型定義
 * 
 * ※ GraphQL Code Generatorで自動生成も可能
 */

// ============================================================================
// Enum (const object + type に変更して erasableSyntaxOnly エラーを回避)
// ============================================================================

export const PriorityEnum = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
} as const;
export type PriorityEnum = typeof PriorityEnum[keyof typeof PriorityEnum];

export const ErrorCategory = {
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  NOT_FOUND: 'not_found',
  CONFLICT: 'conflict',
  RATE_LIMIT: 'rate_limit',
  EXTERNAL_SERVICE: 'external_service',
  INTERNAL: 'internal',
} as const;
export type ErrorCategory = typeof ErrorCategory[keyof typeof ErrorCategory];

// ============================================================================
// Types
// ============================================================================

export interface TodoType {
  __typename: 'TodoType';
  id: string; // Relay GlobalID (Base64)
  todoTitle: string;
  priority: PriorityEnum;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

export interface PriorityStatsType {
  priority: PriorityEnum;
  count: number;
}

export interface ProgressStatsType {
  range020: number;
  range2140: number;
  range4160: number;
  range6180: number;
  range81100: number;
}

export interface SearchResultType {
  id: number;
  todoTitle: string;
  priority: PriorityEnum;
  progress: number;
  score: number;
}

// ============================================================================
// Input Types
// ============================================================================

export interface TodoCreateInput {
  todoTitle: string;
  priority: PriorityEnum;
  progress?: number;
}

export interface TodoUpdateInput {
  todoTitle?: string;
  priority?: PriorityEnum;
  progress?: number;
}

export interface TodoSearchInput {
  query: string;
  topK?: number;
  minScore?: number;
}

// ============================================================================
// Error Types
// ============================================================================

export interface ValidationError {
  __typename: 'ValidationError';
  category: ErrorCategory;
  message: string;
  field?: string;
  code: string;
}

export interface AuthenticationError {
  __typename: 'AuthenticationError';
  category: typeof ErrorCategory.AUTHENTICATION;
  message: string;
  code: string;
}
export interface ConflictError {
  __typename: 'ConflictError';
  category: ErrorCategory;
  message: string;
  conflictingField?: string;
  code: string;
}

export interface NotFoundError {
  __typename: 'NotFoundError';
  category: ErrorCategory;
  message: string;
  resourceType?: string;
  resourceId?: string;
  code: string;
}

export interface InternalError {
  __typename: 'InternalError';
  category: ErrorCategory;
  message: string;
  code: string;
  debugInfo?: string;
}

export interface ExternalServiceError {
  __typename: 'ExternalServiceError';
  category: ErrorCategory;
  message: string;
  serviceName?: string;
  code: string;
}

export interface Success {
  __typename: 'Success';
  message: string;
  success: boolean;
}

// ============================================================================
// Result Union Types
// ============================================================================

export type TodoResult =
  | TodoType
  | ValidationError
  | ConflictError
  | NotFoundError
  | InternalError;

export type DeleteResult =
  | Success
  | NotFoundError
  | InternalError;

export type BulkIndexResult =
  | Success
  | ExternalServiceError
  | InternalError;

// ============================================================================
// Query Response Types
// ============================================================================

export interface GetTodosQuery {
  todos: TodoType[];
}

export interface GetTodoQuery {
  todo: TodoType | null;
}

export interface GetTodoStatsQuery {
  priorityStats: PriorityStatsType[];
}

export interface GetProgressStatsQuery {
  progressStats: ProgressStatsType;
}

export interface SearchTodosQuery {
  searchTodos: SearchResultType[];
}

// ============================================================================
// Mutation Response Types
// ============================================================================

export interface CreateTodoMutation {
  createTodo: TodoResult;
}

export interface UpdateTodoMutation {
  updateTodo: TodoResult;
}

export interface DeleteTodoMutation {
  deleteTodo: DeleteResult;
}

export interface BulkIndexTodosMutation {
  bulkIndexTodos: BulkIndexResult;
}

// ============================================================================
// User Types
// ============================================================================

export interface UserType {
  __typename: 'UserType';
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  dateJoined: string;
}

export interface AuthPayload {
  __typename: 'AuthPayload';
  user: UserType;
  message: string;
}

// ============================================================================
// Input Types (User)
// ============================================================================

export interface RegisterInput {
  email: string;
  password: string;
  passwordConfirm: string;
  firstName?: string;
  lastName?: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

// ============================================================================
// Result Union Types (User)
// ============================================================================

export type AuthResult =
  | AuthPayload
  | ValidationError
  | ConflictError
  | InternalError;

export type LogoutResult =
  | Success
  | AuthenticationError
  | InternalError;

// ============================================================================
// Query/Mutation Response Types (User)
// ============================================================================

export interface GetMeQuery {
  me: UserType | null;
}

export interface RegisterMutation {
  register: AuthResult;
}

export interface LoginMutation {
  login: AuthResult;
}

export interface LogoutMutation {
  logout: LogoutResult;
}