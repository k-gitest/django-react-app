import type { Todo, Priority } from '../types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
//import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

interface TodoItemProps {
  todo: Todo;
  onToggleComplete: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: number) => void;
}

// 優先度によってバッジの色を変えるヘルパー関数
const getPriorityVariant = (priority: Priority) => {
  switch (priority) {
    case 'HIGH':
      return 'destructive'; // 赤系
    case 'MEDIUM':
      return 'default';    // 青系
    case 'LOW':
      return 'secondary';  // 灰色系
    default:
      return 'outline';
  }
};

export const TodoItem = ({ todo, onToggleComplete, onEdit, onDelete }: TodoItemProps) => {
  const isCompleted = todo.progress === 100;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center space-x-2">
          <Checkbox
            checked={isCompleted}
            onCheckedChange={() => onToggleComplete(todo)}
            id={`todo-${todo.id}`}
          />
          <CardTitle className={`text-lg ${isCompleted ? 'line-through text-gray-500' : ''}`}>
            <label htmlFor={`todo-${todo.id}`}>{todo.todo_title}</label>
          </CardTitle>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(todo)}>
              <Pencil className="mr-2 h-4 w-4" />
              編集
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onDelete(todo.id)} className="text-red-600 focus:text-red-600">
              <Trash2 className="mr-2 h-4 w-4" />
              削除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="space-y-2">
        <Badge variant={getPriorityVariant(todo.priority)}>
          {todo.priority === 'LOW' ? '低' : todo.priority === 'MEDIUM' ? '中' : '高'}
        </Badge>
        <Progress value={todo.progress} className="h-2" />
      </CardContent>
      <CardFooter className="flex justify-between text-sm text-gray-500">
        <span>進捗: {todo.progress}%</span>
        <span>更新: {new Date(todo.updated_at).toLocaleDateString()}</span>
      </CardFooter>
    </Card>
  );
};