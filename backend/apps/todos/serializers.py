from rest_framework import serializers
from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    """
    Todoの作成・更新用シリアライザー
    
    - userはread_only（API側でログインユーザーを自動紐付け）
    - バリデーションエラーは統一エラーハンドラーで処理
    """
    
    # フロントからは送らせず、API側でログインユーザーを紐付けるため read_only
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Todo
        fields = [
            'id',
            'user', 
            'todo_title',
            'priority',
            'progress',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_todo_title(self, value: str) -> str:
        """
        タイトルのバリデーション
        
        - 空白のみのタイトルを拒否
        - 前後の空白を自動トリミング
        
        Args:
            value: タイトル文字列
        
        Returns:
            str: トリミング後のタイトル
        
        Raises:
            serializers.ValidationError: タイトルが空の場合
        """
        title = value.strip()
        if not title:
            raise serializers.ValidationError(
                "タイトルは空にできません。",
                code="empty_title"
            )
        
        # 最大長チェック（モデル定義と一致させる）
        if len(title) > 200:
            raise serializers.ValidationError(
                "タイトルは200文字以内で入力してください。",
                code="title_too_long"
            )
        
        return title

    def validate_progress(self, value: int) -> int:
        """
        進捗率のバリデーション
        
        Args:
            value: 進捗率（0-100）
        
        Returns:
            int: バリデーション済みの進捗率
        
        Raises:
            serializers.ValidationError: 範囲外の値の場合
        """
        # DRFがIntegerFieldとして自動的に型変換・検証するため
        # isinstance(value, int)チェックは不要
        
        if not (0 <= value <= 100):
            raise serializers.ValidationError(
                "進捗率は0から100の範囲で指定してください。",
                code="progress_out_of_range"
            )
        
        return value
    
    def validate_priority(self, value: str) -> str:
        """
        優先度のバリデーション
        
        Args:
            value: 優先度（LOW/MEDIUM/HIGH）
        
        Returns:
            str: バリデーション済みの優先度
        
        Raises:
            serializers.ValidationError: 無効な優先度の場合
        """
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"優先度は {', '.join(valid_priorities)} のいずれかを指定してください。",
                code="invalid_priority"
            )
        
        return value


class TodoSearchParamsSerializer(serializers.Serializer):
    """
    セマンティック検索のクエリパラメータバリデーション
    """
    q = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
        error_messages={
            'required': '検索クエリ "q" を指定してください。',
            'blank': '検索クエリは空にできません。',
            'max_length': '検索クエリは500文字以内で入力してください。'
        }
    )
    
    top_k = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=100,
        error_messages={
            'min_value': 'top_k は1以上を指定してください。',
            'max_value': 'top_k は100以下を指定してください。',
            'invalid': 'top_k は整数を指定してください。'
        }
    )
    
    min_score = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        error_messages={
            'min_value': 'min_score は0.0以上を指定してください。',
            'max_value': 'min_score は1.0以下を指定してください。',
            'invalid': 'min_score は小数を指定してください。'
        }
    )
    
    def validate_q(self, value: str) -> str:
        """検索クエリの前後空白を除去"""
        return value.strip()


class VectorIndexingWebhookSerializer(serializers.Serializer):
    """
    ベクトルインデックスWebhookのペイロードバリデーション
    """
    todo_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            'required': 'todo_id is required',
            'invalid': 'todo_id must be an integer',
            'min_value': 'todo_id must be greater than 0'
        }
    )
    
    operation = serializers.ChoiceField(
        choices=['upsert', 'delete'],
        default='upsert',
        error_messages={
            'invalid_choice': 'operation must be "upsert" or "delete"'
        }
    )


class BulkVectorIndexingWebhookSerializer(serializers.Serializer):
    """
    一括ベクトルインデックスWebhookのペイロードバリデーション
    """
    user_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            'required': 'user_id is required',
            'invalid': 'user_id must be an integer',
            'min_value': 'user_id must be greater than 0'
        }
    )