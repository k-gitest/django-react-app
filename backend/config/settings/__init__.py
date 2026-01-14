"""
import os
from decouple import config

# DJANGO_SETTINGS_MODULE が指定されていない場合の予備知識として
# どの環境をロードするかを判定（基本は local）
env_type = os.getenv("ENVIRONMENT", "local").lower()

if env_type == "production":
    from .production import *
elif env_type == "test":
    from .test import *
else:
    from .local import *
"""