from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # ユーザー一覧表示（list_display）から username を除外し、email を追加
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email',)
    ordering = ('email',)

    # ユーザー編集フォーム (fieldsets) から username を除外
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # emailを主要な認証情報として扱う
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # 新規作成フォーム (add_fieldsets) から username を除外
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # emailを必須とし、パスワードフィールドを2つ設定
            'fields': ('email', 'password', 'password2'), 
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)