import { useCallback } from 'react';
import { useMutation } from 'react-relay';
import type { UseMutationConfig } from 'react-relay';
import type {
  MutationParameters,
  GraphQLTaggedNode,
  //MutationConfig,
} from 'relay-runtime';
import { errorHandler } from '@/errors/error-handler';

interface ExtendedMutationConfig<TMutation extends MutationParameters>
  extends UseMutationConfig<TMutation> {
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
          //mutation: mutation,

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

