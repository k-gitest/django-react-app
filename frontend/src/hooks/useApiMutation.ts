import { useCallback } from 'react';
import { useMutation } from 'react-relay';
import type {
  MutationParameters,
  GraphQLTaggedNode,
  UseMutationConfig,
  PayloadError
} from 'relay-runtime';
import { ApiError } from '@/errors/api-error';
import { handleMutationError } from '@/errors/error-handler';

interface ExtendedMutationConfig<TMutation extends MutationParameters>
  extends UseMutationConfig<TMutation> {
  errorContext?: string;
  showToast?: boolean;
}

export const useApiMutation = <TMutation extends MutationParameters>(
  mutation: GraphQLTaggedNode
) => {
  const [commit, isInFlight] = useMutation<TMutation>(mutation);

  const execute = useCallback(
    (config: ExtendedMutationConfig<TMutation>): Promise<TMutation['response']> => {
      const { errorContext, showToast = true, ...relayConfig } = config;

      return new Promise((resolve, reject) => {
        commit({
          ...relayConfig,
          onCompleted: (response, errors) => {
            // GraphQL実行時エラーの処理
            if (errors && errors.length > 0) {
              const graphqlErrors = convertPayloadErrorsToApiErrors(errors);
              graphqlErrors.forEach(error => {
                handleMutationError(error, {
                  context: errorContext || 'Mutation',
                  showToast
                });
              });
              return reject(graphqlErrors[0]);
            }
            // 正常終了
            relayConfig.onCompleted?.(response, errors);
            resolve(response);
          },
          onError: (error) => {
            // ネットワークエラー等の処理
            handleMutationError(error, {
              context: errorContext || 'Mutation',
              showToast
            });
            relayConfig.onError?.(error);
            reject(error);
          },
        });
      });
    },
    [commit]
  );

  return { execute, isInFlight };
};

function convertPayloadErrorsToApiErrors(errors: readonly PayloadError[]): ApiError[] {
  return errors.map(error => {
    const extensions = error.extensions;
    if (extensions?.__typename) {
      const statusMap: Record<string, number> = {
        ValidationError: 400,
        AuthenticationError: 401,
        NotFoundError: 404,
        InternalError: 500,
      };
      return new ApiError(statusMap[extensions.__typename as string] || 500, error.message, extensions);
    }
    return new ApiError(500, error.message, { code: 'graphql_error' });
  });
}