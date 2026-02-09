import { useCallback } from 'react';
import { useMutation } from 'react-relay';
import type {
  MutationParameters,
  GraphQLTaggedNode,
  MutationConfig,
  //PayloadError
} from 'relay-runtime';
//import { ApiError } from '@/errors/api-error';
import { errorHandler } from '@/errors/error-handler';

interface ExtendedMutationConfig<TMutation extends MutationParameters>
  extends MutationConfig<TMutation> {
  errorContext?: string;
  showToast?: boolean;
}

export const useRelayMutation = <TMutation extends MutationParameters>(
  mutation: GraphQLTaggedNode
) => {
  const [commit, isInFlight] = useMutation<TMutation>(mutation);

  const execute = useCallback(
    (config: ExtendedMutationConfig<TMutation>): Promise<TMutation['response']> => {
      const { errorContext, ...relayConfig } = config;

      return new Promise((resolve, reject) => {
        commit({
          ...relayConfig,
          // nullをundefinedに変換して型不整合を解消
          uploadables: relayConfig.uploadables ?? undefined,

          onCompleted: (response, errors) => {
            // fetchRelayでエラー時にthrowしているため、ここに来る時は基本成功
            // relayConfig (呼び出し元) が万が一 errors を見たがっている場合に備えて渡すだけ
            relayConfig.onCompleted?.(response, errors);
            resolve(response);
          },
          onError: (error) => {
            // すでに fetchRelay で整形済みなので、そのまま投げるだけ
            errorHandler(error, errorContext || 'Mutation');
            // 個別のコールバックがあれば実行（基本的には空でOK）
            relayConfig.onError?.(error);
            // コンポーネント側の try-catch に制御を戻す
            reject(error);
          },
        });
      });
    },
    [commit]
  );

  return { execute, isInFlight };
};

/*
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
*/