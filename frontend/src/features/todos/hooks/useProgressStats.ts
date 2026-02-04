//import { useApiQuery } from "@/hooks/use-tanstack-query";
import { todoService } from "../services/todo-service";
import { useApiSuspenseQuery } from "@/hooks/use-suspense-query";

type ProgressStatsData = {
  range: string;
  count: number;
}[];

/*
export const useProgressStats = () => {
  return useApiQuery<ProgressStatsData>({
    queryKey: ['todos', 'progress-stats'],
    queryFn: async () => {
      const res = await todoService.getProgressStats();
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
*/

export const useProgressStats = () => {
  return useApiSuspenseQuery<ProgressStatsData>({
    queryKey: ['todos', 'progress-stats'],
    queryFn: async () => {
      const { data } = await todoService.getProgressStats();
      
      return [
        { range: "0-20%", count: data?.range_0_20 ?? 0 },
        { range: "21-40%", count: data?.range_21_40 ?? 0 },
        { range: "41-60%", count: data?.range_41_60 ?? 0 },
        { range: "61-80%", count: data?.range_61_80 ?? 0 },
        { range: "81-100%", count: data?.range_81_100 ?? 0 },
      ];
    }
  });
};