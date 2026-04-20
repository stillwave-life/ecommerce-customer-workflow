---
name: ecommerce-customer-workflow
description: 面向京东客服场景的 OpenClaw workflow 与桌面 assistant skill，支持离线客服上下文整理、保守回复草稿生成，以及京东客服工作台 desktop_context 合同链路。可选接入 Continuity 上下文压缩。
metadata:
  openclaw:
    runtime: python
    entrypoints:
      - scripts/validate_request.py
      - scripts/prepare_request.py
      - scripts/generate_reply.py
      - scripts/jd_customer_service_start.py
---

# ecommerce-customer-workflow

这是一个面向 OpenClaw 的京东客服 skill。当前包含两条能力线：离线客服 workflow，以及京东客服桌面 assistant 合同链路。

## 使用时机
在以下场景触发：
- 需要根据京东商品 URL、商品截图或人工文本线索整理客服上下文
- 需要把商品资料、FAQ、售后规则、发货规则整理成统一结构
- 需要生成保守、可审核的中文客服回复草稿
- 需要以 `desktop_context` 启动京东客服桌面 assistant，生成回复并准备人工发送前的填充动作
- 需要在外部对话历史较长时调用 Continuity 压缩适配器

## 当前工作流
1. 离线 workflow：输入文本 / URL / 图片路径，输出 `prepared` 与 `reply_draft`
2. 桌面 assistant：输入已解析的 `desktop_context`，输出 `reply` 与 `fill_action`
3. Windows UIA 主线：下一步把真实窗口与控件树转换为 `desktop_context`
4. Continuity 适配器：接收外部传入的 history，按阈值调用已安装的 Continuity 压缩能力

## 当前已实现能力
- 标准 OpenClaw skill 目录结构
- 最小请求校验与标准化脚本
- 离线请求准备脚本 `scripts/prepare_request.py`
- 本地知识补齐与保守回复生成脚本 `scripts/generate_reply.py`
- 京东商品 URL 最小识别
- 本地图片路径输入与保守解析回退
- 京东客服桌面 assistant 合同入口 `scripts/jd_customer_service_start.py`
- UI perception / Windows adapter / Windows UIA stability foundation 合同层
- Continuity 上下文压缩适配器 `app/continuity_adapter.py`

## 资源导航
- 架构细节：`references/architecture.md`
- 接入说明：`references/integration.md`
- 桌面 assistant 示例：`examples/jd_customer_service_start.example.json`
- 诊断导出脚本：`scripts/jd_customer_service_export_diagnostics.py`
- 输入样例：`examples/prepare_request.example.json`
- 回复样例：`examples/generate_reply.example.json`
- 配置模板：`config/default.json`
- Continuity 适配器：`app/continuity_adapter.py`

## 脚本用法
```bash
python3 skills/ecommerce-customer-workflow/scripts/validate_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/prepare_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/generate_reply.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/jd_customer_service_start.py '<JSON>'
```

## Continuity 适配器

```python
from app.continuity_adapter import check_and_compress_context

result = check_and_compress_context(history, max_tokens=200000)
if result["compressed"]:
    history = result["history"]
```

## prepare_request 成功输出示例
```json
{
  "ok": true,
  "prepared": {
    "shop_id": "shop_001",
    "session_id": "sess_001",
    "source_type": "url",
    "source_value": "https://item.jd.com/1001.html",
    "product_ref": {
      "type": "product_id",
      "value": "1001"
    },
    "user_message": "这款黑色还有吗？",
    "page_context": {},
    "parsed_entities": [],
    "knowledge_hits": {
      "catalog": [],
      "faq": [],
      "rules": []
    }
  },
  "action_plan": ["review_prepared_request", "generate_reply"]
}
```

## generate_reply 成功输出示例
```json
{
  "ok": true,
  "reply_draft": "您好，结合当前可确认的信息，先为您整理如下：...",
  "reply_reasoning_summary": "基于本地商品/FAQ/规则命中结果生成保守回复草稿",
  "facts_used": ["catalog:title", "faq:matched_line"]
}
```

## jd_customer_service_start 成功输出边界
```json
{
  "ok": true,
  "reply": {},
  "fill_action": {
    "send_policy": "manual_only",
    "auto_send_allowed": false
  }
}
```

## 当前未实现项
- 真实 Windows UIA backend
- 真实文本填充
- 自动发送客服消息
- 浏览器自动化主线
- 淘宝支持
- 实时联网抓取商品详情
- 完整 RAG
- OpenClaw runtime hook
