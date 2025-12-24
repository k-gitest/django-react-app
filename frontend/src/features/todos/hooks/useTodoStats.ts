import { useApiQuery } from "@/hooks/use-tanstack-query";
import { todoService } from "../services/todo-service";

type TodoStatsData = {
  priority: string;
  count: number;
  fill: string;
}[];

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