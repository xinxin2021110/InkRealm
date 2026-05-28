"""服务层 —— 统一接入 inkrealm 核心包。

启动时把仓库根注入 sys.path，并把 webapp 配置同步到 inkrealm.Context；
为向后兼容，同时调旧 adapter 的 init_config（其内部也会写 inkrealm.Context）。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 路径计算
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[2]
_WEBAPP_ROOT = _HERE.parents[3]
_REPO_ROOT = _HERE.parents[4]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from .. import config as _cfg

# 新核心：一次性初始化
from inkrealm.context import init_context

init_context(
    api_key=_cfg.LLM_API_KEY,
    base_url=_cfg.LLM_BASE_URL,
    model=_cfg.LLM_MODEL,
)

# 旧 adapter 同样调用一遍（idempotent），保证存量代码也走同一个 Context
from novel_character_agent.config import init_config as _init_char_cfg
from novel_story_agent.config import init_config as _init_story_cfg

_init_char_cfg(api_key=_cfg.LLM_API_KEY, base_url=_cfg.LLM_BASE_URL, model=_cfg.LLM_MODEL)
_init_story_cfg(api_key=_cfg.LLM_API_KEY, base_url=_cfg.LLM_BASE_URL, model=_cfg.LLM_MODEL)


def repo_root() -> Path:
    return _REPO_ROOT
