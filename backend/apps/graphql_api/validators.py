"""
GraphQL層のバリデーションロジック
DRFのSerializerバリデーションに相当
"""
from typing import List, Optional
from .types.todo import TodoCreateInput, TodoUpdateInput
from .types.common import ValidationError


class TodoValidator:
    """Todoのバリデーションルール"""
    
    @staticmethod
    def validate_create(input: TodoCreateInput) -> List[ValidationError]:
        """作成時のバリデーション"""
        errors = []
        
        # タイトルの検証
        title = input.todo_title.strip()
        if not title:
            errors.append(ValidationError(
                field="todo_title",
                message="タイトルは空にできません。",
                code="empty_title"
            ))
        elif len(title) > 200:
            errors.append(ValidationError(
                field="todo_title",
                message="タイトルは200文字以内で入力してください。",
                code="title_too_long"
            ))
        
        # 進捗率の検証
        if not (0 <= input.progress <= 100):
            errors.append(ValidationError(
                field="progress",
                message="進捗率は0から100の範囲で指定してください。",
                code="progress_out_of_range"
            ))
        
        return errors
    
    @staticmethod
    def validate_update(input: TodoUpdateInput) -> List[ValidationError]:
        """更新時のバリデーション"""
        errors = []
        
        # タイトルの検証（指定されている場合のみ）
        if input.todo_title is not None:
            title = input.todo_title.strip()
            if not title:
                errors.append(ValidationError(
                    field="todo_title",
                    message="タイトルは空にできません。",
                    code="empty_title"
                ))
            elif len(title) > 200:
                errors.append(ValidationError(
                    field="todo_title",
                    message="タイトルは200文字以内で入力してください。",
                    code="title_too_long"
                ))
        
        # 進捗率の検証（指定されている場合のみ）
        if input.progress is not None:
            if not (0 <= input.progress <= 100):
                errors.append(ValidationError(
                    field="progress",
                    message="進捗率は0から100の範囲で指定してください。",
                    code="progress_out_of_range"
                ))
        
        return errors