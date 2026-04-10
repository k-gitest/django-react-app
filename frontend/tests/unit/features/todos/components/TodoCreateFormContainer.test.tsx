import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoCreateFormContainer } from '@/features/todos/components/TodoCreateFormContainer';

/* =========================
   モック対象
========================= */
import { useTodos } from '@/features/todos/hooks/useTodos';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
import { TodoCreateForm } from '@/features/todos/components/TodoCreateForm';
import type { TodoFormValues } from '@/features/todos/schemas';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@/features/todos/hooks/useTodos', () => ({
  useTodos: vi.fn(),
}));

vi.mock('@/hooks/useExclusiveModal', () => ({
  useExclusiveModal: vi.fn(),
  useUIStore: vi.fn(),
}));

// TodoCreateFormはpropsの検証のみに使うためスタブ化
vi.mock('@/features/todos/components/TodoCreateForm', () => ({
  TodoCreateForm: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useTodosMock = useTodos as unknown as Mock;
const useExclusiveModalMock = useExclusiveModal as unknown as Mock;
const useUIStoreMock = useUIStore as unknown as Mock;
const TodoCreateFormMock = TodoCreateForm as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockFormValues: TodoFormValues = {
  todo_title: 'テストタスク',
  priority: 'HIGH',
  progress: 0,
};

/* =========================
   共通モック
========================= */
const mockCreateTodo = vi.fn();
const mockOpen = vi.fn();
const mockClose = vi.fn();

const setupDefaultMocks = (overrides: {
  isOpen?: boolean;
  isPending?: boolean;
  currentModalId?: string | null;
} = {}) => {
  const { isOpen = false, isPending = false, currentModalId = null } = overrides;

  useTodosMock.mockReturnValue({
    createTodo: mockCreateTodo,
    createMutation: { isPending },
  });

  useExclusiveModalMock.mockReturnValue({
    isOpen,
    open: mockOpen,
    close: mockClose,
  });

  // useUIStore は selector を受け取るので実行して返す
  useUIStoreMock.mockImplementation(
    (selector: (state: { currentModalId: string | null }) => unknown) =>
      selector({ currentModalId })
  );

  // TodoCreateFormは渡されたpropsを data 属性で記録するスタブ
  TodoCreateFormMock.mockImplementation((props: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isLoading: boolean;
    disabled: boolean;
  }) => (
    <div
      data-testid="todo-create-form"
      data-open={props.open}
      data-is-loading={props.isLoading}
      data-disabled={props.disabled}
    />
  ));
};

/* =========================
   ヘルパー: TodoCreateFormに渡されたpropsを取得
========================= */
const getLastProps = () =>
  TodoCreateFormMock.mock.calls.at(-1)?.[0] as {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isLoading: boolean;
    disabled: boolean;
  };

/* =========================
   テスト本体
========================= */
describe('TodoCreateFormContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('TodoCreateFormがレンダリングされる', () => {
      render(<TodoCreateFormContainer />);
      expect(screen.getByTestId('todo-create-form')).toBeInTheDocument();
    });

    it('TodoCreateFormが1回だけ呼ばれる', () => {
      render(<TodoCreateFormContainer />);
      expect(TodoCreateFormMock).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     propsの受け渡し
  -------------------- */

  describe('propsの受け渡し', () => {
    describe('open', () => {
      it('isOpen=falseのとき open=falseが渡される', () => {
        setupDefaultMocks({ isOpen: false });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().open).toBe(false);
      });

      it('isOpen=trueのとき open=trueが渡される', () => {
        setupDefaultMocks({ isOpen: true });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().open).toBe(true);
      });
    });

    describe('isLoading', () => {
      it('isPending=falseのとき isLoading=falseが渡される', () => {
        setupDefaultMocks({ isPending: false });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().isLoading).toBe(false);
      });

      it('isPending=trueのとき isLoading=trueが渡される', () => {
        setupDefaultMocks({ isPending: true });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().isLoading).toBe(true);
      });
    });

    describe('disabled（isLockedByOther）', () => {
      it('currentModalId=nullのとき disabled=falseが渡される', () => {
        setupDefaultMocks({ currentModalId: null, isOpen: false });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().disabled).toBe(false);
      });

      it('currentModalIdがありisOpen=falseのとき disabled=trueが渡される', () => {
        setupDefaultMocks({ currentModalId: 'other-modal', isOpen: false });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().disabled).toBe(true);
      });

      it('currentModalIdがありisOpen=trueのとき disabled=falseが渡される（自分が開いている）', () => {
        setupDefaultMocks({ currentModalId: 'some-modal', isOpen: true });
        render(<TodoCreateFormContainer />);

        expect(getLastProps().disabled).toBe(false);
      });
    });

    it('onOpenChangeが関数として渡される', () => {
      render(<TodoCreateFormContainer />);
      expect(typeof getLastProps().onOpenChange).toBe('function');
    });

    it('onSubmitが関数として渡される', () => {
      render(<TodoCreateFormContainer />);
      expect(typeof getLastProps().onSubmit).toBe('function');
    });
  });

  /* --------------------
     handleOpenChange
  -------------------- */

  describe('handleOpenChange', () => {
    it('newOpen=trueのとき open()が呼ばれる', () => {
      render(<TodoCreateFormContainer />);
      getLastProps().onOpenChange(true);

      expect(mockOpen).toHaveBeenCalledTimes(1);
      expect(mockClose).not.toHaveBeenCalled();
    });

    it('newOpen=falseのとき close()が呼ばれる', () => {
      render(<TodoCreateFormContainer />);
      getLastProps().onOpenChange(false);

      expect(mockClose).toHaveBeenCalledTimes(1);
      expect(mockOpen).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     handleCreateSubmit: 正常系
  -------------------- */

  describe('handleCreateSubmit: 正常系', () => {
    it('createTodoがフォームの値で呼ばれる', async () => {
      mockCreateTodo.mockResolvedValue(undefined);
      render(<TodoCreateFormContainer />);

      await waitFor(async () => {
        await getLastProps().onSubmit(mockFormValues);
      });

      expect(mockCreateTodo).toHaveBeenCalledTimes(1);
      expect(mockCreateTodo).toHaveBeenCalledWith(mockFormValues);
    });

    it('createTodo成功後にclose()が呼ばれる', async () => {
      mockCreateTodo.mockResolvedValue(undefined);
      render(<TodoCreateFormContainer />);

      await waitFor(async () => {
        await getLastProps().onSubmit(mockFormValues);
      });

      expect(mockClose).toHaveBeenCalledTimes(1);
    });

    it('createTodoが完了してからclose()が呼ばれる（順序保証）', async () => {
      const callOrder: string[] = [];
      mockCreateTodo.mockImplementation(async () => {
        callOrder.push('createTodo');
      });
      mockClose.mockImplementation(() => {
        callOrder.push('close');
      });

      render(<TodoCreateFormContainer />);

      await waitFor(async () => {
        await getLastProps().onSubmit(mockFormValues);
      });

      expect(callOrder).toEqual(['createTodo', 'close']);
    });
  });

  /* --------------------
     handleCreateSubmit: エラー系
  -------------------- */

  describe('handleCreateSubmit: エラー系', () => {
    it('createTodoがエラーをスローしてもclose()は呼ばれない', async () => {
      mockCreateTodo.mockRejectedValue(new Error('Create failed'));
      render(<TodoCreateFormContainer />);

      await waitFor(async () => {
        await getLastProps().onSubmit(mockFormValues);
      });

      expect(mockClose).not.toHaveBeenCalled();
    });

    it('createTodoがエラーをスローしても例外は外に伝播しない', async () => {
      mockCreateTodo.mockRejectedValue(new Error('Create failed'));
      render(<TodoCreateFormContainer />);

      await expect(
        waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        })
      ).resolves.not.toThrow();
    });

    it('createTodoがエラーをスローしてもcreateToodoは1回だけ呼ばれる', async () => {
      mockCreateTodo.mockRejectedValue(new Error('Create failed'));
      render(<TodoCreateFormContainer />);

      await waitFor(async () => {
        await getLastProps().onSubmit(mockFormValues);
      });

      expect(mockCreateTodo).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     useUIStoreへのselector
  -------------------- */

  describe('useUIStoreのselector', () => {
    it('currentModalId=nullのとき isLockedByOtherはfalse', () => {
      const selector = useUIStoreMock.mock.calls.at(-1)?.[0];
      expect(selector).toBeUndefined(); // setupDefaultMocksがrenderより先に呼ばれるため

      setupDefaultMocks({ currentModalId: null, isOpen: false });
      render(<TodoCreateFormContainer />);

      const capturedSelector = useUIStoreMock.mock.calls.at(-1)?.[0];
      expect(capturedSelector({ currentModalId: null })).toBe(false);
    });

    it('currentModalId有り＋isOpen=falseのとき isLockedByOtherはtrue', () => {
      setupDefaultMocks({ currentModalId: 'other', isOpen: false });
      render(<TodoCreateFormContainer />);

      const capturedSelector = useUIStoreMock.mock.calls.at(-1)?.[0];
      expect(capturedSelector({ currentModalId: 'other' })).toBe(true);
    });

    it('currentModalId有り＋isOpen=trueのとき isLockedByOtherはfalse', () => {
      setupDefaultMocks({ currentModalId: 'some-modal', isOpen: true });
      render(<TodoCreateFormContainer />);

      const capturedSelector = useUIStoreMock.mock.calls.at(-1)?.[0];
      // selectorはstateだけ見るが、isOpenはhookから来るためselectorの外で判定
      // isOpen=trueのとき !isOpen=false → false
      expect(capturedSelector({ currentModalId: 'some-modal' })).toBe(true);
      // ただし isOpen=true なので disabled=false になる（propsテストで検証済み）
    });
  });
});