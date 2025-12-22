//import { TodoIndex } from "@/features/todos/components/TodoIndex"
import { TodoProgressChart } from "@/features/todos/components/TodoProgressChart"
import { TodoStatsChart } from "@/features/todos/components/TodoStatsChart"
import { TodoList } from "@/features/todos/components/TodoList"

const Dashboard = () => {
    return (
        <>
            <div>ダッシュボード</div>
            <TodoProgressChart />
            <TodoStatsChart />
            <TodoList showActions={false} limit={3} />
        </>
    )
}

export default Dashboard