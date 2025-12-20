import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { useProgressStats } from "../hooks/useProgressStats";

const chartConfig = {
  count: { label: "タスク数", color: "hsl(var(--chart-1))" },
} satisfies ChartConfig;

export const TodoProgressChart = () => {
  const { data, isLoading } = useProgressStats();

  if (isLoading || !data) return <div className="h-[200px] flex items-center justify-center">Loading...</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>進捗分布（%）</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
          <BarChart data={data}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="range" tickLine={false} tickMargin={10} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} allowDecimals={false} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="count" fill="var(--color-count)" radius={4} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};