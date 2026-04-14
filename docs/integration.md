# OpenClaw 接入说明

## 建议接入方式
将本目录作为一个统一 skill 包放入 OpenClaw 的 skills 目录中。

## 当前形态
当前提供的是：
- skill 说明
- 配置模板
- 请求示例
- 架构说明

## 推荐后续接入方式
1. OpenClaw 调用 skill 时传入 `shop_id`、`session_id`、`product_ref`、`user_message`
2. skill 内部根据商品上下文查结构化商品信息
3. 再拼接 FAQ / 规则知识
4. 最终交给模型生成客服回复

## 当前未实现项
- 自动导入器
- 自动 RAG 检索
- 推荐引擎
- 平台 API 适配层
