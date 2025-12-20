import { useApiQuery } from "@/hooks/use-tanstack-query";
import { apiClient } from "@/lib/auth-client";

type TodoStatsResponse = {
  priority: string;
  count: number;
}[];

type TodoStatsData = {
  priority: string;
  count: number;
  fill: string;
}[];

export const useTodoStats = () => {
  return useApiQuery<TodoStatsData>({
    queryKey: ['todos', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get('todos/stats/').json<TodoStatsResponse>();
      // shadcn/ui Charts が期待する形式に変換
      return response.map(item => ({
        priority: item.priority,
        count: item.count,
        fill: `var(--color-${item.priority.toLowerCase()})` // CSS変数で色を制御
      }));
    }
  });
};