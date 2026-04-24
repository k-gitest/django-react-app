import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoProgressChart } from '@/features/todos/components/TodoProgressChart';

/* =========================
   vi.mock（トップレベル）
========================= */

// recharts: 各コンポーネントをdata属性付きスタブに
vi.mock('recharts', () => ({
  BarChart: vi.fn(({ children, data }: { children: React.ReactNode; data: unknown[] }) => (
    <div data-testid="bar-chart" data-item-count={data?.length}>
      {children}
    </div>
  )),
  Bar: vi.fn(({ dataKey, fill, radius }: { dataKey: string; fill: string; radius: number }) => (
    <div
      data-testid="bar"
      data-data-key={dataKey}
      data-fill={fill}
      data-radius={radius}
    />
  )),
  CartesianGrid: vi.fn(({ vertical, strokeDasharray }: { vertical: boolean; strokeDasharray: string }) => (
    <div
      data-testid="cartesian-grid"
      data-vertical={vertical}
      data-stroke-dasharray={strokeDasharray}
    />
  )),
  XAxis: vi.fn(({ dataKey, tickLine, tickMargin, axisLine }: {
    dataKey: string;
    tickLine: boolean;
    tickMargin: number;
    axisLine: boolean;
  }) => (
    <div
      data-testid="x-axis"
      data-data-key={dataKey}
      data-tick-line={tickLine}
      data-tick-margin={tickMargin}
      data-axis-line={axisLine}
    />
  )),
  YAxis: vi.fn(({ tickLine, axisLine, allowDecimals }: {
    tickLine: boolean;
    axisLine: boolean;
    allowDecimals: boolean;
  }) => (
    <div
      data-testid="y-axis"
      data-tick-line={tickLine}
      data-axis-line={axisLine}
      data-allow-decimals={allowDecimals}
    />
  )),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card">{children}</div>
  ),
  CardHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-header">{children}</div>
  ),
  CardTitle: ({ children }: { children: React.ReactNode }) => (
    <h3 data-testid="card-title">{children}</h3>
  ),
  CardContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-content">{children}</div>
  ),
}));

vi.mock('@/components/ui/chart', () => ({
  ChartContainer: vi.fn(({ children, config, className }: {
    children: React.ReactNode;
    config: unknown;
    className?: string;
  }) => (
    <div
      data-testid="chart-container"
      data-config={JSON.stringify(config)}
      data-class-name={className}
    >
      {children}
    </div>
  )),
  ChartTooltip: vi.fn(() => <div data-testid="chart-tooltip" />),
  ChartTooltipContent: vi.fn(() => <div data-testid="chart-tooltip-content" />),
}));

/* =========================
   モック参照
========================= */
import { BarChart, Bar, CartesianGrid, XAxis, YAxis } from 'recharts';
import { ChartContainer } from '@/components/ui/chart';

const BarChartMock = BarChart as unknown as Mock;
const BarMock = Bar as unknown as Mock;
const CartesianGridMock = CartesianGrid as unknown as Mock;
const XAxisMock = XAxis as unknown as Mock;
const YAxisMock = YAxis as unknown as Mock;
const ChartContainerMock = ChartContainer as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockData = [
  { range: '0-20%', count: 5 },
  { range: '21-40%', count: 3 },
  { range: '41-60%', count: 7 },
  { range: '61-80%', count: 4 },
  { range: '81-100%', count: 2 },
];

/* =========================
   テスト本体
========================= */
describe('TodoProgressChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* --------------------
     レンダリング
  -------------------- */
  /*
    describe('レンダリング', () => {
      it('Cardがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('card')).toBeInTheDocument();
      });
  
      it('タイトルが "進捗分布（%）" と表示される', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('card-title')).toHaveTextContent('進捗分布（%）');
      });
  
      it('ChartContainerがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('chart-container')).toBeInTheDocument();
      });
  
      it('BarChartがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      });
  
      it('Barがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('bar')).toBeInTheDocument();
      });
  
      it('CartesianGridがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
      });
  
      it('XAxisがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('x-axis')).toBeInTheDocument();
      });
  
      it('YAxisがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('y-axis')).toBeInTheDocument();
      });
  
      it('ChartTooltipがレンダリングされる', () => {
        render(<TodoProgressChart data={mockData} />);
        expect(screen.getByTestId('chart-tooltip')).toBeInTheDocument();
      });
    });
  */
  /* --------------------
     dataのprops受け渡し
  -------------------- */
  /*
    describe('dataのprops受け渡し', () => {
      it('BarChartにdataがそのまま渡される', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const barChartProps = BarChartMock.mock.calls.at(-1)?.[0];
        expect(barChartProps.data).toEqual(mockData);
      });
  
      it('BarChartに渡されるdataの件数が正しい', () => {
        render(<TodoProgressChart data={mockData} />);
  
        expect(screen.getByTestId('bar-chart')).toHaveAttribute(
          'data-item-count',
          String(mockData.length)
        );
      });
  
      it('dataが空配列のとき BarChartに空配列が渡される', () => {
        render(<TodoProgressChart data={[]} />);
  
        const barChartProps = BarChartMock.mock.calls.at(-1)?.[0];
        expect(barChartProps.data).toEqual([]);
      });
  
      it('data=[]のとき BarChartのitem-countが0になる', () => {
        render(<TodoProgressChart data={[]} />);
  
        expect(screen.getByTestId('bar-chart')).toHaveAttribute(
          'data-item-count',
          '0'
        );
      });
  
      it('dataが1件のとき 正しく渡される', () => {
        const singleData = [{ range: '0-20%', count: 10 }];
        render(<TodoProgressChart data={singleData} />);
  
        const barChartProps = BarChartMock.mock.calls.at(-1)?.[0];
        expect(barChartProps.data).toEqual(singleData);
      });
    });
  */
  /* --------------------
     ChartContainerのconfigとclassName
  -------------------- */
  /*
    describe('ChartContainerへのprops', () => {
      it('configにcountのラベルが含まれる', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.count.label).toBe('タスク数');
      });
  
      it('configにcountのcolorが含まれる', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.count.color).toBe('hsl(var(--chart-1))');
      });
  
      it('classNameに "min-h-[200px] w-full" が含まれる', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const chartContainerProps = ChartContainerMock.mock.calls.at(-1)?.[0];
        expect(chartContainerProps.className).toContain('min-h-[200px]');
        expect(chartContainerProps.className).toContain('w-full');
      });
    });
  */
  /* --------------------
     Barのprops
  -------------------- */
  /*
    describe('Barへのprops', () => {
      it('dataKeyが "count" になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        expect(screen.getByTestId('bar')).toHaveAttribute('data-data-key', 'count');
      });
  
      it('fillが "var(--color-count)" になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        expect(screen.getByTestId('bar')).toHaveAttribute(
          'data-fill',
          'var(--color-count)'
        );
      });
  
      it('radiusが 4 になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const barProps = BarMock.mock.calls.at(-1)?.[0];
        expect(barProps.radius).toBe(4);
      });
    });
  */
  /* --------------------
     XAxisのprops
  -------------------- */
  /*
    describe('XAxisへのprops', () => {
      it('dataKeyが "range" になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        expect(screen.getByTestId('x-axis')).toHaveAttribute('data-data-key', 'range');
      });
  
      it('tickLineがfalseになっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const xAxisProps = XAxisMock.mock.calls.at(-1)?.[0];
        expect(xAxisProps.tickLine).toBe(false);
      });
  
      it('axisLineがfalseになっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const xAxisProps = XAxisMock.mock.calls.at(-1)?.[0];
        expect(xAxisProps.axisLine).toBe(false);
      });
  
      it('tickMarginが 10 になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const xAxisProps = XAxisMock.mock.calls.at(-1)?.[0];
        expect(xAxisProps.tickMargin).toBe(10);
      });
    });
  */
  /* --------------------
     YAxisのprops
  -------------------- */
  /*
    describe('YAxisへのprops', () => {
      it('tickLineがfalseになっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const yAxisProps = YAxisMock.mock.calls.at(-1)?.[0];
        expect(yAxisProps.tickLine).toBe(false);
      });
  
      it('axisLineがfalseになっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const yAxisProps = YAxisMock.mock.calls.at(-1)?.[0];
        expect(yAxisProps.axisLine).toBe(false);
      });
  
      it('allowDecimalsがfalseになっている（整数のみ表示）', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const yAxisProps = YAxisMock.mock.calls.at(-1)?.[0];
        expect(yAxisProps.allowDecimals).toBe(false);
      });
    });
  */
  /* --------------------
     CartesianGridのprops
  -------------------- */
  /*
    describe('CartesianGridへのprops', () => {
      it('verticalがfalseになっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        const gridProps = CartesianGridMock.mock.calls.at(-1)?.[0];
        expect(gridProps.vertical).toBe(false);
      });
  
      it('strokeDasharrayが "3 3" になっている', () => {
        render(<TodoProgressChart data={mockData} />);
  
        expect(screen.getByTestId('cartesian-grid')).toHaveAttribute(
          'data-stroke-dasharray',
          '3 3'
        );
      });
    });
    */
});