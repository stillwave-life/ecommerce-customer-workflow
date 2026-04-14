# 架构说明

## 目标
把京东客服离线能力抽象成可复用的 OpenClaw workflow skill，而不是某个店铺的私有脚本。

## 核心分层
1. 输入准备层
2. URL / 图片解析层
3. 本地商品与知识补齐层
4. 回复生成层

## 当前最小能力
- 接受 `shop_id`、`session_id`、`source_type`、`source_value`、`user_message`
- 兼容旧的 `product_ref` 输入
- 对文本、京东商品 URL、本地图片路径进行统一归一化
- 基于本地商品、FAQ、规则生成统一 `prepared` 结构
- 基于事实生成保守中文客服回复草稿
- 信息不足时明确无法确认，不编造库存、价格、规则或服务承诺

## 已验证内容
- `scripts/validate_request.py` 可继续作为最小校验入口
- `scripts/prepare_request.py` 可作为离线请求准备入口
- `scripts/generate_reply.py` 可作为离线回复生成入口
- 中文编码输出保持 UTF-8

## 未验证或未实现内容
- 多轮 REPL
- 自动导入器
- FAQ/规则自动 RAG
- 推荐引擎
- 京东后台浏览器自动化
- 京东 API 或其他平台 API 适配
- OpenClaw runtime hook

## 与 LoRA 的关系
当前 skill 先提供离线 workflow 与接入骨架，不直接把 LoRA 推理作为标准入口依赖。后续可把 `ecom_cs_mvp_infer.py` 包装为可配置推理后端，再接入本 skill 的回复生成流程。

## 未来扩展方向
- 增强图片理解后端
- 浏览器执行层适配
- 显式确认后发送能力
- 向量检索与知识召回
- 多商家配置与权限隔离
- 会话状态管理
