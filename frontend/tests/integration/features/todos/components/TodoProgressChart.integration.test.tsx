import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ComponentProps, ReactNode } from 'react';
import { TodoProgressChart } from '@/features/todos/components/TodoProgressChart';
import { useProgressStats } from '@/features/todos/hooks/useProgressStats';
import * as RechartsPrimitive from "recharts";

// --- モック定義 ---

vi.mock('@/features/todos/hooks/useProgressStats');
const mockedUseProgressStats = vi.mocked(useProgressStats);

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof RechartsPrimitive>();
  return {
    ...actual,
    Bar: (props: ComponentProps<typeof RechartsPrimitive.Bar>) => {
      // 1. 一度 unknown を経由して Record に変換
      // 2. DOMに直接渡すとエラーになるプロパティ（object等）をあらかじめ除外
      const { ...rest } = props as unknown as { data: unknown; [key: string]: unknown };
      return <div data-testid="bar" {...rest} />;
    },
    BarChart: (props: ComponentProps<typeof RechartsPrimitive.BarChart>) => {
      const { data, children } = props;
      return (
        <div data-testid="bar-chart" data-data={JSON.stringify(data)}>
          {children}
        </div>
      );
    },
    XAxis: (props: ComponentProps<typeof RechartsPrimitive.XAxis>) => {
      // booleanを文字列に変換して検証可能にする
      return (
        <div 
          data-testid="x-axis" 
          data-datakey={String(props.dataKey)}
          data-tickline={String(props.tickLine)}
          data-axisline={String(props.axisLine)}
        />
      );
    },
    YAxis: (props: ComponentProps<typeof RechartsPrimitive.YAxis>) => {
      return (
        <div 
          data-testid="y-axis" 
          data-tickline={String(props.tickLine)}
          data-axisline={String(props.axisLine)}
          data-allowdecimals={String(props.allowDecimals)}
        />
      );
    },
    CartesianGrid: (props: ComponentProps<typeof RechartsPrimitive.CartesianGrid>) => {
      const { vertical, strokeDasharray } = props as unknown as Record<string, unknown>;
      return <div data-testid="cartesian-grid" data-vertical={String(vertical)} data-strokedasharray={String(strokeDasharray)} />;
    },
    ResponsiveContainer: ({ children }: { children: ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

describe('TodoProgressChart', () => {
  const mockProgressData = [
    { range: '0-20%', count: 5 },
    { range: '21-40%', count: 3 },
    { range: '41-60%', count: 7 },
    { range: '61-80%', count: 4 },
    { range: '81-100%', count: 2 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ローディング状態', () => {
    it('ローディング中は"Loading..."が表示される', () => {
      mockedUseProgressStats.mockReturnValue({
        data: undefined,
        isLoading: true,
        // 必要に応じて他の TanStack Query の戻り値を定義
      } as ReturnType<typeof useProgressStats>);

      render(<TodoProgressChart />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('データ表示', () => {
    it('進捗データが正常に表示される', () => {
      mockedUseProgressStats.mockReturnValue({
        data: mockProgressData,
        isLoading: false,
      } as ReturnType<typeof useProgressStats>);

      render(<TodoProgressChart />);

      expect(screen.getByText('進捗分布（%）')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      
      // データが正しく渡されているか、属性から検証
      const barChart = screen.getByTestId('bar-chart');
      expect(barChart.getAttribute('data-data')).toBe(JSON.stringify(mockProgressData));
    });
  });

  describe('グラフの設定検証', () => {
    beforeEach(() => {
      mockedUseProgressStats.mockReturnValue({
        data: mockProgressData,
        isLoading: false,
      } as ReturnType<typeof useProgressStats>);
    });

    it('XAxisに正しいプロパティが渡されている', () => {
        render(<TodoProgressChart />);
        const xAxis = screen.getByTestId('x-axis');
        
        expect(xAxis.getAttribute('data-datakey')).toBe('range');
        expect(xAxis.getAttribute('data-tickline')).toBe('false');
        expect(xAxis.getAttribute('data-axisline')).toBe('false');
    });

    it('YAxisが正しく設定されている', () => {
        render(<TodoProgressChart />);
        const yAxis = screen.getByTestId('y-axis');

        expect(yAxis.getAttribute('data-tickline')).toBe('false');
        expect(yAxis.getAttribute('data-axisline')).toBe('false');
        expect(yAxis.getAttribute('data-allowdecimals')).toBe('false');
    });

    it('Barに正しいプロパティが渡されている', () => {
      render(<TodoProgressChart />);
      const bar = screen.getByTestId('bar');
      
      expect(bar.getAttribute('dataKey')).toBe('count');
      expect(bar.getAttribute('fill')).toBe('var(--color-count)');
      expect(bar.getAttribute('radius')).toBe('4');
    });
  });

  describe('UI構造の検証', () => {
    it('ChartContainerに適切なスタイルクラスが適用されている', () => {
      mockedUseProgressStats.mockReturnValue({
        data: mockProgressData,
        isLoading: false,
      } as ReturnType<typeof useProgressStats>);

      const { container } = render(<TodoProgressChart />);
      
      // class名の検証
      const containerElement = container.querySelector('.min-h-\\[200px\\]');
      expect(containerElement).toHaveClass('w-full');
    });
  });
});