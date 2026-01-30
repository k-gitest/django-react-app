"""
GraphQL層のバリデーションロジック
DRFのSerializerバリデーションに相当
"""
from typing import List
import re

from apps.graphql_api.types.todo import TodoCreateInput, TodoUpdateInput
from apps.graphql_api.types.user import (
    RegisterInput,
    LoginInput,
    ChangePasswordInput,
)
from apps.graphql_api.types.common import ValidationError
from apps.users.user_service import UserQueryService


class TodoValidator:
    """Todoのバリデーションルール（既存）"""
    
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


class UserValidator:
    """Userのバリデーションルール（新規）"""
    
    @staticmethod
    def validate_register(input: RegisterInput) -> List[ValidationError]:
        """
        ユーザー登録時のバリデーション
        
        Args:
            input: RegisterInput
        
        Returns:
            List[ValidationError]: エラーリスト（空なら正常）
        """
        errors = []
        
        # メールアドレスの検証
        email_error = UserValidator._validate_email(input.email)
        if email_error:
            errors.append(email_error)
        else:
            # メールアドレス重複チェック
            if UserQueryService.email_exists(input.email):
                errors.append(ValidationError(
                    field="email",
                    message=f"メールアドレス {input.email} は既に登録されています。",
                    code="email_already_exists"
                ))
        
        # パスワードの検証
        password_errors = UserValidator._validate_password(
            input.password,
            input.password_confirm
        )
        errors.extend(password_errors)
        
        # 名前の検証（オプション）
        if input.first_name and len(input.first_name) > 150:
            errors.append(ValidationError(
                field="first_name",
                message="名は150文字以内で入力してください。",
                code="first_name_too_long"
            ))
        
        if input.last_name and len(input.last_name) > 150:
            errors.append(ValidationError(
                field="last_name",
                message="姓は150文字以内で入力してください。",
                code="last_name_too_long"
            ))
        
        return errors
    
    @staticmethod
    def validate_login(input: LoginInput) -> List[ValidationError]:
        """
        ログイン時のバリデーション
        
        Args:
            input: LoginInput
        
        Returns:
            List[ValidationError]: エラーリスト（空なら正常）
        """
        errors = []
        
        # メールアドレスの検証
        email_error = UserValidator._validate_email(input.email)
        if email_error:
            errors.append(email_error)
        
        # パスワードの検証（空チェックのみ）
        if not input.password:
            errors.append(ValidationError(
                field="password",
                message="パスワードを入力してください。",
                code="password_required"
            ))
        
        return errors
    
    @staticmethod
    def validate_change_password(
        input: ChangePasswordInput,
        user
    ) -> List[ValidationError]:
        """
        パスワード変更時のバリデーション
        
        Args:
            input: ChangePasswordInput
            user: 現在のユーザー
        
        Returns:
            List[ValidationError]: エラーリスト（空なら正常）
        """
        errors = []
        
        # 現在のパスワードが正しいか検証
        if not user.check_password(input.old_password):
            errors.append(ValidationError(
                field="old_password",
                message="現在のパスワードが正しくありません。",
                code="invalid_old_password"
            ))
        
        # 新しいパスワードの検証
        password_errors = UserValidator._validate_password(
            input.new_password,
            input.new_password_confirm
        )
        errors.extend(password_errors)
        
        # 新旧パスワードが同じでないか
        if input.old_password == input.new_password:
            errors.append(ValidationError(
                field="new_password",
                message="新しいパスワードは現在のパスワードと異なるものを指定してください。",
                code="same_password"
            ))
        
        return errors
    
    # ===== ヘルパーメソッド =====
    
    @staticmethod
    def _validate_email(email: str) -> ValidationError | None:
        """
        メールアドレスの形式検証
        
        Args:
            email: メールアドレス
        
        Returns:
            ValidationError | None
        """
        if not email:
            return ValidationError(
                field="email",
                message="メールアドレスを入力してください。",
                code="email_required"
            )
        
        # 簡易的なメールアドレス形式チェック
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return ValidationError(
                field="email",
                message="有効なメールアドレスを入力してください。",
                code="invalid_email"
            )
        
        return None
    
    @staticmethod
    def _validate_password(
        password: str,
        password_confirm: str
    ) -> List[ValidationError]:
        """
        パスワードの検証
        
        Args:
            password: パスワード
            password_confirm: パスワード確認
        
        Returns:
            List[ValidationError]: エラーリスト
        """
        errors = []
        
        # 必須チェック
        if not password:
            errors.append(ValidationError(
                field="password",
                message="パスワードを入力してください。",
                code="password_required"
            ))
            return errors
        
        # 最小文字数
        if len(password) < 8:
            errors.append(ValidationError(
                field="password",
                message="パスワードは8文字以上で入力してください。",
                code="password_too_short"
            ))
        
        # 最大文字数
        if len(password) > 128:
            errors.append(ValidationError(
                field="password",
                message="パスワードは128文字以内で入力してください。",
                code="password_too_long"
            ))
        
        # パスワード確認の一致
        if password != password_confirm:
            errors.append(ValidationError(
                field="password_confirm",
                message="パスワードが一致しません。",
                code="password_mismatch"
            ))
        
        return errors