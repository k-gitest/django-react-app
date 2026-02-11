import { ComponentAsyncBoundary } from '@/components/async-boundary';
import { TodoList } from '@/features/todos/components/TodoListContainer';
import { TodoProgressChart } from '@/features/todos/components/TodoProgressChart';
import { TodoStatsChart } from '@/features/todos/components/TodoStatsChart';

const Dashboard = () => {
  return (
    <>
      <div>ダッシュボード</div>
      <ComponentAsyncBoundary componentName="DashboardProgress">
        <TodoProgressChart />
      </ComponentAsyncBoundary>
      <ComponentAsyncBoundary componentName="DashboardStats">
        <TodoStatsChart />
      </ComponentAsyncBoundary>
      <ComponentAsyncBoundary componentName="DashboardList">
        <TodoList showActions={false} limit={3} />
      </ComponentAsyncBoundary>
    </>
  );
};

export default Dashboard;
