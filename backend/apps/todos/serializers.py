from rest_framework import serializers
from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    # フロントからは送らせず、API側でログインユーザーを紐付けるため read_only
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Todo
        fields = ['id', 'user', 'todo_title', 'priority', 'progress', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_todo_title(self, value):
        """空白のみのタイトルを弾く（トリミングも実施）"""
        title = value.strip()
        if not title:
            raise serializers.ValidationError("タイトルは空にできません。")
        return title

    def validate_progress(self, value):
        """進捗率の範囲チェック"""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("進捗率は0から100の範囲で指定してください。")
        return value
    
    # 注意: isinstance(value, int)チェックは不要
    # DRFがIntegerFieldとして自動的に型変換・検証する