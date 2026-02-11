import { graphql } from 'react-relay';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { TodoStatsChart } from './TodoStatsChart';
import type { TodoStatsChartRelayContainerQuery } from '@/__generated__/TodoStatsChartRelayContainerQuery.graphql';

const TodoStatsQuery = graphql`
  query TodoStatsChartRelayContainerQuery {
    priorityStats {
      priority
      count
    }
  }
`;

export const TodoStatsChartRelayContainer = () => {
  const data = useRelayLazyLoadQuery<TodoStatsChartRelayContainerQuery>(TodoStatsQuery, {});

  const chartData = (data?.priorityStats ?? []).map((item) => ({
    priority: item.priority,
    count: item.count,
    // 必要ならここで fill も追加できる
    fill: item.priority === 'HIGH' ? 'var(--color-high)' : 'var(--color-medium)',
  }));

  // undefined の場合は空配列を渡す
  return <TodoStatsChart data={chartData} />;
};