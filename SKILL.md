---
name: ecommerce-customer-workflow
description: 面向京东客服场景的离线 OpenClaw workflow skill，支持文本、京东商品 URL、本地图片路径输入，完成结构化补齐与可审核中文回复草稿生成。
metadata:
  openclaw:
    runtime: python
    entrypoints:
      - scripts/validate_request.py
      - scripts/prepare_request.py
      - scripts/generate_reply.py
---

# ecommerce-customer-workflow

这是一个面向 OpenClaw 的京东客服离线 workflow skill。当前版本聚焦离线 MVP：统一处理文本、京东商品 URL、本地图片路径输入，补齐本地商品与 FAQ/规则信息，并生成可审核的中文客服回复草稿。

## 使用时机
在以下场景触发：
- 需要根据京东商品 URL、商品截图或人工文本线索整理客服上下文
- 需要把商品资料、FAQ、售后规则、发货规则整理成统一结构
- 需要先生成保守、可审核的中文客服回复草稿
- 需要在不接入后台自动化的前提下先验证客服 workflow

## 当前工作流
1. 接收文本、京东商品 URL 或本地图片路径输入
2. 解析并生成统一 `prepared` 请求结构
3. 命中本地商品资料、FAQ、规则数据
4. 基于已命中的事实生成中文客服回复草稿
5. 信息不足时明确无法确认，不编造库存、价格、服务承诺或平台规则

## 当前已实现能力
- 标准 OpenClaw skill 目录结构
- 最小请求校验与标准化脚本
- 离线请求准备脚本 `scripts/prepare_request.py`
- 本地知识补齐与保守回复生成脚本 `scripts/generate_reply.py`
- 京东商品 URL 最小识别
- 本地图片路径输入与保守解析回退

## 资源导航
- 架构细节：`references/architecture.md`
- 接入说明：`references/integration.md`
- 已验证模型能力与边界：`references/model-handoff.md`
- 输入样例：`examples/prepare_request.example.json`
- 回复样例：`examples/generate_reply.example.json`
- 回复提示词资产：`assets/reply_prompt.txt`
- 配置模板：`config/default.json`

## 脚本用法
```bash
python3 skills/ecommerce-customer-workflow/scripts/validate_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/prepare_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/generate_reply.py '<JSON>'
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
    "page_context": {
      "url": "https://item.jd.com/1001.html",
      "hostname": "item.jd.com",
      "path": "/1001.html"
    },
    "parsed_entities": [
      {
        "type": "product_id",
        "value": "1001",
        "source": "url"
      }
    ],
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

## 当前未实现项
- 京东客服后台自动化
- 自动发送客服消息
- 淘宝支持
- 实时联网抓取商品详情
- 完整 RAG
- 多轮 REPL
- OpenClaw runtime hook
