from rest_framework import serializers

class AnalyticsEventWebhookSerializer(serializers.Serializer):
    """
    分析イベントWebhookのペイロードバリデーション
    
    QStashから呼ばれるWebhook用のバリデーター
    """
    event_type = serializers.ChoiceField(
        choices=['auth_event'],  # 将来的に他のイベントタイプも追加可能
        required=True,
        error_messages={
            'required': 'event_type is required',
            'invalid_choice': 'invalid event_type'
        }
    )
    event_data = serializers.DictField(
        required=True,
        error_messages={
            'required': 'event_data is required'
        }
    )
    
    def validate_event_data(self, value):
        """
        event_dataの詳細バリデーション
        
        auth_eventの場合、必須フィールドをチェック
        """
        event_type = self.initial_data.get('event_type')
        
        if event_type == 'auth_event':
            required_fields = ['user_id', 'event_type', 'timestamp']
            missing_fields = [field for field in required_fields if field not in value]
            
            if missing_fields:
                raise serializers.ValidationError(
                    f"event_data is missing required fields: {', '.join(missing_fields)}"
                )
        
        return value