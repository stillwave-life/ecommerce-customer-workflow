# 更新日志

## v1.6.0 - 2026-04-19

### 新增功能

**Continuity 上下文压缩适配器**
- 新增 `app/continuity_adapter.py`
- 当外部传入的 history 超过阈值时调用已安装的 Continuity 压缩能力
- 未安装 Continuity 时返回未压缩结果，不影响主流程

### 更新文件

- `SKILL.md` - 添加 Continuity 适配器说明
- `_meta.json` - 更新版本至 1.6.0，添加集成信息
- `app/continuity_adapter.py` - 新增适配器

### 使用方法

```python
from app.continuity_adapter import check_and_compress_context

result = check_and_compress_context(history, max_tokens=200000)
if result["compressed"]:
    history = result["history"]
```

### 依赖

- Continuity skill 安装在 `~/.openclaw/skills/Continuity` 或 `~/.openclaw/workspace/skills/Continuity`
