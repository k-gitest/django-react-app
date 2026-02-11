import { TodoIndex } from "@/features/todos/components/TodoIndexContainer"
//import { TodoIndexContainer as Todoindex } from "@/features/todos/components/TodoIndexRelayContainer"
import { PageAsyncBoundary } from "@/components/async-boundary"

const TodoPage = () => {
    return (
        <PageAsyncBoundary pageName="Todoページ" >
            <TodoIndex />
        </PageAsyncBoundary>
    )
}

export default TodoPage