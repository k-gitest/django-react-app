from .models import Todo
from django.db.models import Count, Case, When, Value, IntegerField

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

    @staticmethod
    def get_progress_stats(user):
        """進捗率の分布を集計（20%刻み）"""
        return Todo.objects.filter(user=user).aggregate(
            range_0_20=Count(Case(When(progress__lte=20, then=1))),
            range_21_40=Count(Case(When(progress__gt=20, progress__lte=40, then=1))),
            range_41_60=Count(Case(When(progress__gt=40, progress__lte=60, then=1))),
            range_61_80=Count(Case(When(progress__gt=60, progress__lte=80, then=1))),
            range_81_100=Count(Case(When(progress__gt=80, then=1))),
        )