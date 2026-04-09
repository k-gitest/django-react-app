import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoCreateForm } from '@/features/todos/components/TodoCreateForm';

/* =========================
   モック対象
========================= */
import { TodoForm } from '@/features/todos/components/TodoForm';
import type { TodoFormValues } from '@/features/todos/schemas';

/* =========================
   vi.mock（トップレベル）
========================= */

// Dialog系: open/onOpenChangeの制御と子要素のレンダリングをシンプルに再現
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: {
    children: React.ReactNode;
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-testid="dialog" data-open={open}>
      {/* onOpenChangeをテストから呼べるよう隠しボタンとして露出 */}
      <button
        data-testid="dialog-close-trigger"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  ),
  DialogTrigger: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-trigger">{children}</div>
  ),
  DialogContent: ({ children }: { children: React.ReactNode }) =>
    <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) =>
    <div data-testid="dialog-header">{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) =>
    <h2 data-testid="dialog-title">{children}</h2>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, disabled, onClick }: {
    children: React.ReactNode;
    disabled?: boolean;
    onClick?: () => void;
  }) => (
    <button
      data-testid="create-button"
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  ),
}));

vi.mock('lucide-react', () => ({
  Plus: () => <span data-testid="plus-icon" />,
}));

// TodoForm: onSubmit・submitLabel・isLoadingを検証できるスタブ
vi.mock('@/features/todos/components/TodoForm', () => ({
  TodoForm: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const TodoFormMock = TodoForm as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockFormValues: TodoFormValues = {
  todo_title: 'テストタスク',
  priority: 'HIGH',
  progress: 0,
};

/* =========================
   デフォルトprops
========================= */
const defaultProps = {
  open: true,
  onOpenChange: vi.fn(),
  onSubmit: vi.fn(),
  isLoading: false,
  disabled: false,
};

/* =========================
   ヘルパー: TodoFormのonSubmitを手動トリガー
========================= */
const getTodoFormOnSubmit = (): ((values: TodoFormValues) => Promise<void>) => {
  const lastCall = TodoFormMock.mock.calls.at(-1)?.[0];
  return lastCall?.onSubmit;
};

/* =========================
   テスト本体
========================= */

describe('TodoCreateForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // TodoFormのデフォルト実装: submitLabelをdata属性で露出
    TodoFormMock.mockImplementation(({ submitLabel, isLoading }: {
      onSubmit: (v: TodoFormValues) => void;
      submitLabel: string;
      isLoading?: boolean;
    }) => (
      <div
        data-testid="todo-form"
        data-submit-label={submitLabel}
        data-is-loading={isLoading}
      />
    ));
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('Dialogがレンダリングされる', () => {
      render(<TodoCreateForm {...defaultProps} />);
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
    });

    it('新規タスク追加ボタンがレンダリングされる', () => {
      render(<TodoCreateForm {...defaultProps} />);
      expect(screen.getByTestId('create-button')).toBeInTheDocument();
      expect(screen.getByTestId('create-button')).toHaveTextContent('新規タスク追加');
    });

    it('ダイアログタイトルが「新しいタスクを作成」と表示される', () => {
      render(<TodoCreateForm {...defaultProps} />);
      expect(screen.getByTestId('dialog-title')).toHaveTextContent('新しいタスクを作成');
    });

    it('TodoFormがレンダリングされる', () => {
      render(<TodoCreateForm {...defaultProps} />);
      expect(screen.getByTestId('todo-form')).toBeInTheDocument();
    });

    it('Plusアイコンがレンダリングされる', () => {
      render(<TodoCreateForm {...defaultProps} />);
      expect(screen.getByTestId('plus-icon')).toBeInTheDocument();
    });
  });

  /* --------------------
     Dialog開閉制御
  -------------------- */

  describe('Dialog開閉制御', () => {
    it('open=trueのとき data-open属性がtrueになる', () => {
      render(<TodoCreateForm {...defaultProps} open={true} />);
      expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'true');
    });

    it('open=falseのとき data-open属性がfalseになる', () => {
      render(<TodoCreateForm {...defaultProps} open={false} />);
      expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'false');
    });

    it('onOpenChangeがDialogに渡される', async () => {
      const onOpenChange = vi.fn();
      render(<TodoCreateForm {...defaultProps} onOpenChange={onOpenChange} />);

      await userEvent.click(screen.getByTestId('dialog-close-trigger'));

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  /* --------------------
     Buttonのdisabled制御
  -------------------- */

  describe('Buttonのdisabled制御', () => {
    it('disabled=falseのとき ボタンが活性状態になる', () => {
      render(<TodoCreateForm {...defaultProps} disabled={false} />);
      expect(screen.getByTestId('create-button')).not.toBeDisabled();
    });

    it('disabled=trueのとき ボタンが非活性状態になる', () => {
      render(<TodoCreateForm {...defaultProps} disabled={true} />);
      expect(screen.getByTestId('create-button')).toBeDisabled();
    });

    it('disabledが未指定のとき ボタンが活性状態になる', () => {
      const { onOpenChange, onSubmit } = defaultProps;
      render(
        <TodoCreateForm open={true} onOpenChange={onOpenChange} onSubmit={onSubmit} />
      );
      expect(screen.getByTestId('create-button')).not.toBeDisabled();
    });
  });

  /* --------------------
     TodoFormへのprops
  -------------------- */

  describe('TodoFormへのprops', () => {
    it('isLoading=falseのとき submitLabelが「タスクを作成」になる', () => {
      render(<TodoCreateForm {...defaultProps} isLoading={false} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-submit-label',
        'タスクを作成'
      );
    });

    it('isLoading=trueのとき submitLabelが「作成中...」になる', () => {
      render(<TodoCreateForm {...defaultProps} isLoading={true} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-submit-label',
        '作成中...'
      );
    });

    it('isLoadingがTodoFormに渡される', () => {
      render(<TodoCreateForm {...defaultProps} isLoading={true} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-is-loading',
        'true'
      );
    });

    it('TodoFormにonSubmitが渡される', () => {
      render(<TodoCreateForm {...defaultProps} />);
      const onSubmit = getTodoFormOnSubmit();
      expect(typeof onSubmit).toBe('function');
    });
  });

  /* --------------------
     フォーム送信（handleSubmit）
  -------------------- */

  describe('フォーム送信（handleSubmit）', () => {
    it('onSubmitが呼ばれる', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      render(<TodoCreateForm {...defaultProps} onSubmit={onSubmit} />);

      await waitFor(async () => {
        await getTodoFormOnSubmit()(mockFormValues);
      });

      expect(onSubmit).toHaveBeenCalledTimes(1);
      expect(onSubmit).toHaveBeenCalledWith(mockFormValues);
    });

    it('onSubmit成功後にonOpenChange(false)でDialogが閉じる', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onOpenChange = vi.fn();
      render(
        <TodoCreateForm
          {...defaultProps}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
        />
      );

      await waitFor(async () => {
        await getTodoFormOnSubmit()(mockFormValues);
      });

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it('onSubmitが完了してからDialogが閉じる（順序保証）', async () => {
      const callOrder: string[] = [];
      const onSubmit = vi.fn().mockImplementation(async () => {
        callOrder.push('onSubmit');
      });
      const onOpenChange = vi.fn().mockImplementation(() => {
        callOrder.push('onOpenChange');
      });

      render(
        <TodoCreateForm
          {...defaultProps}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
        />
      );

      await waitFor(async () => {
        await getTodoFormOnSubmit()(mockFormValues);
      });

      expect(callOrder).toEqual(['onSubmit', 'onOpenChange']);
    });

    it('onSubmitが同期関数でも動作する', async () => {
      const onSubmit = vi.fn(); // 同期
      const onOpenChange = vi.fn();
      render(
        <TodoCreateForm
          {...defaultProps}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
        />
      );

      await waitFor(async () => {
        await getTodoFormOnSubmit()(mockFormValues);
      });

      expect(onSubmit).toHaveBeenCalledWith(mockFormValues);
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it('onSubmitがエラーをスローしたとき onOpenChangeは呼ばれない', async () => {
      const onSubmit = vi.fn().mockRejectedValue(new Error('Submit failed'));
      const onOpenChange = vi.fn();
      render(
        <TodoCreateForm
          {...defaultProps}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
        />
      );

      await expect(
        waitFor(async () => {
          await getTodoFormOnSubmit()(mockFormValues);
        })
      ).rejects.toThrow('Submit failed');

      expect(onOpenChange).not.toHaveBeenCalledWith(false);
    });
  });
});