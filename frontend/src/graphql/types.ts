export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  Date: { input: string; output: string; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
  GlobalID: { input: string; output: string; }
};

export type AuthPayload = {
  __typename?: 'AuthPayload';
  Authpayload_Typename: Scalars['String']['output'];
  message: Scalars['String']['output'];
  user: UserType;
};

export type AuthResult = AuthPayload | ConflictError | ExternalServiceError | InternalError | RateLimitError | ValidationError;

export type AuthenticationError = {
  __typename?: 'AuthenticationError';
  Authenticationerror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type AuthorizationError = {
  __typename?: 'AuthorizationError';
  Authorizationerror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type ChangePasswordInput = {
  /** 新しいパスワード */
  newPassword: Scalars['String']['input'];
  /** 新しいパスワード（確認） */
  newPasswordConfirm: Scalars['String']['input'];
  /** 現在のパスワード */
  oldPassword: Scalars['String']['input'];
};

export type ChangePasswordResult = AuthenticationError | InternalError | Success | ValidationError;

export type ConflictError = {
  __typename?: 'ConflictError';
  Conflicterror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  conflictingField?: Maybe<Scalars['String']['output']>;
  message: Scalars['String']['output'];
};

export type CreateTodoPayload = {
  __typename?: 'CreateTodoPayload';
  todoEdge: TodoEdge;
};

export type DeleteTodoPayload = {
  __typename?: 'DeleteTodoPayload';
  deletedTodoId: Scalars['ID']['output'];
  message: Scalars['String']['output'];
};

export type ErrorCategory =
  | 'AUTHENTICATION'
  | 'AUTHORIZATION'
  | 'CONFLICT'
  | 'EXTERNAL_SERVICE'
  | 'INTERNAL'
  | 'NOT_FOUND'
  | 'RATE_LIMIT'
  | 'VALIDATION';

export type ExternalServiceError = {
  __typename?: 'ExternalServiceError';
  Externalserviceerror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
  serviceName?: Maybe<Scalars['String']['output']>;
};

export type InternalError = {
  __typename?: 'InternalError';
  Internalerror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  debugInfo?: Maybe<Scalars['String']['output']>;
  message: Scalars['String']['output'];
};

export type LoginInput = {
  /** メールアドレス */
  email: Scalars['String']['input'];
  /** パスワード */
  password: Scalars['String']['input'];
};

export type LogoutResult = AuthenticationError | InternalError | Success;

export type Mutation = {
  __typename?: 'Mutation';
  bulkIndexTodos: SuccessExternalServiceErrorInternalError;
  changePassword: ChangePasswordResult;
  createTodo: TodoCreateResult;
  deleteTodo: TodoDeleteResult;
  login: AuthResult;
  logout: LogoutResult;
  register: AuthResult;
  updateTodo: TodoUpdateResult;
};


export type MutationChangePasswordArgs = {
  input: ChangePasswordInput;
};


export type MutationCreateTodoArgs = {
  input: TodoCreateInput;
};


export type MutationDeleteTodoArgs = {
  id: Scalars['ID']['input'];
};


export type MutationLoginArgs = {
  input: LoginInput;
};


export type MutationRegisterArgs = {
  input: RegisterInput;
};


export type MutationUpdateTodoArgs = {
  id: Scalars['ID']['input'];
  input: TodoUpdateInput;
};

/** An object with a Globally Unique ID */
export type Node = {
  /** The Globally Unique ID of this object */
  id: Scalars['ID']['output'];
};

export type NotFoundError = {
  __typename?: 'NotFoundError';
  Notfounderror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
  resourceId?: Maybe<Scalars['String']['output']>;
  resourceType?: Maybe<Scalars['String']['output']>;
};

/** Information to aid in pagination. */
export type PageInfo = {
  __typename?: 'PageInfo';
  /** When paginating forwards, the cursor to continue. */
  endCursor?: Maybe<Scalars['String']['output']>;
  /** When paginating forwards, are there more items? */
  hasNextPage: Scalars['Boolean']['output'];
  /** When paginating backwards, are there more items? */
  hasPreviousPage: Scalars['Boolean']['output'];
  /** When paginating backwards, the cursor to continue. */
  startCursor?: Maybe<Scalars['String']['output']>;
};

export type PriorityEnum =
  | 'HIGH'
  | 'LOW'
  | 'MEDIUM';

export type PriorityStatsType = {
  __typename?: 'PriorityStatsType';
  count: Scalars['Int']['output'];
  priority: PriorityEnum;
};

export type ProgressStatsType = {
  __typename?: 'ProgressStatsType';
  range020: Scalars['Int']['output'];
  range2140: Scalars['Int']['output'];
  range4160: Scalars['Int']['output'];
  range6180: Scalars['Int']['output'];
  range81100: Scalars['Int']['output'];
};

export type Query = {
  __typename?: 'Query';
  me?: Maybe<UserType>;
  priorityStats: Array<PriorityStatsType>;
  progressStats: ProgressStatsType;
  searchTodos: Array<SearchResultType>;
  todo?: Maybe<TodoType>;
  todos: Array<TodoType>;
  todosConnection: TodoConnection;
  user?: Maybe<UserType>;
};


export type QuerySearchTodosArgs = {
  input: TodoSearchInput;
};


export type QueryTodoArgs = {
  id: Scalars['ID']['input'];
};


export type QueryTodosConnectionArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryUserArgs = {
  id: Scalars['Int']['input'];
};

export type RateLimitError = {
  __typename?: 'RateLimitError';
  Ratelimiterror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  message: Scalars['String']['output'];
  retryAfter?: Maybe<Scalars['Int']['output']>;
};

export type RegisterInput = {
  /** メールアドレス（ログインID） */
  email: Scalars['String']['input'];
  /** 名 */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** 姓 */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /** パスワード（8文字以上） */
  password: Scalars['String']['input'];
  /** パスワード確認 */
  passwordConfirm: Scalars['String']['input'];
};

export type SearchResultType = {
  __typename?: 'SearchResultType';
  id: Scalars['Int']['output'];
  priority: PriorityEnum;
  progress: Scalars['Int']['output'];
  score: Scalars['Float']['output'];
  todoTitle: Scalars['String']['output'];
};

export type Success = {
  __typename?: 'Success';
  Success_Typename: Scalars['String']['output'];
  message: Scalars['String']['output'];
  success: Scalars['Boolean']['output'];
};

export type SuccessExternalServiceErrorInternalError = ExternalServiceError | InternalError | Success;

export type TodoConnection = {
  __typename?: 'TodoConnection';
  edges: Array<TodoEdge>;
  pageInfo: PageInfo;
  /** ユーザーのTodo総数 */
  totalCount: Scalars['Int']['output'];
};

export type TodoCreateInput = {
  /** 優先度 */
  priority?: PriorityEnum;
  /** 進捗率（0-100） */
  progress?: Scalars['Int']['input'];
  /** タスクのタイトル（1-200文字） */
  todoTitle: Scalars['String']['input'];
};

export type TodoCreateResult = AuthenticationError | CreateTodoPayload | InternalError | ValidationError;

export type TodoDeleteResult = AuthenticationError | AuthorizationError | DeleteTodoPayload | InternalError | NotFoundError;

export type TodoEdge = {
  __typename?: 'TodoEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  node: TodoType;
};

export type TodoSearchInput = {
  /** 最小類似度スコア（0.0-1.0） */
  minScore?: Scalars['Float']['input'];
  /** 検索クエリ（自然言語） */
  query: Scalars['String']['input'];
  /** 返す結果数（1-100） */
  topK?: Scalars['Int']['input'];
};

export type TodoType = Node & {
  __typename?: 'TodoType';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  priority: PriorityEnum;
  progress: Scalars['Int']['output'];
  todoTitle: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
  /** TodoのオーナーのEmailアドレス */
  userEmail: Scalars['String']['output'];
};

export type TodoUpdateInput = {
  /** 優先度 */
  priority?: InputMaybe<PriorityEnum>;
  /** 進捗率（0-100） */
  progress?: InputMaybe<Scalars['Int']['input']>;
  /** タスクのタイトル（1-200文字） */
  todoTitle?: InputMaybe<Scalars['String']['input']>;
};

export type TodoUpdateResult = AuthenticationError | AuthorizationError | InternalError | NotFoundError | UpdateTodoPayload | ValidationError;

export type UpdateTodoPayload = {
  __typename?: 'UpdateTodoPayload';
  todo: TodoType;
};

export type UserType = {
  __typename?: 'UserType';
  dateJoined: Scalars['DateTime']['output'];
  email: Scalars['String']['output'];
  firstName: Scalars['String']['output'];
  fullName: Scalars['String']['output'];
  id: Scalars['Int']['output'];
  isStaff: Scalars['Boolean']['output'];
  lastName: Scalars['String']['output'];
};

export type ValidationError = {
  __typename?: 'ValidationError';
  Validationerror_Typename: Scalars['String']['output'];
  category: ErrorCategory;
  code: Scalars['String']['output'];
  field?: Maybe<Scalars['String']['output']>;
  message: Scalars['String']['output'];
};

export type TodoFieldsFragment = { __typename?: 'TodoType', id: string, todoTitle: string, priority: PriorityEnum, progress: number, createdAt: string, updatedAt: string, userEmail: string };

export type UserFieldsFragment = { __typename?: 'UserType', id: number, email: string, firstName: string, lastName: string, isStaff: boolean, dateJoined: string };

export type CreateTodoMutationVariables = Exact<{
  input: TodoCreateInput;
}>;


export type CreateTodoMutation = { __typename?: 'Mutation', createTodo:
    | { __typename: 'AuthenticationError' }
    | { __typename: 'CreateTodoPayload', todoEdge: { __typename?: 'TodoEdge', node: { __typename?: 'TodoType', id: string, todoTitle: string, priority: PriorityEnum, progress: number, createdAt: string, updatedAt: string, userEmail: string } } }
    | { __typename: 'InternalError', message: string }
    | { __typename: 'ValidationError', message: string, field?: string | null }
   };

export type UpdateTodoMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: TodoUpdateInput;
}>;


export type UpdateTodoMutation = { __typename?: 'Mutation', updateTodo:
    | { __typename: 'AuthenticationError' }
    | { __typename: 'AuthorizationError' }
    | { __typename: 'InternalError', message: string }
    | { __typename: 'NotFoundError', message: string }
    | { __typename: 'UpdateTodoPayload', todo: { __typename?: 'TodoType', id: string, todoTitle: string, priority: PriorityEnum, progress: number, createdAt: string, updatedAt: string, userEmail: string } }
    | { __typename: 'ValidationError', message: string, field?: string | null }
   };

export type DeleteTodoMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteTodoMutation = { __typename?: 'Mutation', deleteTodo:
    | { __typename: 'AuthenticationError' }
    | { __typename: 'AuthorizationError' }
    | { __typename: 'DeleteTodoPayload', deletedTodoId: string, message: string }
    | { __typename: 'InternalError', message: string }
    | { __typename: 'NotFoundError', message: string }
   };

export type BulkIndexTodosMutationVariables = Exact<{ [key: string]: never; }>;


export type BulkIndexTodosMutation = { __typename?: 'Mutation', bulkIndexTodos:
    | { __typename: 'ExternalServiceError', message: string }
    | { __typename: 'InternalError', message: string }
    | { __typename: 'Success', message: string, success: boolean }
   };

export type RegisterMutationVariables = Exact<{
  input: RegisterInput;
}>;


export type RegisterMutation = { __typename?: 'Mutation', register:
    | { __typename: 'AuthPayload', message: string, user: { __typename?: 'UserType', id: number, email: string, firstName: string, lastName: string, isStaff: boolean, dateJoined: string } }
    | { __typename: 'ConflictError', category: ErrorCategory, message: string, conflictingField?: string | null, code: string }
    | { __typename: 'ExternalServiceError' }
    | { __typename: 'InternalError', category: ErrorCategory, message: string, code: string }
    | { __typename: 'RateLimitError' }
    | { __typename: 'ValidationError', category: ErrorCategory, message: string, field?: string | null, code: string }
   };

export type LoginMutationVariables = Exact<{
  input: LoginInput;
}>;


export type LoginMutation = { __typename?: 'Mutation', login:
    | { __typename: 'AuthPayload', message: string, user: { __typename?: 'UserType', id: number, email: string, firstName: string, lastName: string, isStaff: boolean, dateJoined: string } }
    | { __typename: 'ConflictError' }
    | { __typename: 'ExternalServiceError' }
    | { __typename: 'InternalError', category: ErrorCategory, message: string, code: string }
    | { __typename: 'RateLimitError' }
    | { __typename: 'ValidationError', category: ErrorCategory, message: string, field?: string | null, code: string }
   };

export type LogoutMutationVariables = Exact<{ [key: string]: never; }>;


export type LogoutMutation = { __typename?: 'Mutation', logout:
    | { __typename: 'AuthenticationError', category: ErrorCategory, message: string, code: string }
    | { __typename: 'InternalError', category: ErrorCategory, message: string, code: string }
    | { __typename: 'Success', message: string, success: boolean }
   };

export type GetTodosQueryVariables = Exact<{ [key: string]: never; }>;


export type GetTodosQuery = { __typename?: 'Query', todos: Array<{ __typename?: 'TodoType', id: string, todoTitle: string, priority: PriorityEnum, progress: number, createdAt: string, updatedAt: string, userEmail: string }> };

export type GetTodoQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetTodoQuery = { __typename?: 'Query', todo?: { __typename?: 'TodoType', id: string, todoTitle: string, priority: PriorityEnum, progress: number, createdAt: string, updatedAt: string, userEmail: string } | null };

export type GetTodoStatsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetTodoStatsQuery = { __typename?: 'Query', priorityStats: Array<{ __typename?: 'PriorityStatsType', priority: PriorityEnum, count: number }> };

export type GetProgressStatsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetProgressStatsQuery = { __typename?: 'Query', progressStats: { __typename?: 'ProgressStatsType', range020: number, range2140: number, range4160: number, range6180: number, range81100: number } };

export type SearchTodosQueryVariables = Exact<{
  input: TodoSearchInput;
}>;


export type SearchTodosQuery = { __typename?: 'Query', searchTodos: Array<{ __typename?: 'SearchResultType', id: number, todoTitle: string, priority: PriorityEnum, progress: number, score: number }> };

export type GetMeQueryVariables = Exact<{ [key: string]: never; }>;


export type GetMeQuery = { __typename?: 'Query', me?: { __typename?: 'UserType', id: number, email: string, firstName: string, lastName: string, isStaff: boolean, dateJoined: string } | null };
