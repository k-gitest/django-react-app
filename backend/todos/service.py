from .models import Todo
from django.db.models import Count, Case, When
from django.shortcuts import get_object_or_404


class TodoService:
    """
    Todoのビジネスロジック層
    
    バリデーションはSerializerで行われているため、
    ここでは純粋なビジネスロジックのみを実装
    """
    
    @staticmethod
    def get_user_todos(user):
        """ユーザー自身のタスクのみを取得（認可の担保）"""
        return Todo.objects.filter(user=user)

    @staticmethod
    def create_todo(user, validated_data):
        """
        タスクの作成
        
        Args:
            user: 作成者
            validated_data: Serializerで検証済みのデータ
        """
        return Todo.objects.create(user=user, **validated_data)

    @staticmethod
    def update_todo(todo_id, user, validated_data):
        """
        タスクの更新
        
        Args:
            todo_id: 更新対象のID
            user: リクエストユーザー（認可チェック用）
            validated_data: Serializerで検証済みのデータ
        """
        # 認可チェック: 存在確認 + 本人確認
        todo = get_object_or_404(Todo, id=todo_id, user=user)
        
        # 更新
        for key, value in validated_data.items():
            setattr(todo, key, value)
        todo.save()
        
        return todo

    @staticmethod
    def delete_todo(todo_id, user):
        """
        タスクの削除
        
        Args:
            todo_id: 削除対象のID
            user: リクエストユーザー（認可チェック用）
        """
        # 認可チェック: 存在確認 + 本人確認
        todo = get_object_or_404(Todo, id=todo_id, user=user)
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

    @staticmethod
    def get_priority_stats(user):
        """優先度別の統計を取得"""
        return list(
            Todo.objects.filter(user=user)
            .values('priority')
            .annotate(count=Count('id'))
            .order_by('priority')
        )