import { useMemo } from 'react';
import { graphql, useFragment } from 'react-relay';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { TodoStatsChart } from './TodoStatsChart';
import type { TodoStatsChartRelayContainerQuery } from '@/__generated__/TodoStatsChartRelayContainerQuery.graphql';
import type { TodoStatsChartRelayContainer_stats$key } from '@/__generated__/TodoStatsChartRelayContainer_stats.graphql';

// Fragment定義（これ自体がドキュメントになる）
const TodoStatsFragment = graphql`
  fragment TodoStatsChartRelayContainer_stats on Query {
    priorityStats {
      priority
      count
    }
  }
`;

const TodoStatsQuery = graphql`
query TodoStatsChartRelayContainerQuery {
  ...TodoStatsChartRelayContainer_stats
}
`;

/*
const TodoStatsQuery = graphql`
  query TodoStatsChartRelayContainerQuery {
    priorityStats {
      priority
      count
    }
  }
`;
*/

export const TodoStatsChartRelayContainer = () => {
  //const data = useRelayLazyLoadQuery<TodoStatsChartRelayContainerQuery>(TodoStatsQuery, {});
  const queryData = useRelayLazyLoadQuery<TodoStatsChartRelayContainerQuery>(TodoStatsQuery, {});

  const data = useFragment<TodoStatsChartRelayContainer_stats$key>(TodoStatsFragment, queryData);

  const chartData = useMemo(() => {
    return (data?.priorityStats ?? []).map((item) => ({
      priority: item.priority ?? "UNKNOWN",
      count: item.count ?? 0,
      fill: item.priority === 'HIGH' ? 'var(--color-high)' : 'var(--color-medium)',
    }));
  }, [data]);

  // undefined の場合は空配列を渡す
  return <TodoStatsChart data={chartData} />;
};