"""墨韵书境后端 - 全局配置"""
from __future__ import annotations

from pathlib import Path


# 项目根 (webapp/)
ROOT_DIR = Path(__file__).resolve().parents[2]

# 数据目录
DATA_DIR = ROOT_DIR / "data"
NOVELS_DIR = DATA_DIR / "novels"
CACHE_DIR = DATA_DIR / "cache"
STORIES_DIR = DATA_DIR / "stories"
EXPORTS_DIR = DATA_DIR / "exports"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "inkrealm.db"

for _d in (DATA_DIR, NOVELS_DIR, CACHE_DIR, STORIES_DIR, EXPORTS_DIR, UPLOADS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# LLM 配置(密钥按用户要求写死)
LLM_API_KEY = "sk-66a329fb2054471a9a44e8cadbca9df5"
LLM_BASE_URL = "https://api.deepseek.com"
# 修正：旧值 "deepseek-v4-flash" 在 DeepSeek 官方不存在；改为通用对话模型
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4096

# 上传限制
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# 内置示例小说 (启动时自动注册)
SEED_NOVEL_PATH = ROOT_DIR.parent / "《武动乾坤》天蚕土豆.jsonl"
SEED_NOVEL_TITLE = "武动乾坤"
SEED_NOVEL_AUTHOR = "天蚕土豆"

# CORS
ALLOWED_ORIGINS = ["*"]
