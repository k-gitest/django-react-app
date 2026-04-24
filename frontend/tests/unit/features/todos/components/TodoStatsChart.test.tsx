import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoStatsChart } from '@/features/todos/components/TodoStatsChart';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('recharts', () => ({
  PieChart: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  )),
  Pie: vi.fn(({ data, dataKey, nameKey, innerRadius }: {
    data: unknown[];
    dataKey: string;
    nameKey: string;
    innerRadius: number;
  }) => (
    <div
      data-testid="pie"
      data-data-key={dataKey}
      data-name-key={nameKey}
      data-inner-radius={innerRadius}
      data-item-count={data?.length}
    />
  )),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" data-class-name={className}>{children}</div>
  ),
  CardHeader: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-header" data-class-name={className}>{children}</div>
  ),
  CardTitle: ({ children }: { children: React.ReactNode }) => (
    <h3 data-testid="card-title">{children}</h3>
  ),
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card-content" data-class-name={className}>{children}</div>
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
  ChartTooltip: vi.fn(({ cursor, content }: { cursor: boolean; content: React.ReactNode }) => (
    <div
      data-testid="chart-tooltip"
      data-cursor={cursor}
    >
      {content}
    </div>
  )),
  ChartTooltipContent: vi.fn(({ hideLabel }: { hideLabel?: boolean }) => (
    <div
      data-testid="chart-tooltip-content"
      data-hide-label={hideLabel}
    />
  )),
}));

/* =========================
   モック参照
========================= */
import { Pie, PieChart } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

const PieMock = Pie as unknown as Mock;
const PieChartMock = PieChart as unknown as Mock;
const ChartContainerMock = ChartContainer as unknown as Mock;
const ChartTooltipMock = ChartTooltip as unknown as Mock;
const ChartTooltipContentMock = ChartTooltipContent as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockData = [
  { priority: 'HIGH', count: 5, fill: 'var(--color-high)' },
  { priority: 'MEDIUM', count: 3, fill: 'var(--color-medium)' },
  { priority: 'LOW', count: 2, fill: 'var(--color-low)' },
];

/* =========================
   テスト本体
========================= */
describe('TodoStatsChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* --------------------
     レンダリング
  -------------------- */
  /*
    describe('レンダリング', () => {
      it('Cardがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('card')).toBeInTheDocument();
      });
  
      it('タイトルが "優先度別タスク分布" と表示される', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('card-title')).toHaveTextContent('優先度別タスク分布');
      });
  
      it('ChartContainerがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('chart-container')).toBeInTheDocument();
      });
  
      it('PieChartがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
      });
  
      it('Pieがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('pie')).toBeInTheDocument();
      });
  
      it('ChartTooltipがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('chart-tooltip')).toBeInTheDocument();
      });
  
      it('ChartTooltipContentがレンダリングされる', () => {
        render(<TodoStatsChart data={mockData} />);
        expect(screen.getByTestId('chart-tooltip-content')).toBeInTheDocument();
      });
    });
  */
  /* --------------------
     dataのprops受け渡し
  -------------------- */
  /*
    describe('dataのprops受け渡し', () => {
      it('PieにdataがそのまM渡される', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const pieProps = PieMock.mock.calls.at(-1)?.[0];
        expect(pieProps.data).toEqual(mockData);
      });
  
      it('Pieに渡されるdataの件数が正しい', () => {
        render(<TodoStatsChart data={mockData} />);
  
        expect(screen.getByTestId('pie')).toHaveAttribute(
          'data-item-count',
          String(mockData.length)
        );
      });
  
      it('dataが空配列のとき Pieに空配列が渡される', () => {
        render(<TodoStatsChart data={[]} />);
  
        const pieProps = PieMock.mock.calls.at(-1)?.[0];
        expect(pieProps.data).toEqual([]);
      });
  
      it('fillがnullのアイテムも受け付ける', () => {
        const dataWithNull = [{ priority: 'HIGH', count: 5, fill: null }];
        expect(() => render(<TodoStatsChart data={dataWithNull} />)).not.toThrow();
  
        const pieProps = PieMock.mock.calls.at(-1)?.[0];
        expect(pieProps.data[0].fill).toBeNull();
      });
  
      it('fillが未指定のアイテムも受け付ける', () => {
        const dataWithoutFill = [{ priority: 'HIGH', count: 5 }];
        expect(() => render(<TodoStatsChart data={dataWithoutFill} />)).not.toThrow();
      });
    });
  */
  /* --------------------
     Pieのprops
  -------------------- */
  /*
    describe('Pieへのprops', () => {
      it('dataKeyが "count" になっている', () => {
        render(<TodoStatsChart data={mockData} />);
  
        expect(screen.getByTestId('pie')).toHaveAttribute('data-data-key', 'count');
      });
  
      it('nameKeyが "priority" になっている', () => {
        render(<TodoStatsChart data={mockData} />);
  
        expect(screen.getByTestId('pie')).toHaveAttribute('data-name-key', 'priority');
      });
  
      it('innerRadiusが 60 になっている', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const pieProps = PieMock.mock.calls.at(-1)?.[0];
        expect(pieProps.innerRadius).toBe(60);
      });
    });
  */
  /* --------------------
     ChartTooltipのprops
  -------------------- */
  /*
    describe('ChartTooltipへのprops', () => {
      it('cursorがfalseになっている', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const tooltipProps = ChartTooltipMock.mock.calls.at(-1)?.[0];
        expect(tooltipProps.cursor).toBe(false);
      });
  
      it('ChartTooltipContentがcontentとして渡される', () => {
        render(<TodoStatsChart data={mockData} />);
  
        expect(ChartTooltipContentMock).toHaveBeenCalledTimes(1);
      });
  
      it('ChartTooltipContentにhideLabelが渡される', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const tooltipContentProps = ChartTooltipContentMock.mock.calls.at(-1)?.[0];
        expect(tooltipContentProps.hideLabel).toBe(true);
      });
    });
  */
  /* --------------------
     ChartContainerのconfigとclassName
  -------------------- */
  /*
    describe('ChartContainerへのprops', () => {
      it('configにcountのラベルが含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.count.label).toBe('タスク数');
      });
  
      it('configにhighのラベルと色が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.high.label).toBe('優先度: 高');
        expect(config.high.color).toBe('hsl(var(--destructive))');
      });
  
      it('configにmediumのラベルと色が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.medium.label).toBe('優先度: 中');
        expect(config.medium.color).toBe('hsl(var(--primary))');
      });
  
      it('configにlowのラベルと色が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const config = JSON.parse(
          screen.getByTestId('chart-container').getAttribute('data-config') ?? '{}'
        );
        expect(config.low.label).toBe('優先度: 低');
        expect(config.low.color).toBe('hsl(var(--muted))');
      });
  
      it('classNameに "mx-auto" が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const containerProps = ChartContainerMock.mock.calls.at(-1)?.[0];
        expect(containerProps.className).toContain('mx-auto');
      });
  
      it('classNameに "aspect-square" が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const containerProps = ChartContainerMock.mock.calls.at(-1)?.[0];
        expect(containerProps.className).toContain('aspect-square');
      });
  
      it('classNameに "max-h-[250px]" が含まれる', () => {
        render(<TodoStatsChart data={mockData} />);
  
        const containerProps = ChartContainerMock.mock.calls.at(-1)?.[0];
        expect(containerProps.className).toContain('max-h-[250px]');
      });
    });
  */
});