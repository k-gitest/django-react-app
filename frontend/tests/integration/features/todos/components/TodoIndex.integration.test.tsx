import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TodoIndex } from '@/features/todos/components/TodoIndex';

// 子コンポーネントのモック
// チャートやフォームは個別にテストされているはずなので、
// Indexレベルでは「存在するか」を確認するために簡略化します。
vi.mock('@/features/todos/components/TodoList', () => ({
  TodoList: () => <div data-testid="todo-list">TodoList Component</div>,
}));

vi.mock('@/features/todos/components/TodoCreateForm', () => ({
  TodoCreateForm: () => <button data-testid="todo-create-form">Create Form</button>,
}));

vi.mock('@/features/todos/components/TodoStatsChart', () => ({
  TodoStatsChart: () => <div data-testid="todo-stats-chart">Stats Chart</div>,
}));

vi.mock('@/features/todos/components/TodoProgressChart', () => ({
  TodoProgressChart: () => <div data-testid="todo-progress-chart">Progress Chart</div>,
}));

describe('TodoIndex', () => {
  it('ヘッダーテキストと説明文が表示されること', () => {
    render(<TodoIndex />);
    
    expect(screen.getByText('TODO')).toBeInTheDocument();
    expect(screen.getByText('現在のタスク状況と進捗統計を確認できます。')).toBeInTheDocument();
  });

  it('すべての主要なコンポーネントが正しく配置されていること', () => {
    render(<TodoIndex />);

    // 各コンポーネントが描画されているか確認
    expect(screen.getByTestId('todo-create-form')).toBeInTheDocument();
    expect(screen.getByTestId('todo-stats-chart')).toBeInTheDocument();
    expect(screen.getByTestId('todo-progress-chart')).toBeInTheDocument();
    expect(screen.getByTestId('todo-list')).toBeInTheDocument();
  });

  it('「マイタスク」セクションのタイトルが表示されること', () => {
    render(<TodoIndex />);
    expect(screen.getByText('マイタスク')).toBeInTheDocument();
  });

  it('レイアウト構造が正しいクラスを持っていること', () => {
    const { container } = render(<TodoIndex />);
    
    // Gridレイアウトが適用されているか（簡易的な確認）
    const gridContainer = container.querySelector('.grid');
    expect(gridContainer).toHaveClass('md:grid-cols-2');
  });
});