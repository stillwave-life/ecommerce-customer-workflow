# JD Windows UIA Probe Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为当前 OpenClaw skill 增加面向 Windows UIA 桌面助手主线的文档与 probe 实施计划，使 skill 描述、入口声明和后续实现方向与当前项目状态一致。

**Architecture:** 保持现有离线 workflow 与 desktop assistant 双主线并存，不引入 browser automation 路线。新增的实现重点放在 Windows UIA probe / adapter / foundation 链路，由 `windows_adapter` 承接真实 UIA 风格输入，再进入 `perception -> launcher`。

**Tech Stack:** Python, OpenClaw skill metadata, JSON CLI entrypoints, pytest

---

### Task 1: 更新 SKILL.md 为双主线说明

**Files:**
- Modify: `SKILL.md`
- Reference: `scripts/jd_customer_service_start.py`
- Reference: `app/desktop/launcher.py`

**Step 1: Write the failing review check**

手动检查当前 `SKILL.md`。

预期失败点：
- 仍把项目描述为纯离线 MVP
- 没有提到 `scripts/jd_customer_service_start.py`
- 没有提到 Windows UIA / desktop assistant 主线

**Step 2: Confirm the gap**

阅读：
- `SKILL.md`
- `scripts/jd_customer_service_start.py`

Expected: `SKILL.md` 与当前 desktop assistant 能力不一致。

**Step 3: Write minimal update**

更新 `SKILL.md`：
- 保留 `validate_request.py` / `prepare_request.py` / `generate_reply.py`
- 增加 `scripts/jd_customer_service_start.py`
- 说明项目当前有两条能力线：
  - 离线客服 workflow
  - 京东桌面客服 assistant 合同链路
- 明确当前未实现真实自动发送
- 明确 Windows UIA 是下一步主线，不是 browser automation

**Step 4: Review updated content**

核对：
- YAML frontmatter 合法
- `metadata.openclaw.entrypoints` 包含 desktop assistant 入口
- 描述与当前代码状态一致

**Step 5: Commit**

```bash
git add SKILL.md
git commit -m "docs: align skill description with desktop assistant direction"
```

---

### Task 2: 更新 _meta.json 元数据

**Files:**
- Modify: `_meta.json`
- Reference: `SKILL.md`

**Step 1: Write the failing review check**

检查当前 `_meta.json`。

预期失败点：
- 只有 slug/version/owner 占位
- 没有 runtime
- 没有 entrypoints
- 没有 config defaults

**Step 2: Confirm the gap**

阅读：
- `_meta.json`
- `SKILL.md`

Expected: `_meta.json` 不符合 OpenClaw 建议格式。

**Step 3: Write minimal update**

更新 `_meta.json` 至最小可用结构：

```json
{
  "name": "ecommerce-customer-workflow",
  "version": "1.5.0",
  "description": "京东客服 workflow 与桌面 assistant skill",
  "runtime": "python",
  "entrypoints": [
    "scripts/validate_request.py",
    "scripts/prepare_request.py",
    "scripts/generate_reply.py",
    "scripts/jd_customer_service_start.py"
  ],
  "config": {
    "defaults": "config/default.json"
  }
}
```

**Step 4: Review updated content**

核对：
- 路径都真实存在
- 与 `SKILL.md` 一致

**Step 5: Commit**

```bash
git add _meta.json
git commit -m "docs: add openclaw metadata entrypoints"
```

---

### Task 3: 更新 config/default.json 说明 UIA 主线

**Files:**
- Modify: `config/default.json`
- Reference: `scripts/jd_customer_service_start.py`

**Step 1: Write the failing review check**

检查当前 `config/default.json`。

预期失败点：
- 有 `browser_automation: false`，但没有 desktop assistant / windows uia 相关能力标识
- 配置没有体现当前主线方向

**Step 2: Confirm the gap**

阅读：
- `config/default.json`
- `scripts/jd_customer_service_start.py`

Expected: 配置没有表达 desktop assistant / UIA 当前状态。

**Step 3: Write minimal update**

只增加当前真正会用到的字段，例如：

```json
"features": {
  ...,
  "desktop_assistant": true,
  "windows_uia_probe": false,
  "windows_uia_live_backend": false,
  "browser_automation": false
}
```

必要时增加：

```json
"desktop_policy": {
  "manual_send_only": true,
  "minimum_platform_confidence": 0.7
}
```

不要添加未使用的大量未来字段。

**Step 4: Review updated content**

核对：
- JSON 合法
- 字段与当前代码边界一致
- 不虚假宣称 live backend 已完成

**Step 5: Commit**

```bash
git add config/default.json
git commit -m "docs: document desktop assistant config flags"
```

---

### Task 4: 更新 README.md 项目定位

**Files:**
- Modify: `README.md`
- Reference: `docs/windows-ui-automation-adapter-direction.md`
- Reference: `docs/windows-uia-stability-foundation.md`

**Step 1: Write the failing review check**

检查当前 `README.md`。

预期失败点：
- 仍强调离线 workflow
- 把后续路线写成 browser 自动化主线
- 没有体现 Windows UIA probe / desktop assistant 当前方向

**Step 2: Confirm the gap**

阅读：
- `README.md`
- `docs/windows-ui-automation-adapter-direction.md`
- `docs/windows-uia-stability-foundation.md`

Expected: README 与最新设计方向不一致。

**Step 3: Write minimal update**

更新 README：
- 首页一句话改为：离线 workflow + desktop assistant foundation
- 增加当前 desktop assistant 入口介绍
- 把“浏览器半自动执行”降级为旧设想，不作为当前主线
- 明确当前下一步是 Windows UIA probe / adapter，而不是 browser automation

**Step 4: Review updated content**

核对：
- 文案简短完整
- 与 docs 主线一致
- 不承诺未实现能力

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update readme for windows uia direction"
```

---

### Task 5: 补 examples 与入口契约说明

**Files:**
- Create: `examples/jd_customer_service_start.example.json`
- Modify: `README.md`
- Modify: `SKILL.md`
- Reference: `scripts/jd_customer_service_start.py`

**Step 1: Write the failing review check**

检查当前 examples。

预期失败点：
- 没有 desktop assistant 示例输入
- 文档无法直接演示 `jd_customer_service_start.py`

**Step 2: Confirm the gap**

阅读：
- `examples/prepare_request.example.json`
- `examples/generate_reply.example.json`
- `scripts/jd_customer_service_start.py`

Expected: 缺少 desktop assistant 输入样例。

**Step 3: Write minimal example**

创建：`examples/jd_customer_service_start.example.json`

内容使用当前实际 contract：

```json
{
  "command": "京东客服启动",
  "shop_id": "shop_001",
  "session_id": "desktop-session-1",
  "desktop_context": {
    "platform": "jd_customer_service",
    "confidence": 0.9,
    "active_customer": {
      "id": "jd_4a3d4c80e30ef",
      "name": "jd_4a3d4c80e30ef"
    },
    "chat_context": {
      "latest_customer_message": "这款还有吗？",
      "recent_messages": [],
      "contains_image": false
    },
    "product_context": {
      "tab_active": false,
      "items": []
    },
    "user_order_context": {
      "user_labels": [],
      "orders": [],
      "service_forms": []
    },
    "input_context": {
      "editable": true,
      "has_smart_reply": false,
      "send_button_visible": true,
      "existing_text": ""
    }
  }
}
```

并在 `README.md` / `SKILL.md` 增加调用示例。

**Step 4: Review updated content**

核对：
- 示例能直接喂给脚本
- `desktop_context` shape 与代码一致

**Step 5: Commit**

```bash
git add examples/jd_customer_service_start.example.json README.md SKILL.md
git commit -m "docs: add desktop assistant example payload"
```

---

### Task 6: 写正式 UIA probe 实施计划

**Files:**
- Create: `docs/plans/2026-04-19-jd-windows-uia-probe.md`
- Reference: `app/desktop/windows_adapter/ui_node_adapter.py`
- Reference: `app/desktop/windows_adapter/region_input_bridge.py`
- Reference: `app/desktop/windows_uia_foundation/input_candidate_ranker.py`
- Reference: `app/desktop/windows_uia_foundation/action_gate.py`
- Reference: `app/desktop/launcher.py`

**Step 1: Write the failing review check**

检查 `docs/plans/`。

预期失败点：
- 没有一份按 writing-plans 格式编写的正式 OpenClaw/UIA probe 实施计划
- 现有文档偏方向说明，不是可执行任务单

**Step 2: Confirm the gap**

阅读：
- `docs/plans/2026-04-16-windows-ui-automation-adapter.md`
- `docs/plans/2026-04-17-windows-uia-stability-foundation.md`

Expected: 现有计划偏合同层，不是本轮要执行的文档更新 + probe 落地计划。

**Step 3: Write minimal plan**

创建：`docs/plans/2026-04-19-jd-windows-uia-probe.md`

内容要求：
- 使用 writing-plans 标准头
- 目标写清：Windows UIA probe / adapter 接入
- 任务拆细到 TDD 粒度
- 关键文件明确列出
- 验证命令明确列出
- 不写 browser automation 路线

**Step 4: Review updated content**

核对：
- 文件名符合日期规范
- 头部格式正确
- 步骤足够细
- 能直接交给执行阶段

**Step 5: Commit**

```bash
git add docs/plans/2026-04-19-jd-windows-uia-probe.md
git commit -m "docs: add windows uia probe implementation plan"
```

---

### Task 7: 统一回归文档一致性

**Files:**
- Review: `SKILL.md`
- Review: `_meta.json`
- Review: `README.md`
- Review: `config/default.json`
- Review: `examples/jd_customer_service_start.example.json`
- Review: `docs/plans/2026-04-19-jd-windows-uia-probe.md`

**Step 1: Run review checklist**

检查：
- OpenClaw metadata 是否一致
- entrypoints 是否真实存在
- README / SKILL / config 表述是否一致
- 是否仍然坚持 manual-only 边界
- 是否没有误写 browser automation 为当前主线

**Step 2: Run targeted validation commands**

Run:

```bash
py -3 scripts/jd_customer_service_start.py "$(python - <<'PY'
import json
from pathlib import Path
print(json.dumps(json.loads(Path('examples/jd_customer_service_start.example.json').read_text(encoding='utf-8')), ensure_ascii=False))
PY
)"
```

Expected: 返回 `ok: true` 且包含 `reply` 与 `fill_action`。

**Step 3: Run tests**

Run:

```bash
py -3 -m pytest tests/desktop/test_jd_customer_service_start.py tests/desktop/test_launcher.py tests/desktop/test_fill_action.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add SKILL.md _meta.json README.md config/default.json examples/jd_customer_service_start.example.json docs/plans/2026-04-19-jd-windows-uia-probe.md
git commit -m "docs: align openclaw skill docs with windows uia desktop direction"
```
