import { graphql, useFragment } from 'react-relay';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { TodoProgressChart } from './TodoProgressChart';
import type { TodoProgressChartRelayContainerQuery } from '@/__generated__/TodoProgressChartRelayContainerQuery.graphql';
import type { TodoProgressChartRelayContainer_progress$key } from '@/__generated__/TodoProgressChartRelayContainer_progress.graphql'

const TodoProgressFragment = graphql`
fragment TodoProgressChartRelayContainer_progress on Query {
  progressStats {
    range020
    range2140
    range4160
    range6180
    range81100
  }
}
`

const TodoProgressQuery = graphql`
query TodoProgressChartRelayContainerQuery {
  ...TodoProgressChartRelayContainer_progress
}
`
/*
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
*/

export const TodoProgressChartRelayContainer = () => {
  //const data = useRelayLazyLoadQuery<TodoProgressChartRelayContainerQuery>(TodoProgressQuery, {});
  const queryData = useRelayLazyLoadQuery<TodoProgressChartRelayContainerQuery>(TodoProgressQuery, {});

  const data = useFragment<TodoProgressChartRelayContainer_progress$key>(TodoProgressFragment, queryData);

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