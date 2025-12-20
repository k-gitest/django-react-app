from .models import Todo

class TodoService:
    @staticmethod
    def get_user_todos(user):
        """ユーザー自身のタスクのみを取得（認可の担保）"""
        return Todo.objects.filter(user=user)

    @staticmethod
    def create_todo(user, data):
        """タスクの作成"""
        return Todo.objects.create(user=user, **data)

    @staticmethod
    def update_todo(todo_id, user, data):
        """タスクの更新（本人のものであることを確認）"""
        todo = Todo.objects.get(id=todo_id, user=user)
        for key, value in data.items():
            setattr(todo, key, value)
        todo.save()
        return todo

    @staticmethod
    def delete_todo(todo_id, user):
        """タスクの削除"""
        todo = Todo.objects.get(id=todo_id, user=user)
        todo.delete()