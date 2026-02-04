//import { useApiQuery } from "@/hooks/use-tanstack-query";
import { useApiSuspenseQuery } from "@/hooks/use-suspense-query";
import { todoService } from "../services/todo-service";

type TodoStatsData = {
  priority: string;
  count: number;
  fill: string;
}[];

//type StatsRes = Awaited<ReturnType<typeof todoService.getTodoStats>>;

/*
export const useTodoStats = () => {
  return useApiQuery<TodoStatsData>({
    queryKey: ['todos', 'stats'],
    queryFn: async () => {
      const response = await todoService.getTodoStats();
      return response.map(item => ({
        priority: item.priority,
        count: item.count,
        fill: `var(--color-${item.priority.toLowerCase()})`
      }));
    }
  });
};
*/

export const useTodoStats = () => {
  return useApiSuspenseQuery<TodoStatsData>({
    queryKey: ['todos', 'stats'],
    queryFn: async () => {
      const response = await todoService.getTodoStats();
      const safeResponse = response.data ?? [];
      return safeResponse.map(item => ({
        priority: item.priority ?? 'UNKNOWN',
        count: item.count ?? 0,
        fill: `var(--color-${(item.priority ?? 'unknown').toLowerCase()})`
      }));
    }
  });
};