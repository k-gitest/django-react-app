import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/auth-client";

export const useTodoStats = () => {
  return useQuery({
    queryKey: ['todos', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get('todos/stats/').json<{priority: string, count: number}[]>();
      // shadcn/ui Charts が期待する形式に変換
      return response.map(item => ({
        priority: item.priority,
        count: item.count,
        fill: `var(--color-${item.priority.toLowerCase()})` // CSS変数で色を制御
      }));
    }
  });
};