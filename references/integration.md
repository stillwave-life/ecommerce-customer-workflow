# OpenClaw 接入说明

## 推荐接入方式
将本目录作为一个标准 skill 包放入 OpenClaw 的 skills 目录中，优先通过 `SKILL.md` 作为主入口，配合 `_meta.json`、`scripts/`、`references/`、`assets/`、`examples/` 提供说明与资源。

## 当前提供内容
- `SKILL.md`：skill 主入口与触发说明
- `_meta.json`：基础元数据
- `config/default.json`：配置模板
- `scripts/validate_request.py`：最小请求校验入口
- `scripts/prepare_request.py`：离线请求准备入口
- `scripts/generate_reply.py`：离线回复生成入口
- `references/`：架构、接入、模型移交文档
- `assets/`：请求样例与提示词资产
- `examples/`：可直接执行的示例输入

## 建议调用流程
1. OpenClaw 传入 `shop_id`、`session_id`、`source_type`、`source_value`、`user_message`
2. `scripts/prepare_request.py` 完成输入归一化、URL/图片解析和本地知识补齐
3. 上层运行时人工审核 `prepared` 结果
4. `scripts/generate_reply.py` 基于 `prepared` 输出保守客服回复草稿

## 最小脚本示例
```bash
python3 skills/ecommerce-customer-workflow/scripts/prepare_request.py '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://item.jd.com/1001.html","user_message":"这款还有吗？"}'
python3 skills/ecommerce-customer-workflow/scripts/generate_reply.py '{"prepared": {...}}'
```

## UTF-8 输出说明
- 所有脚本会显式以 UTF-8 写入 stdout/stderr
- 运行时应在 UTF-8 终端环境下查看中文结果
- JSON 输出保持稳定，成功为 `{"ok": true, ...}`，失败为 `{"ok": false, "error": "..."}`

## 当前边界
当前 skill 只保证离线结构化补齐与回复草稿生成，不承诺以下能力：
- 京东后台浏览器自动化
- 自动发送客服消息
- 自动 RAG 检索
- 推荐引擎
- 平台 API 适配层
- 多轮会话 REPL
- OpenClaw runtime hook

## 与已验证模型的衔接
已验证可用能力是本地脚本 `F:/qwen2vl_train/LLaMA-Factory/scripts/ecom_cs_mvp_infer.py` 的单轮中文客服推理。后续如果要接入模型，应将该能力封装成可配置后端，再与本 skill 的 `prepared` / `reply_draft` 标准输入输出对接。
