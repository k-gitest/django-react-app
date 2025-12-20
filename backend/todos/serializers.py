from rest_framework import serializers
from .models import Todo

class TodoSerializer(serializers.ModelSerializer):
    # フロントからは送らせず、API側でログインユーザーを紐付けるため read_only
    user = serializers.ReadOnlyField(source='user.email')

    class Priority(serializers.ChoiceField):
        def __init__(self, **kwargs):
            super().__init__(choices=Todo.Priority.choices, **kwargs)

    class Meta:
        model = Todo
        fields = ['id', 'user', 'todo_title', 'priority', 'progress', 'created_at', 'updated_at']