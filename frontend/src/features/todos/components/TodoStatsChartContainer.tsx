import { useTodoStats } from "../hooks/useTodoStats";
import { TodoStatsChart } from './TodoStatsChart';

export const TodoStatsChartContainer = () => {
  const { data } = useTodoStats();
  return <TodoStatsChart data={data ?? []} />;
};