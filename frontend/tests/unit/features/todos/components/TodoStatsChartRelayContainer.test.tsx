import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoStatsChartRelayContainer } from '@/features/todos/components/TodoStatsChartRelayContainer';

/* =========================
   モック対象
========================= */
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { useFragment } from 'react-relay';
import { TodoStatsChart } from '@/features/todos/components/TodoStatsChart';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  graphql: vi.fn(() => ({})),
  useFragment: vi.fn(),
}));

vi.mock('@/hooks/useRelayLazyLoadQuery', () => ({
  useRelayLazyLoadQuery: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoStatsChart', () => ({
  TodoStatsChart: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useRelayLazyLoadQueryMock = useRelayLazyLoadQuery as unknown as Mock;
const useFragmentMock = useFragment as unknown as Mock;
const TodoStatsChartMock = TodoStatsChart as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockQueryData = { __fragmentRefs: {} };

const mockPriorityStats = [
  { priority: 'HIGH', count: 5 },
  { priority: 'MEDIUM', count: 3 },
  { priority: 'LOW', count: 2 },
];

const expectedChartData = [
  { priority: 'HIGH', count: 5, fill: 'var(--color-high)' },
  { priority: 'MEDIUM', count: 3, fill: 'var(--color-medium)' },
  { priority: 'LOW', count: 2, fill: 'var(--color-medium)' },
];

/* =========================
   セットアップヘルパー
========================= */
const setupDefaultMocks = (overrides: {
  priorityStats?: { priority: string | null; count: number | null }[] | null;
} = {}) => {
  const { priorityStats = mockPriorityStats } = overrides;

  useRelayLazyLoadQueryMock.mockReturnValue(mockQueryData);
  useFragmentMock.mockReturnValue(
    priorityStats !== null ? { priorityStats } : { priorityStats: null }
  );

  TodoStatsChartMock.mockImplementation((props: {
    data: { priority: string; count: number; fill: string }[];
  }) => (
    <div
      data-testid="todo-stats-chart"
      data-chart-data={JSON.stringify(props.data)}
    />
  ));
};

/* =========================
   ヘルパー
========================= */
const getChartData = (): { priority: string; count: number; fill: string }[] =>
  JSON.parse(
    screen.getByTestId('todo-stats-chart').getAttribute('data-chart-data') ?? '[]'
  );

const getLastTodoStatsChartProps = () =>
  TodoStatsChartMock.mock.calls.at(-1)?.[0] as {
    data: { priority: string; count: number; fill: string }[];
  };

/* =========================
   テスト本体
========================= */
describe('TodoStatsChartRelayContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /* --------------------
     フックの呼び出し
  -------------------- */
  /*
    describe('フックの呼び出し', () => {
      it('useRelayLazyLoadQueryが空のvariablesで呼ばれる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(useRelayLazyLoadQueryMock).toHaveBeenCalledWith(
          expect.anything(),
          {}
        );
      });
  
      it('useRelayLazyLoadQueryが1回だけ呼ばれる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(useRelayLazyLoadQueryMock).toHaveBeenCalledTimes(1);
      });
  
      it('useFragmentがqueryDataで呼ばれる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(useFragmentMock).toHaveBeenCalledWith(
          expect.anything(),
          mockQueryData
        );
      });
  
      it('useFragmentが1回だけ呼ばれる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(useFragmentMock).toHaveBeenCalledTimes(1);
      });
    });
  */
  /* --------------------
     レンダリング
  -------------------- */
  /*
    describe('レンダリング', () => {
      it('TodoStatsChartがレンダリングされる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(screen.getByTestId('todo-stats-chart')).toBeInTheDocument();
      });
  
      it('TodoStatsChartが1回だけ呼ばれる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(TodoStatsChartMock).toHaveBeenCalledTimes(1);
      });
    });
  */
  /* --------------------
     chartDataへの変換（正常系）
  -------------------- */
  /*
    describe('chartDataへの変換（正常系）', () => {
      it('priorityStatsの件数と同じ数のchartDataが渡される', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(getChartData()).toHaveLength(mockPriorityStats.length);
      });
  
      it('chartDataが期待どおりの構造で渡される', () => {
        render(<TodoStatsChartRelayContainer />);
  
        expect(getLastTodoStatsChartProps().data).toEqual(expectedChartData);
      });
  
      it('priorityとcountがそのままマッピングされる', () => {
        render(<TodoStatsChartRelayContainer />);
  
        const data = getChartData();
        expect(data[0].priority).toBe('HIGH');
        expect(data[0].count).toBe(5);
        expect(data[1].priority).toBe('MEDIUM');
        expect(data[1].count).toBe(3);
        expect(data[2].priority).toBe('LOW');
        expect(data[2].count).toBe(2);
      });
    });
  */
  /* --------------------
     fillの条件分岐
  -------------------- */
  /*
    describe('fillの条件分岐', () => {
      it('priority="HIGH"のとき fill="var(--color-high)"になる', () => {
        setupDefaultMocks({
          priorityStats: [{ priority: 'HIGH', count: 5 }],
        });
        render(<TodoStatsChartRelayContainer />);
  
        expect(getChartData()[0].fill).toBe('var(--color-high)');
      });
  
      it('priority="MEDIUM"のとき fill="var(--color-medium)"になる', () => {
        setupDefaultMocks({
          priorityStats: [{ priority: 'MEDIUM', count: 3 }],
        });
        render(<TodoStatsChartRelayContainer />);
  
        expect(getChartData()[0].fill).toBe('var(--color-medium)');
      });
  
      it('priority="LOW"のとき fill="var(--color-medium)"になる', () => {
        setupDefaultMocks({
          priorityStats: [{ priority: 'LOW', count: 2 }],
        });
        render(<TodoStatsChartRelayContainer />);
  
        expect(getChartData()[0].fill).toBe('var(--color-medium)');
      });
  
      it('priority="HIGH"以外はすべてfill="var(--color-medium)"になる', () => {
        setupDefaultMocks({
          priorityStats: [
            { priority: 'MEDIUM', count: 3 },
            { priority: 'LOW', count: 2 },
            { priority: 'UNKNOWN', count: 1 },
          ],
        });
        render(<TodoStatsChartRelayContainer />);
  
        getChartData().forEach((item) => {
          expect(item.fill).toBe('var(--color-medium)');
        });
      });
  
      it('複数のpriorityが混在しても各fillが正しい', () => {
        render(<TodoStatsChartRelayContainer />);
  
        const data = getChartData();
        expect(data.find((d) => d.priority === 'HIGH')?.fill).toBe('var(--color-high)');
        expect(data.find((d) => d.priority === 'MEDIUM')?.fill).toBe('var(--color-medium)');
        expect(data.find((d) => d.priority === 'LOW')?.fill).toBe('var(--color-medium)');
      });
    });
  */
  /* --------------------
     フォールバック処理
  -------------------- */
  /*
    describe('フォールバック処理', () => {
      describe('priorityのフォールバック', () => {
        it('priority=nullのとき "UNKNOWN"にフォールバックされる', () => {
          setupDefaultMocks({
            priorityStats: [{ priority: null, count: 1 }],
          });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()[0].priority).toBe('UNKNOWN');
        });
  
        it('priority=nullのfillは "var(--color-medium)"になる（HIGH以外扱い）', () => {
          setupDefaultMocks({
            priorityStats: [{ priority: null, count: 1 }],
          });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()[0].fill).toBe('var(--color-medium)');
        });
      });
  
      describe('countのフォールバック', () => {
        it('count=nullのとき 0にフォールバックされる', () => {
          setupDefaultMocks({
            priorityStats: [{ priority: 'HIGH', count: null }],
          });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()[0].count).toBe(0);
        });
  
        it('count=0のとき 0がそのまま渡される', () => {
          setupDefaultMocks({
            priorityStats: [{ priority: 'MEDIUM', count: 0 }],
          });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()[0].count).toBe(0);
        });
      });
  
      describe('priorityStatsのフォールバック', () => {
        it('priorityStatsがnullのとき 空配列が渡される', () => {
          setupDefaultMocks({ priorityStats: null });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()).toEqual([]);
        });
  
        it('dataがnullのとき 空配列が渡される', () => {
          useFragmentMock.mockReturnValue(null);
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()).toEqual([]);
        });
  
        it('dataがundefinedのとき 空配列が渡される', () => {
          useFragmentMock.mockReturnValue(undefined);
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()).toEqual([]);
        });
  
        it('priorityStatsが空配列のとき 空配列が渡される', () => {
          setupDefaultMocks({ priorityStats: [] });
          render(<TodoStatsChartRelayContainer />);
  
          expect(getChartData()).toEqual([]);
        });
      });
    });
    */
});