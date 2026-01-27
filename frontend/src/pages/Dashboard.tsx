import { TodoProgressChart } from "@/features/todos/components/TodoProgressChart"
import { TodoStatsChart } from "@/features/todos/components/TodoStatsChart"
import { TodoList } from "@/features/todos/components/TodoList"
import { ComponentAsyncBoundary } from "@/components/async-boundary"

const Dashboard = () => {
    return (
        <>
            <div>ダッシュボード</div>
            <TodoProgressChart />
            <ComponentAsyncBoundary componentName="DashboardStats">
                <TodoStatsChart />
            </ComponentAsyncBoundary>
            <TodoList showActions={false} limit={3} />
        </>
    )
}

export default Dashboard