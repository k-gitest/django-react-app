import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoProgressChartRelayContainer } from '@/features/todos/components/TodoProgressChartRelayContainer';

/* =========================
   モック対象
========================= */
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { useFragment } from 'react-relay';
import { TodoProgressChart } from '@/features/todos/components/TodoProgressChart';

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

vi.mock('@/features/todos/components/TodoProgressChart', () => ({
  TodoProgressChart: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useRelayLazyLoadQueryMock = useRelayLazyLoadQuery as unknown as Mock;
const useFragmentMock = useFragment as unknown as Mock;
const TodoProgressChartMock = TodoProgressChart as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockQueryData = { __fragmentRefs: {} };

const mockStats = {
  range020: 5,
  range2140: 3,
  range4160: 7,
  range6180: 4,
  range81100: 2,
};

const expectedChartData = [
  { range: '0-20', count: 5 },
  { range: '21-40', count: 3 },
  { range: '41-60', count: 7 },
  { range: '61-80', count: 4 },
  { range: '81-100', count: 2 },
];

/* =========================
   セットアップヘルパー
========================= */
const setupDefaultMocks = (overrides: {
  stats?: typeof mockStats | null;
} = {}) => {
  const { stats = mockStats } = overrides;

  useRelayLazyLoadQueryMock.mockReturnValue(mockQueryData);
  useFragmentMock.mockReturnValue(
    stats !== null ? { progressStats: stats } : { progressStats: null }
  );

  TodoProgressChartMock.mockImplementation((props: {
    data: { range: string; count: number }[];
  }) => (
    <div
      data-testid="todo-progress-chart"
      data-chart-data={JSON.stringify(props.data)}
    />
  ));
};

/* =========================
   ヘルパー
========================= */
const getChartData = (): { range: string; count: number }[] =>
  JSON.parse(
    screen.getByTestId('todo-progress-chart').getAttribute('data-chart-data') ?? '[]'
  );

const getLastTodoProgressChartProps = () =>
  TodoProgressChartMock.mock.calls.at(-1)?.[0] as {
    data: { range: string; count: number }[];
  };

/* =========================
   テスト本体
========================= */
describe('TodoProgressChartRelayContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /* --------------------
     フックの呼び出し
  -------------------- */

  describe('フックの呼び出し', () => {
    it('useRelayLazyLoadQueryが空のvariablesで呼ばれる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(useRelayLazyLoadQueryMock).toHaveBeenCalledWith(
        expect.anything(),
        {}
      );
    });

    it('useRelayLazyLoadQueryが1回だけ呼ばれる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(useRelayLazyLoadQueryMock).toHaveBeenCalledTimes(1);
    });

    it('useFragmentがqueryDataで呼ばれる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(useFragmentMock).toHaveBeenCalledWith(
        expect.anything(),
        mockQueryData
      );
    });

    it('useFragmentが1回だけ呼ばれる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(useFragmentMock).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('TodoProgressChartがレンダリングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(screen.getByTestId('todo-progress-chart')).toBeInTheDocument();
    });

    it('TodoProgressChartが1回だけ呼ばれる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(TodoProgressChartMock).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     chartDataへの変換（正常系）
  -------------------- */

  describe('chartDataへの変換（正常系）', () => {
    it('statsが存在するとき 5件のchartDataが渡される', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()).toHaveLength(5);
    });

    it('chartDataが期待どおりの構造で渡される', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getLastTodoProgressChartProps().data).toEqual(expectedChartData);
    });

    it('range020が "0-20" にマッピングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()[0]).toEqual({ range: '0-20', count: 5 });
    });

    it('range2140が "21-40" にマッピングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()[1]).toEqual({ range: '21-40', count: 3 });
    });

    it('range4160が "41-60" にマッピングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()[2]).toEqual({ range: '41-60', count: 7 });
    });

    it('range6180が "61-80" にマッピングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()[3]).toEqual({ range: '61-80', count: 4 });
    });

    it('range81100が "81-100" にマッピングされる', () => {
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()[4]).toEqual({ range: '81-100', count: 2 });
    });

    it('配列の順序が 0-20 → 21-40 → 41-60 → 61-80 → 81-100 の順になっている', () => {
      render(<TodoProgressChartRelayContainer />);

      const ranges = getChartData().map((d) => d.range);
      expect(ranges).toEqual(['0-20', '21-40', '41-60', '61-80', '81-100']);
    });

    it('各countがstatsの値と一致する', () => {
      render(<TodoProgressChartRelayContainer />);

      const data = getChartData();
      expect(data[0].count).toBe(mockStats.range020);
      expect(data[1].count).toBe(mockStats.range2140);
      expect(data[2].count).toBe(mockStats.range4160);
      expect(data[3].count).toBe(mockStats.range6180);
      expect(data[4].count).toBe(mockStats.range81100);
    });
  });

  /* --------------------
     chartDataへの変換（エッジケース）
  -------------------- */

  describe('chartDataへの変換（エッジケース）', () => {
    it('statsがnullのとき 空配列が渡される', () => {
      setupDefaultMocks({ stats: null });
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()).toEqual([]);
    });

    it('progressStatsがnullのとき 空配列が渡される', () => {
      useFragmentMock.mockReturnValue({ progressStats: null });
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()).toEqual([]);
    });

    it('dataがnullのとき 空配列が渡される', () => {
      useFragmentMock.mockReturnValue(null);
      render(<TodoProgressChartRelayContainer />);

      expect(getChartData()).toEqual([]);
    });

    it('全countが0のとき 0が正しく渡される', () => {
      setupDefaultMocks({
        stats: {
          range020: 0,
          range2140: 0,
          range4160: 0,
          range6180: 0,
          range81100: 0,
        },
      });
      render(<TodoProgressChartRelayContainer />);

      getChartData().forEach((item) => {
        expect(item.count).toBe(0);
      });
    });

    it('大きな数値も正しく変換される', () => {
      setupDefaultMocks({
        stats: {
          range020: 1000,
          range2140: 500,
          range4160: 250,
          range6180: 100,
          range81100: 50,
        },
      });
      render(<TodoProgressChartRelayContainer />);

      const data = getChartData();
      expect(data[0].count).toBe(1000);
      expect(data[4].count).toBe(50);
    });
  });
});