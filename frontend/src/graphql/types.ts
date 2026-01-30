/**
 * GraphQL型定義
 * 
 * ※ GraphQL Code Generatorで自動生成も可能
 */

// ============================================================================
// Enum
// ============================================================================

export enum PriorityEnum {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
}

export enum ErrorCategory {
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  NOT_FOUND = 'not_found',
  CONFLICT = 'conflict',
  RATE_LIMIT = 'rate_limit',
  EXTERNAL_SERVICE = 'external_service',
  INTERNAL = 'internal',
}

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