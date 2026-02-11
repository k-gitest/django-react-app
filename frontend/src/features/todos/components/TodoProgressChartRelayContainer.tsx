import { graphql } from 'react-relay';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { TodoProgressChart } from './TodoProgressChart';
import type { TodoProgressChartRelayContainerQuery } from '@/__generated__/TodoProgressChartRelayContainerQuery.graphql';

const TodoProgressQuery = graphql`
  query TodoProgressChartRelayContainerQuery {
    progressStats {
      range020
      range2140
      range4160
      range6180
      range81100
    }
  }
`;

export const TodoProgressChartRelayContainer = () => {
  const data = useRelayLazyLoadQuery<TodoProgressChartRelayContainerQuery>(TodoProgressQuery, {});
	const stats = data?.progressStats;
  // 1つのオブジェクトを、配列形式に変換する
  // これを行うことで「lengthがない」というエラーが消え、同時に「readonly」も外れます
  const chartData = stats ? [
    { range: '0-20', count: stats.range020 },
    { range: '21-40', count: stats.range2140 },
    { range: '41-60', count: stats.range4160 },
    { range: '61-80', count: stats.range6180 },
    { range: '81-100', count: stats.range81100 },
  ] : [];

  // 取得したデータをそのまま View へ
  return <TodoProgressChart data={chartData} />;
};