import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoList } from '@/features/todos/components/TodoList';

/* =========================
   モック対象
========================= */
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { TodoItemRelayContainer } from '@/features/todos/components/TodoItemRelayContainer';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  graphql: vi.fn(() => ({})),
}));

vi.mock('@/hooks/useRelayLazyLoadQuery', () => ({
  useRelayLazyLoadQuery: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoItemRelayContainer', () => ({
  TodoItemRelayContainer: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useRelayLazyLoadQueryMock = useRelayLazyLoadQuery as unknown as Mock;
const TodoItemRelayContainerMock = TodoItemRelayContainer as unknown as Mock;

/* =========================
   ダミーデータ
========================= */

// edge.node の最小スタブ（fragment ref として扱われる）
const makeEdge = (id: string, title: string = `タスク${id}`) => ({
  node: {
    id,
    todoTitle: title,
    // fragment ref として TodoItemRelayContainer に渡される
    __fragmentRefs: {},
  },
});

const makeQueryResponse = (overrides: {
  edges?: ReturnType<typeof makeEdge>[];
  totalCount?: number;
  hasNextPage?: boolean;
  endCursor?: string | null;
} = {}) => ({
  todosConnection: {
    edges: overrides.edges ?? [
      makeEdge('1'),
      makeEdge('2'),
      makeEdge('3'),
    ],
    pageInfo: {
      hasNextPage: overrides.hasNextPage ?? false,
      endCursor: overrides.endCursor ?? null,
    },
    totalCount: overrides.totalCount ?? 3,
  },
});

/* =========================
   セットアップヘルパー
========================= */
const setupDefaultMocks = (
  queryResponse = makeQueryResponse()
) => {
  useRelayLazyLoadQueryMock.mockReturnValue(queryResponse);

  TodoItemRelayContainerMock.mockImplementation((props: {
    todoRef: { id: string };
    showActions?: boolean;
  }) => (
    <div
      data-testid={`todo-item-relay-container-${props.todoRef.id}`}
      data-id={props.todoRef.id}
      data-show-actions={props.showActions}
    />
  ));
};

/* =========================
   ヘルパー
========================= */
const getAllTodoItemRelayContainerProps = () =>
  TodoItemRelayContainerMock.mock.calls.map((call) => call[0] as {
    todoRef: { id: string };
    showActions?: boolean;
  });

/* =========================
   テスト本体
========================= */
describe('TodoList（Relay版）', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /* --------------------
     useRelayLazyLoadQueryの呼び出し
  -------------------- */

  describe('useRelayLazyLoadQueryの呼び出し', () => {
    it('first=100でクエリが呼ばれる', () => {
      render(<TodoList />);

      expect(useRelayLazyLoadQueryMock).toHaveBeenCalledWith(
        expect.anything(),
        { first: 100 }
      );
    });

    it('useRelayLazyLoadQueryが1回だけ呼ばれる', () => {
      render(<TodoList />);

      expect(useRelayLazyLoadQueryMock).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     空タスク表示
  -------------------- */

  describe('空タスク表示', () => {
    it('edgesが空配列のとき 空メッセージが表示される', () => {
      setupDefaultMocks(makeQueryResponse({ edges: [], totalCount: 0 }));
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('空のとき TodoItemRelayContainerはレンダリングされない', () => {
      setupDefaultMocks(makeQueryResponse({ edges: [], totalCount: 0 }));
      render(<TodoList />);

      expect(
        screen.queryByTestId(/^todo-item-relay-container-/)
      ).not.toBeInTheDocument();
    });

    it('todosConnectionがnullのとき 空メッセージが表示される', () => {
      useRelayLazyLoadQueryMock.mockReturnValue({ todosConnection: null });
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('todosConnectionがundefinedのとき 空メッセージが表示される', () => {
      useRelayLazyLoadQueryMock.mockReturnValue({ todosConnection: undefined });
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('空のとき ヘッダー（タスク一覧・totalCount）は表示されない', () => {
      setupDefaultMocks(makeQueryResponse({ edges: [], totalCount: 0 }));
      render(<TodoList />);

      expect(screen.queryByText('タスク一覧')).not.toBeInTheDocument();
    });
  });

  /* --------------------
     ヘッダー表示
  -------------------- */

  describe('ヘッダー表示', () => {
    it('"タスク一覧"が表示される', () => {
      render(<TodoList />);

      expect(screen.getByText('タスク一覧')).toBeInTheDocument();
    });

    it('totalCountが "全N件" の形式で表示される', () => {
      setupDefaultMocks(makeQueryResponse({ totalCount: 5 }));
      render(<TodoList />);

      expect(screen.getByText('全5件')).toBeInTheDocument();
    });

    it('totalCount=0のとき "全0件" と表示される', () => {
      // edges があって totalCount だけ 0 のケース（データ不整合）
      setupDefaultMocks(makeQueryResponse({ totalCount: 0 }));
      render(<TodoList />);

      // edges が空ではないので一覧表示になる
      expect(screen.getByText('全0件')).toBeInTheDocument();
    });

    it('todosConnectionのtotalCountがnullのとき "全0件" と表示される', () => {
      useRelayLazyLoadQueryMock.mockReturnValue({
        todosConnection: {
          edges: [makeEdge('1')],
          pageInfo: { hasNextPage: false, endCursor: null },
          totalCount: null,
        },
      });
      render(<TodoList />);

      expect(screen.getByText('全0件')).toBeInTheDocument();
    });
  });

  /* --------------------
     TodoItemRelayContainerのレンダリング
  -------------------- */

  describe('TodoItemRelayContainerのレンダリング', () => {
    it('edges数だけTodoItemRelayContainerがレンダリングされる', () => {
      render(<TodoList />);

      expect(
        screen.getAllByTestId(/^todo-item-relay-container-/)
      ).toHaveLength(3);
    });

    it('各TodoItemRelayContainerにtodoRefが渡される', () => {
      render(<TodoList />);

      const allProps = getAllTodoItemRelayContainerProps();
      expect(allProps[0].todoRef).toEqual(expect.objectContaining({ id: '1' }));
      expect(allProps[1].todoRef).toEqual(expect.objectContaining({ id: '2' }));
      expect(allProps[2].todoRef).toEqual(expect.objectContaining({ id: '3' }));
    });

    it('todoRef は edge.node がそのまま渡される', () => {
      render(<TodoList />);

      const allProps = getAllTodoItemRelayContainerProps();
      const edges = makeQueryResponse().todosConnection.edges;
      expect(allProps[0].todoRef).toBe(edges[0].node);
    });
  });

  /* --------------------
     showActionsのprops伝達
  -------------------- */

  describe('showActionsのprops伝達', () => {
    it('showActionsが未指定のとき trueがTodoItemRelayContainerに渡される', () => {
      render(<TodoList />);

      getAllTodoItemRelayContainerProps().forEach((props) => {
        expect(props.showActions).toBe(true);
      });
    });

    it('showActions=trueのとき trueがTodoItemRelayContainerに渡される', () => {
      render(<TodoList showActions={true} />);

      getAllTodoItemRelayContainerProps().forEach((props) => {
        expect(props.showActions).toBe(true);
      });
    });

    it('showActions=falseのとき falseがTodoItemRelayContainerに渡される', () => {
      render(<TodoList showActions={false} />);

      getAllTodoItemRelayContainerProps().forEach((props) => {
        expect(props.showActions).toBe(false);
      });
    });

    it('showActions=falseでも TodoItemRelayContainerが使われる（TodoItem直接使用なし）', () => {
      render(<TodoList showActions={false} />);

      expect(TodoItemRelayContainerMock).toHaveBeenCalled();
    });
  });

  /* --------------------
     limitによる表示件数制御
  -------------------- */

  describe('limitによる表示件数制御', () => {
    it('limit=2のとき 先頭2件だけレンダリングされる', () => {
      render(<TodoList limit={2} />);

      expect(screen.getByTestId('todo-item-relay-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-relay-container-2')).toBeInTheDocument();
      expect(
        screen.queryByTestId('todo-item-relay-container-3')
      ).not.toBeInTheDocument();
    });

    it('limit=1のとき 先頭1件だけレンダリングされる', () => {
      render(<TodoList limit={1} />);

      expect(screen.getByTestId('todo-item-relay-container-1')).toBeInTheDocument();
      expect(
        screen.queryByTestId('todo-item-relay-container-2')
      ).not.toBeInTheDocument();
    });

    it('limitがedges数以上のとき 全件レンダリングされる', () => {
      render(<TodoList limit={10} />);

      expect(
        screen.getAllByTestId(/^todo-item-relay-container-/)
      ).toHaveLength(3);
    });

    it('limitが未指定のとき 全件レンダリングされる', () => {
      render(<TodoList />);

      expect(
        screen.getAllByTestId(/^todo-item-relay-container-/)
      ).toHaveLength(3);
    });

    it('showActions=falseとlimitを組み合わせた場合も正しく動作する', () => {
      render(<TodoList showActions={false} limit={2} />);

      expect(screen.getByTestId('todo-item-relay-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-relay-container-2')).toBeInTheDocument();
      expect(
        screen.queryByTestId('todo-item-relay-container-3')
      ).not.toBeInTheDocument();
      getAllTodoItemRelayContainerProps()
        .slice(0, 2)
        .forEach((props) => expect(props.showActions).toBe(false));
    });
  });
});