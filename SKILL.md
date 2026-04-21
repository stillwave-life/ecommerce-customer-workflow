---
name: ecommerce-customer-workflow
description: 面向京东客服场景的 OpenClaw workflow 与桌面 assistant skill，支持离线客服上下文整理、保守回复草稿生成，以及京东客服工作台 desktop_context 合同链路。
metadata:
  openclaw:
    runtime: python
    entrypoints:
      - scripts/validate_request.py
      - scripts/prepare_request.py
      - scripts/generate_reply.py
      - scripts/jd_customer_service_start.py
      - scripts/jd_generate_reply_and_fill_ahk.py
---

# ecommerce-customer-workflow

这是一个面向 OpenClaw 的京东客服 skill。当前包含三条能力线：离线客服 workflow、京东客服桌面 assistant 合同链路，以及管理员环境下通过 AHK 执行的自动填充入口。

## 使用时机
在以下场景触发：
- 需要根据京东商品 URL、商品截图或人工文本线索整理客服上下文
- 需要把商品资料、FAQ、售后规则、发货规则整理成统一结构
- 需要生成保守、可审核的中文客服回复草稿
- 需要以 `desktop_context` 启动京东客服桌面 assistant，生成回复并准备人工发送前的填充动作
- 需要在管理员环境中对当前打开的京东咚咚窗口执行“生成回复 + AHK 自动填充”，但不自动发送

## 当前工作流
1. 离线 workflow：输入文本 / URL / 图片路径，输出 `prepared` 与 `reply_draft`
2. 桌面 assistant：输入已解析的 `desktop_context`，输出 `reply` 与 `fill_action`
3. AHK 填充入口：输入客户问题文本，输出 `reply_draft`、`fill_result`、截图证据与 `manual_only` 填充结果

## 当前已实现能力
- 标准 OpenClaw skill 目录结构
- 最小请求校验与标准化脚本
- 离线请求准备脚本 `scripts/prepare_request.py`
- 本地知识补齐与保守回复生成脚本 `scripts/generate_reply.py`
- 京东商品 URL 最小识别
- 本地图片路径输入与保守解析回退
- 京东客服桌面 assistant 合同入口 `scripts/jd_customer_service_start.py`
- 基于普通 `AutoHotkey64.exe` 的管理员填充脚本 `scripts/jd_fill_with_ahk.py`
- 生成回复并调用 AHK 填充的统一入口 `scripts/jd_generate_reply_and_fill_ahk.py`
- AHK 诊断输出：`diagnostics_path`、`after_input.png`、`run.json`

## 资源导航
- 架构细节：`references/architecture.md`
- 接入说明：`references/integration.md`
- 桌面 assistant 示例：`examples/jd_customer_service_start.example.json`
- 诊断导出脚本：`scripts/jd_customer_service_export_diagnostics.py`
- 输入样例：`examples/prepare_request.example.json`
- 回复样例：`examples/generate_reply.example.json`
- 配置模板：`config/default.json`

## 脚本用法
```bash
python3 skills/ecommerce-customer-workflow/scripts/validate_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/prepare_request.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/generate_reply.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/jd_customer_service_start.py '<JSON>'
python3 skills/ecommerce-customer-workflow/scripts/jd_generate_reply_and_fill_ahk.py '这款还有吗？'
```

## AHK 自动填充说明
- 必须在管理员 PowerShell 中运行调用链。
- 默认 AHK 路径为：`C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe`
- 当前只支持 `manual_only`，不会自动发送。
- `ok=true` / `executed=true` 仅代表 AHK 执行完成；是否真正填入以 `after_input.png` 和人工确认为准。

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

## jd_generate_reply_and_fill_ahk 成功输出边界
```json
{
  "ok": true,
  "reply_draft": "您好，目前我这边还无法确认您咨询的具体商品信息。您可以补充商品链接、商品截图，或提供型号/规格，我再帮您继续核实。",
  "fill_result": {
    "ok": true,
    "executed": true,
    "fill_visually_confirmed": false,
    "requires_manual_confirmation": true,
    "send_policy": "manual_only",
    "auto_send_allowed": false
  },
  "diagnostics_path": "...",
  "screenshots": {
    "after_input": "..."
  }
}
```

## 当前未实现项
- 自动发送客服消息
- 稳定的京东页面 OCR 主链路
- 直接 DOM / DevTools 接入
- 淘宝支持
- 实时联网抓取商品详情
- 完整 RAG
