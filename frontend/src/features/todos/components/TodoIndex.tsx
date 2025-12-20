import { TodoList } from '@/features/todos/components/TodoList';
import { TodoCreateForm } from '@/features/todos/components/TodoCreateForm';
import { TodoStatsChart } from '@/features/todos/components/TodoStatsChart';
import { TodoProgressChart } from '@/features/todos/components/TodoProgressChart';

export const Dashboard = () => {
  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      {/* ヘッダーエリア */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">TODO</h1>
          <p className="text-muted-foreground">現在のタスク状況と進捗統計を確認できます。</p>
        </div>
        <TodoCreateForm />
      </div>

      {/* 統計エリア (Gridレイアウト) */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="md:col-span-1 lg:col-span-3">
          <TodoStatsChart />
        </div>
        <div className="md:col-span-1 lg:col-span-4">
          <TodoProgressChart />
        </div>
      </div>

      {/* メインコンテンツエリア */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold tracking-tight">マイタスク</h2>
        </div>
        <div className="bg-card rounded-lg border shadow-sm p-6">
          <TodoList />
        </div>
      </div>
    </div>
  );
};