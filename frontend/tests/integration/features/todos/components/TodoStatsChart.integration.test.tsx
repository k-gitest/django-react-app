import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ComponentProps, ReactNode } from 'react';
import { TodoStatsChart } from '@/features/todos/components/TodoStatsChart';
import { useTodoStats } from '@/features/todos/hooks/useTodoStats';
import type * as RechartsPrimitive from "recharts";

// --- モック定義 ---

vi.mock('@/features/todos/hooks/useTodoStats');
const mockedUseTodoStats = vi.mocked(useTodoStats);

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof RechartsPrimitive>();
  return {
    ...actual,
    PieChart: ({ children }: { children: ReactNode }) => (
      <div data-testid="pie-chart">{children}</div>
    ),
    Pie: (props: ComponentProps<typeof RechartsPrimitive.Pie>) => {
      // ESLintエラーを回避しつつ、必要な値だけを属性に書き出す
      return (
        <div 
          data-testid="pie" 
          data-data={JSON.stringify(props.data)}
          data-datakey={String(props.dataKey ?? '')}
          data-namekey={String(props.nameKey ?? '')}
          data-innerradius={String(props.innerRadius ?? '')}
        />
      );
    },
    // shadcn/ui の ChartTooltip が内部で使用するため定義が必要
    Tooltip: () => <div data-testid="recharts-tooltip" />,
    ResponsiveContainer: ({ children }: { children: ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('TodoStatsChart', () => {
  const mockTodoData = [
    { priority: 'high', count: 5, fill: 'var(--color-high)' },
    { priority: 'medium', count: 10, fill: 'var(--color-medium)' },
    { priority: 'low', count: 15, fill: 'var(--color-low)' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('表示状態のテスト', () => {
    it('読み込み中は Loading が表示されること', () => {
      mockedUseTodoStats.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as ReturnType<typeof useTodoStats>);

      render(<TodoStatsChart />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('データ取得後、チャートとタイトルが表示されること', () => {
      mockedUseTodoStats.mockReturnValue({
        data: mockTodoData,
        isLoading: false,
      } as ReturnType<typeof useTodoStats>);

      render(<TodoStatsChart />);

      expect(screen.getByText('優先度別タスク分布')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  describe('Pie コンポーネントの設定検証', () => {
    it('Pie に正しいプロパティが渡されていること', () => {
      mockedUseTodoStats.mockReturnValue({
        data: mockTodoData,
        isLoading: false,
      } as ReturnType<typeof useTodoStats>);

      render(<TodoStatsChart />);

      const pie = screen.getByTestId('pie');
      
      // データが丸ごと渡されているか確認
      expect(pie.getAttribute('data-data')).toBe(JSON.stringify(mockTodoData));
      
      // キーとサイズの設定確認
      expect(pie.getAttribute('data-datakey')).toBe('count');
      expect(pie.getAttribute('data-namekey')).toBe('priority');
      expect(pie.getAttribute('data-innerradius')).toBe('60');
    });
  });

  describe('UI構造の検証', () => {
    it('ChartContainer が適切なクラスとスタイルを持っていること', () => {
      mockedUseTodoStats.mockReturnValue({
        data: mockTodoData,
        isLoading: false,
      } as ReturnType<typeof useTodoStats>);

      const { container } = render(<TodoStatsChart />);
      
      // mx-auto aspect-square などのクラスが適用されている要素を探す
      const chartContainer = container.querySelector('.mx-auto.aspect-square');
      expect(chartContainer).toBeInTheDocument();
      expect(chartContainer).toHaveClass('max-h-[250px]');
    });
  });
});