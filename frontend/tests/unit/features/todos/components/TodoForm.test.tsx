import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TodoForm } from '@/features/todos/components/TodoForm';
import type { TodoFormValues } from '@/features/todos/schemas';

describe('TodoForm', () => {
  let mockOnSubmit: (values: TodoFormValues) => Promise<void>;
  let mockOnCancel: () => void;

  beforeEach(() => {
    mockOnSubmit = vi.fn<(values: TodoFormValues) => Promise<void>>().mockResolvedValue(undefined);
    mockOnCancel = vi.fn();
  });

  describe('表示', () => {
    it('フォームの全ての入力フィールドが表示される', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // タイトル
      expect(screen.getByLabelText(/タイトル/i)).toBeInTheDocument();

      // 優先度（comboboxとして表示）
      expect(screen.getByRole('combobox')).toBeInTheDocument();

      // 進捗（ラベルのテキストで確認）
      expect(screen.getByText(/進捗 \(0%\)/i)).toBeInTheDocument();

      // 送信ボタン
      expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument();
    });

    it('デフォルトのsubmitLabelは「保存」', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      expect(screen.getByRole('button', { name: '保存' })).toBeInTheDocument();
    });

    it('submitLabelをカスタマイズできる', () => {
      render(<TodoForm onSubmit={mockOnSubmit} submitLabel="作成" />);

      expect(screen.getByRole('button', { name: '作成' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '保存' })).not.toBeInTheDocument();
    });

    it('onCancelが渡されない場合、キャンセルボタンは表示されない', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      expect(screen.queryByRole('button', { name: /キャンセル/i })).not.toBeInTheDocument();
    });

    it('onCancelが渡された場合、キャンセルボタンが表示される', () => {
      render(<TodoForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      expect(screen.getByRole('button', { name: /キャンセル/i })).toBeInTheDocument();
    });
  });

  describe('初期値', () => {
    it('defaultValuesが指定されない場合、デフォルト値が設定される', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // タイトルは空
      const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement;
      expect(titleInput.value).toBe('');

      // 優先度は「中」（表示テキスト）
      expect(screen.getAllByText('中')[0]).toBeInTheDocument();

      // 進捗は0
      expect(screen.getByText(/進捗 \(0%\)/i)).toBeInTheDocument();
    });

    it('defaultValuesが指定された場合、初期値として設定される', () => {
      const defaultValues: Partial<TodoFormValues> = {
        todo_title: 'テストタスク',
        priority: 'HIGH',
        progress: 75,
      };

      render(<TodoForm onSubmit={mockOnSubmit} defaultValues={defaultValues} />);

      // タイトル
      const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement;
      expect(titleInput.value).toBe('テストタスク');

      // 優先度は「高」
      expect(screen.getAllByText('高')[0]).toBeInTheDocument();

      // 進捗
      expect(screen.getByText(/進捗 \(75%\)/i)).toBeInTheDocument();
    });

    it('defaultValuesが部分的に指定された場合、他はデフォルト値になる', () => {
      const defaultValues: Partial<TodoFormValues> = {
        todo_title: 'テストタスク',
      };

      render(<TodoForm onSubmit={mockOnSubmit} defaultValues={defaultValues} />);

      // タイトルは指定された値
      const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement;
      expect(titleInput.value).toBe('テストタスク');

      // 優先度はデフォルト（中）
      expect(screen.getAllByText('中')[0]).toBeInTheDocument();

      // 進捗はデフォルト（0）
      expect(screen.getByText(/進捗 \(0%\)/i)).toBeInTheDocument();
    });
  });

  describe('入力操作', () => {
    it('タイトルを入力できる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, 'テストタスク');

      expect(titleInput).toHaveValue('テストタスク');
    });

    it('進捗を数値入力で変更できる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const progressInput = screen.getByRole('spinbutton');
      await user.clear(progressInput);
      await user.type(progressInput, '50');

      await waitFor(() => {
        expect(screen.getByText(/進捗 \(50%\)/i)).toBeInTheDocument();
      });
    });

    it('進捗が0未満の場合、0に制限される', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const progressInput = screen.getByRole('spinbutton');
      
      // 直接負の値を設定（type経由ではなく）
      await user.clear(progressInput);
      
      // まず正の値を入力してから、手動で負の値を設定
      await user.type(progressInput, '50');
      
      // プログラマティックに負の値を設定
      fireEvent.change(progressInput, { target: { value: '-10' } });

      // 送信して実際の値を確認
      await user.type(screen.getByLabelText(/タイトル/i), 'Test');
      await user.click(screen.getByRole('button', { name: /保存/i }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          todo_title: 'Test',
          priority: 'MEDIUM',
          progress: 0, // 負の値は0に制限される
        });
      });
    });

    it('進捗が100を超える場合、100に制限される', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const progressInput = screen.getByRole('spinbutton');
      await user.clear(progressInput);
      await user.type(progressInput, '150');

      await waitFor(() => {
        expect(progressInput).toHaveValue(100);
      });
    });

    it('進捗が空欄の場合、0になる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} defaultValues={{ progress: 50 }} />);

      const progressInput = screen.getByRole('spinbutton');
      await user.clear(progressInput);

      await waitFor(() => {
        expect(progressInput).toHaveValue(0);
      });
    });
  });

  describe('バリデーション', () => {
    it('タイトルが空の場合、エラーメッセージが表示される', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/タイトルを入力してください/i)).toBeInTheDocument();
      });

      // onSubmitは呼ばれない
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('タイトルが1文字の場合も有効', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, 'A');

      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          todo_title: 'A',
          priority: 'MEDIUM',
          progress: 0,
        });
      });
    });

    it('タイトルが長い場合も有効', async () => {
      const user = userEvent.setup();
      const longTitle = 'あ'.repeat(200);

      render(<TodoForm onSubmit={mockOnSubmit} />);

      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, longTitle);

      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          todo_title: longTitle,
          priority: 'MEDIUM',
          progress: 0,
        });
      });
    });
  });

  describe('フォーム送信', () => {
    it('デフォルト値で送信するとonSubmitが呼ばれる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // タイトルのみ入力（優先度と進捗はデフォルト値を使用）
      await user.type(screen.getByLabelText(/タイトル/i), 'テストタスク');

      // 送信
      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          todo_title: 'テストタスク',
          priority: 'MEDIUM',
          progress: 0,
        });
      });
    });

    it('初期値を指定して送信できる', async () => {
      const user = userEvent.setup();
      
      const defaultValues: Partial<TodoFormValues> = {
        todo_title: '既存タスク',
        priority: 'HIGH',
        progress: 75,
      };
      
      render(<TodoForm onSubmit={mockOnSubmit} defaultValues={defaultValues} />);

      // 送信
      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          todo_title: '既存タスク',
          priority: 'HIGH',
          progress: 75,
        });
      });
    });

    it('送信成功後、フォームがリセットされる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // 入力
      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, 'テストタスク');

      // 送信
      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      // フォームがリセットされる
      await waitFor(() => {
        expect(titleInput).toHaveValue('');
      });
    });

    it('送信中はボタンが無効化され、テキストが変わる', async () => {
      const user = userEvent.setup();
      
      // 送信を遅延させる
      const delayedSubmit = vi.fn<(values: TodoFormValues) => Promise<void>>(() => 
        new Promise(resolve => setTimeout(() => resolve(undefined), 100))
      );
      
      render(<TodoForm onSubmit={delayedSubmit} />);

      await user.type(screen.getByLabelText(/タイトル/i), 'テストタスク');
      
      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      // 送信中
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /保存中/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /保存中/i })).toBeDisabled();
      });

      // 送信完了後
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /保存/i })).not.toBeDisabled();
      });
    });

    it('送信に失敗した場合、フォームはリセットされない', async () => {
      const user = userEvent.setup();
      const errorSubmit = vi.fn<(values: TodoFormValues) => Promise<void>>().mockRejectedValue(new Error('Submit failed'));

      render(<TodoForm onSubmit={errorSubmit} />);

      const titleInput = screen.getByLabelText(/タイトル/i);
      await user.type(titleInput, 'テストタスク');

      const submitButton = screen.getByRole('button', { name: /保存/i });
      await user.click(submitButton);

      // エラーが発生しても入力値は保持される
      await waitFor(() => {
        expect(errorSubmit).toHaveBeenCalled();
      });

      expect(titleInput).toHaveValue('テストタスク');
    });
  });

  describe('キャンセル', () => {
    it('キャンセルボタンをクリックするとonCancelが呼ばれる', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      const cancelButton = screen.getByRole('button', { name: /キャンセル/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('キャンセルボタンはtype="button"のためフォーム送信されない', async () => {
      const user = userEvent.setup();
      render(<TodoForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      await user.type(screen.getByLabelText(/タイトル/i), 'テストタスク');

      const cancelButton = screen.getByRole('button', { name: /キャンセル/i });
      await user.click(cancelButton);

      // onCancelは呼ばれるが、onSubmitは呼ばれない
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('優先度の表示', () => {
    it('初期値の優先度が表示される', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // デフォルトは「中」
      expect(screen.getAllByText('中')[0]).toBeInTheDocument();
    });

    it('指定した優先度が表示される', () => {
      render(<TodoForm onSubmit={mockOnSubmit} defaultValues={{ priority: 'HIGH' }} />);

      // 「高」が表示される
      expect(screen.getAllByText('高')[0]).toBeInTheDocument();
    });

    it('Selectコンポーネントが正しく設定されている', () => {
      render(<TodoForm onSubmit={mockOnSubmit} />);

      // comboboxが存在する
      const combobox = screen.getByRole('combobox');
      expect(combobox).toBeInTheDocument();

      // hiddenなselectにオプションが存在する（実際のForm送信用）
      const hiddenSelect = document.querySelector('select[aria-hidden="true"]');
      expect(hiddenSelect).toBeInTheDocument();
      
      const options = hiddenSelect?.querySelectorAll('option');
      expect(options).toHaveLength(3);
    });
  });
});