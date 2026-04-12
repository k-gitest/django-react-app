import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoEditModal } from '@/features/todos/components/TodoEditModal';

/* =========================
   モック対象
========================= */
import { TodoForm } from '@/features/todos/components/TodoForm';
import type { TodoFormValues } from '@/features/todos/schemas';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: {
    children: React.ReactNode;
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-testid="dialog" data-open={open}>
      <button
        data-testid="dialog-close-trigger"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  ),
  DialogContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-content">{children}</div>
  ),
  DialogHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-header">{children}</div>
  ),
  DialogTitle: ({ children }: { children: React.ReactNode }) => (
    <h2 data-testid="dialog-title">{children}</h2>
  ),
}));

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
const defaultProps = {
  id: 1,
  title: 'テストタスク',
  priority: 'HIGH' as const,
  progress: 50,
  open: true,
  onOpenChange: vi.fn(),
  onSubmit: vi.fn(),
  isSubmitting: false,
};

const mockFormValues: TodoFormValues = {
  todo_title: 'テストタスク',
  priority: 'HIGH',
  progress: 50,
};

/* =========================
   ヘルパー
========================= */
const getLastTodoFormProps = () =>
  TodoFormMock.mock.calls.at(-1)?.[0] as {
    defaultValues: { todo_title: string; priority: string; progress: number };
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isLoading?: boolean;
    submitLabel: string;
  };

/* =========================
   テスト本体
========================= */
describe('TodoEditModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    TodoFormMock.mockImplementation(({ submitLabel, isLoading, defaultValues }: {
      defaultValues: { todo_title: string; priority: string; progress: number };
      onSubmit: (v: TodoFormValues) => void;
      submitLabel: string;
      isLoading?: boolean;
    }) => (
      <div
        data-testid="todo-form"
        data-submit-label={submitLabel}
        data-is-loading={isLoading}
        data-default-title={defaultValues?.todo_title}
        data-default-priority={defaultValues?.priority}
        data-default-progress={defaultValues?.progress}
      />
    ));
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('Dialogがレンダリングされる', () => {
      render(<TodoEditModal {...defaultProps} />);
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
    });

    it('ダイアログタイトルが「タスクを編集」と表示される', () => {
      render(<TodoEditModal {...defaultProps} />);
      expect(screen.getByTestId('dialog-title')).toHaveTextContent('タスクを編集');
    });

    it('TodoFormがレンダリングされる', () => {
      render(<TodoEditModal {...defaultProps} />);
      expect(screen.getByTestId('todo-form')).toBeInTheDocument();
    });

    it('DialogTrigger（新規作成ボタン）はレンダリングされない', () => {
      render(<TodoEditModal {...defaultProps} />);
      expect(screen.queryByTestId('dialog-trigger')).not.toBeInTheDocument();
      expect(screen.queryByTestId('create-button')).not.toBeInTheDocument();
    });
  });

  /* --------------------
     Dialog開閉制御
  -------------------- */

  describe('Dialog開閉制御', () => {
    it('open=trueのとき data-open属性がtrueになる', () => {
      render(<TodoEditModal {...defaultProps} open={true} />);
      expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'true');
    });

    it('open=falseのとき data-open属性がfalseになる', () => {
      render(<TodoEditModal {...defaultProps} open={false} />);
      expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'false');
    });

    it('onOpenChangeがDialogに渡される', async () => {
      const onOpenChange = vi.fn();
      render(<TodoEditModal {...defaultProps} onOpenChange={onOpenChange} />);

      await userEvent.click(screen.getByTestId('dialog-close-trigger'));

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  /* --------------------
     defaultValuesのマッピング
  -------------------- */

  describe('defaultValuesのマッピング', () => {
    it('titleがtodo_titleにマッピングされる', () => {
      render(<TodoEditModal {...defaultProps} title="マッピングテスト" />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-default-title',
        'マッピングテスト'
      );
    });

    it('priorityがdefaultValuesに渡される', () => {
      render(<TodoEditModal {...defaultProps} priority="MEDIUM" />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-default-priority',
        'MEDIUM'
      );
    });

    it('progressがdefaultValuesに渡される', () => {
      render(<TodoEditModal {...defaultProps} progress={75} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-default-progress',
        '75'
      );
    });

    it('defaultValuesが正しい構造でTodoFormに渡される', () => {
      render(<TodoEditModal {...defaultProps} />);

      expect(getLastTodoFormProps().defaultValues).toEqual({
        todo_title: 'テストタスク',
        priority: 'HIGH',
        progress: 50,
      });
    });

    it.each([
      { priority: 'HIGH' as const },
      { priority: 'MEDIUM' as const },
      { priority: 'LOW' as const },
    ])('priority=$priorityが正しく渡される', ({ priority }) => {
      render(<TodoEditModal {...defaultProps} priority={priority} />);

      expect(getLastTodoFormProps().defaultValues.priority).toBe(priority);
    });
  });

  /* --------------------
     submitLabelの切り替え
  -------------------- */

  describe('submitLabelの切り替え', () => {
    it('isSubmitting=falseのとき submitLabelが「変更を保存」になる', () => {
      render(<TodoEditModal {...defaultProps} isSubmitting={false} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-submit-label',
        '変更を保存'
      );
    });

    it('isSubmitting=trueのとき submitLabelが「保存中...」になる', () => {
      render(<TodoEditModal {...defaultProps} isSubmitting={true} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-submit-label',
        '保存中...'
      );
    });

    it('isSubmittingが未指定のとき submitLabelが「変更を保存」になる', () => {
      const { id, title, priority, progress, open, onOpenChange, onSubmit } = defaultProps;
      render(
        <TodoEditModal
          id={id}
          title={title}
          priority={priority}
          progress={progress}
          open={open}
          onOpenChange={onOpenChange}
          onSubmit={onSubmit}
        />
      );
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-submit-label',
        '変更を保存'
      );
    });
  });

  /* --------------------
     isLoadingの受け渡し
  -------------------- */

  describe('isLoadingの受け渡し', () => {
    it('isSubmitting=trueのとき isLoading=trueがTodoFormに渡される', () => {
      render(<TodoEditModal {...defaultProps} isSubmitting={true} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-is-loading',
        'true'
      );
    });

    it('isSubmitting=falseのとき isLoading=falseがTodoFormに渡される', () => {
      render(<TodoEditModal {...defaultProps} isSubmitting={false} />);
      expect(screen.getByTestId('todo-form')).toHaveAttribute(
        'data-is-loading',
        'false'
      );
    });
  });

  /* --------------------
     onSubmitの受け渡し
  -------------------- */

  describe('onSubmitの受け渡し', () => {
    it('onSubmitがそのままTodoFormに渡される（ラップなし）', () => {
      const onSubmit = vi.fn();
      render(<TodoEditModal {...defaultProps} onSubmit={onSubmit} />);

      // handleSubmitはコメントアウトされているため、渡されたonSubmitと同一参照
      expect(getLastTodoFormProps().onSubmit).toBe(onSubmit);
    });

    it('TodoForm経由でonSubmitを呼ぶとフォーム値がそのまま渡される', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      render(<TodoEditModal {...defaultProps} onSubmit={onSubmit} />);

      await getLastTodoFormProps().onSubmit(mockFormValues);

      expect(onSubmit).toHaveBeenCalledTimes(1);
      expect(onSubmit).toHaveBeenCalledWith(mockFormValues);
    });

    it('onSubmit後にonOpenChange(false)は呼ばれない（閉じる処理なし）', async () => {
      const onSubmit = vi.fn().mockResolvedValue(undefined);
      const onOpenChange = vi.fn();
      render(
        <TodoEditModal
          {...defaultProps}
          onSubmit={onSubmit}
          onOpenChange={onOpenChange}
        />
      );

      await getLastTodoFormProps().onSubmit(mockFormValues);

      // handleSubmitがコメントアウトされているため onOpenChange は呼ばれない
      expect(onOpenChange).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     idプロップ（JSX内で未使用）
  -------------------- */

  describe('idプロップ', () => {
    it('idが数値でもレンダリングでエラーにならない', () => {
      expect(() =>
        render(<TodoEditModal {...defaultProps} id={42} />)
      ).not.toThrow();
    });

    it('idが文字列でもレンダリングでエラーにならない', () => {
      expect(() =>
        render(<TodoEditModal {...defaultProps} id="relay-node-id-abc" />)
      ).not.toThrow();
    });
  });
});