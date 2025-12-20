import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/auth-client";

export const useProgressStats = () => {
  return useQuery({
    queryKey: ['todos', 'progress-stats'],
    queryFn: async () => {
      const res = await apiClient.get('todos/progress-stats/').json<Record<string, number>>();
      // グラフ表示用のラベルと値のペアに変換
      return [
        { range: "0-20%", count: res.range_0_20 },
        { range: "21-40%", count: res.range_21_40 },
        { range: "41-60%", count: res.range_41_60 },
        { range: "61-80%", count: res.range_61_80 },
        { range: "81-100%", count: res.range_81_100 },
      ];
    }
  });
};