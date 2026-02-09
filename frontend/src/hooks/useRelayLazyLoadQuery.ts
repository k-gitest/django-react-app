import { useEffect, useRef } from 'react';
import { useLazyLoadQuery } from 'react-relay';
import type { OperationType, GraphQLTaggedNode, FetchPolicy } from 'relay-runtime';

interface UseRelayQueryOptions<TQuery extends OperationType> {
  fetchPolicy?: FetchPolicy;
  onSuccess?: (data: TQuery['response']) => void;
}

export const useRelayLazyLoadQuery = <TQuery extends OperationType>(
  query: GraphQLTaggedNode,
  variables: TQuery['variables'],
  options?: UseRelayQueryOptions<TQuery>
): TQuery['response'] => {
  const data = useLazyLoadQuery<TQuery>(query, variables, {
    fetchPolicy: options?.fetchPolicy || 'store-or-network',
  });

  // callbackが再生成されても副作用が暴走しないようrefで管理
  const onSuccessRef = useRef(options?.onSuccess);
  useEffect(() => {
    onSuccessRef.current = options?.onSuccess;
  }, [options?.onSuccess]);

  // データが取得・更新されたタイミングで実行
  useEffect(() => {
    if (data) {
      onSuccessRef.current?.(data);
    }
  }, [data]); // variablesが変わってdataが更新された時も発火する

  return data;
};