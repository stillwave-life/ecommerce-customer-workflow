# 2026-04-15 Session RAG 修复交接文档

## 1. 背景与目标

当前项目只能定位为 **单轮离线演示版**。

已有 text/url/image 输入分流、本地 catalog/faq/rules 简单命中、约束构建纯函数、回复草稿纯函数和少量单元测试；但 session memory、CSV/PostgreSQL 存储、约束闭环、`reply_strategy` 派生、session 生命周期都没有在主链路中真正实现。

下一次任务目标不是继续写规划文档，而是按本文档补齐基础闭环，让项目从“字段看起来存在”变成“链路真实可运行”。

本次交接文档只保存事实、风险和执行顺序，不代表这些能力已完成。

## 2. 当前判定

- 当前是否可演示：是，仅限单轮离线演示。
- 当前是否可测试：是，但测试覆盖低。
- 当前是否可真实试运行：否。
- 当前是否可生产使用：否。

最容易误判为已完成的能力：

- `config/default.json` 中的 `features.rag = true`
- `config/default.json` 中的 `storage_backend = csv/postgres` 配置
- `app/models.py` 中的 `memory_hits/constraints/reply_strategy/session_status` 字段
- `docs/plans/2026-04-15-session-rag-storage-design.md` 中“双后端可运行”的表述

## 3. 已验证现状

### 3.1 输入校验与规范化

已完成最小请求校验。

关键文件：

- `scripts/validate_request.py`
- `scripts/prepare_request.py`
- `app/models.py`

现状：

- 可校验 `shop_id/session_id/user_message` 是否为空。
- 非法 JSON 会返回错误。
- `source_type` 当前支持 `text/url/image`，但在 `scripts/prepare_request.py` 中硬编码，没有读取配置。

### 3.2 prepare_request 基础分流

关键文件：

- `scripts/prepare_request.py`

现状：

- `main()` 已完成基础 CLI 入口。
- `text` 输入进入文本路径。
- `url` 输入调用 `parse_product_url(...)`。
- `image` 输入调用 `parse_product_image(...)`。
- `load_knowledge_hits(...)` 已接入本地知识命中。

缺口：

- 没有初始化 memory repository。
- 没有保存 message。
- 没有 memory extraction。
- 没有 memory search。
- 没有调用 `build_constraints(...)`。
- 没有派生 `reply_strategy`。
- 没有写入或读取 `session_status`。
- 调用 `build_prepared_result(...)` 时没有传入 `memory_hits/constraints/reply_strategy/session_status`。

### 3.3 URL 解析

关键文件：

- `app/parsers/url_parser.py`

现状：

- 京东商品 URL 最小解析可用。
- 类似 `https://item.jd.com/1001.html` 可解析出 `product_ref = {"type": "product_id", "value": "1001"}`。

缺口：

- 不抓页面。
- 不读取登录态。
- 不查实时价格、库存、发货。

### 3.4 图片输入

关键文件：

- `app/parsers/image_parser.py`

现状：

- 只做图片路径存在性校验与保守结构化返回。

缺口：

- 没有 OCR。
- 没有商品识别。
- 没有规格/颜色/型号抽取。

### 3.5 本地知识命中

关键文件：

- `app/data/knowledge_loader.py`
- `app/data/catalog_loader.py`

现状：

- 可读取本地 `products.csv/faq.md/rules.md`。
- 可基于 product id、sku、实体候选做朴素字符串命中。

缺口：

- 没有字段级召回排序。
- 没有 product scope 严格隔离。
- FAQ/rules 只要字符串重叠就可能误命中。
- 这不是 session RAG。

### 3.6 constraints 纯函数

关键文件：

- `app/constraints/constraint_builder.py`
- `tests/constraints/test_constraint_builder.py`

现状：

- `build_constraints(...)` 存在。
- 可把同字段多值判为 `conflicted`。
- 可把必需字段缺失判为 `missing`。

缺口：

- 主链路没有调用。
- `forbidden_claims` 只有字段占位，没有真实规则来源和回复层执行。

### 3.7 reply 纯函数

关键文件：

- `app/reply/reply_builder.py`
- `tests/reply/test_reply_builder.py`

现状：

- `build_reply_draft(...)` 可消费手工传入的 `reply_strategy`。
- `ask_for_clarification`、`resolve_conflict`、`answer_with_context` 分支已有函数级测试。

缺口：

- 主链路不会生成 `reply_strategy`。
- 未知 `reply_strategy` 会静默退化到保守回复。
- `forbidden_claims` 未执行。

### 3.8 测试

现有测试：

- `tests/test_models.py`
- `tests/constraints/test_constraint_builder.py`
- `tests/reply/test_reply_builder.py`

当前测试可信度：低。

原因：

- 主要是纯函数测试。
- 未覆盖 CLI 端到端。
- 未覆盖文件 I/O。
- 未覆盖 session 生命周期。
- 未覆盖 CSV/PostgreSQL backend。
- 未覆盖配置错误路径。
- 未覆盖并发与损坏恢复。

## 4. 未完成清单

### P0 未完成

1. `app/memory/memory_repository.py`
   - repository 抽象不存在。
   - 缺少 `ensure_session/save_message/save_memories/load_constraints/replace_constraints/search_memories/close_session`。

2. `app/memory/csv_memory_repository.py`
   - CSV 后端不存在。
   - `config/default.json` 中的 `storage.csv.base_dir` 没有任何运行时代码使用。

3. `app/memory/memory_extractor.py`
   - 记忆抽取不存在。
   - text 输入无法抽取 `product_id/sku/model/color/size`。

4. `scripts/prepare_request.py` 编排闭环
   - 未接入 repository。
   - 未保存 message。
   - 未抽取 memories。
   - 未检索 memory hits。
   - 未构建 constraints。
   - 未派生 reply_strategy。
   - 未回写 constraints。
   - 未填充 session_status。

5. `tests/scripts/test_prepare_request.py`
   - CLI 主链路测试不存在。

6. `tests/memory/test_csv_memory_repository.py`
   - CSV 创建、读写、关闭 session、损坏/缺失文件、并发相关测试不存在。

### P1 未完成

1. PostgreSQL backend
   - `app/db/postgres.py` 不存在。
   - `app/memory/postgres_memory_repository.py` 不存在。
   - `references/postgres_init.sql` 不存在。
   - `tests/memory/test_postgres_memory_repository.py` 不存在。

2. `forbidden_claims` 执行
   - `constraints.forbidden_claims` 没有被回复层读取和执行。

3. 配置真实生效
   - `supported_source_types` 未从配置读取。
   - `storage_backend` 未控制运行路径。
   - `reply_policy` 未被回复层作为行为控制面。
   - `features.rag` 当前只是声明，不是已生效能力。

4. 文档去夸大
   - `docs/project-summary.md` 中“已完成离线 MVP”“可运行”需要改写。
   - `docs/plans/2026-04-15-session-rag-storage-design.md` 中“双后端都可运行”需要改写。
   - README 中 `features.rag=true` 相关描述需要明确为预留能力或本地字符串命中能力。

## 5. 下一次实施顺序

### P0-1：定义 repository 抽象

新增：

- `app/memory/__init__.py`
- `app/memory/memory_repository.py`

接口至少包含：

- `ensure_session(shop_id, session_id) -> dict`
- `save_message(shop_id, session_id, role, content, metadata) -> dict`
- `save_memories(shop_id, session_id, memories) -> list[dict]`
- `load_constraints(shop_id, session_id) -> list[dict]`
- `replace_constraints(shop_id, session_id, constraints) -> None`
- `search_memories(shop_id, session_id, query, limit) -> list[dict]`
- `close_session(shop_id, session_id) -> dict`

要求：

- repository 接口必须稳定，CSV 和 PostgreSQL 共享同一业务语义。
- 关闭 session 后禁止继续写入新 memory，且不参与实时召回。

### P0-2：实现 CSV repository

新增：

- `app/memory/csv_memory_repository.py`
- `tests/memory/test_csv_memory_repository.py`

建议文件：

- `sessions.csv`
- `messages.csv`
- `memories.csv`
- `constraints.csv`

最低要求：

- 首次运行可创建目录和 CSV。
- 可保存 session。
- 可保存 message。
- 可保存 memories。
- 可搜索 active session 的 memories。
- 可替换 constraints。
- 可关闭 session。
- closed session 不再参与召回。
- 文件缺失时可恢复为空表。
- 损坏文件要有明确失败或保守恢复策略，不能静默产出脏数据。

并发要求：

- 至少使用临时文件 + 原子替换，避免半行写入。
- 如果不做跨进程锁，文档必须明确 CSV 只适合单进程/本地演示。

### P0-3：实现 memory extractor

新增：

- `app/memory/memory_extractor.py`
- `tests/memory/test_memory_extractor.py`

最低抽取字段：

- `product_id`
- `sku`
- `model`
- `color`
- `size`

输出建议：

```json
{
  "memory_type": "constraint_fact",
  "memory_text": "客户提到黑色",
  "memory_payload": {
    "field": "color",
    "value": "黑色",
    "status": "candidate"
  }
}
```

要求：

- 与 `build_constraints(...)` 当前输入结构兼容。
- 先做可解释规则抽取，不要引入模型依赖。
- 不要过度抽象。

### P0-4：接通 prepare_request 主链路

修改：

- `scripts/prepare_request.py`

必须接入：

1. 读取 `config/default.json`。
2. 从配置读取 `supported_source_types`。
3. 按 `storage_backend` 初始化 repository。
4. `ensure_session(...)`。
5. `save_message(...)`。
6. `extract_memories(...)`。
7. `save_memories(...)`。
8. `search_memories(...)`。
9. `load_constraints(...)`。
10. `build_constraints(...)`。
11. 派生 `reply_strategy`。
12. `replace_constraints(...)`。
13. 将 `memory_hits/constraints/reply_strategy/session_status` 传给 `build_prepared_result(...)`。

`reply_strategy` 最小规则：

- 如果 `constraints.conflicted` 非空：`resolve_conflict`
- 否则如果 `constraints.missing` 非空：`ask_for_clarification`
- 否则如果 `memory_hits` 非空：`answer_with_context`
- 否则：`None` 或保守默认策略

### P0-5：补主链路测试

新增：

- `tests/scripts/test_prepare_request.py`

覆盖：

- happy path
- 缺 `shop_id`
- 缺 `session_id`
- 缺 `user_message`
- 非法 `source_type`
- 缺 `source_value`
- text 输入抽取 memory
- URL 输入命中 catalog
- memory conflict 派生 `resolve_conflict`
- missing constraint 派生 `ask_for_clarification`
- closed session 不召回

### P1-1：实现 PostgreSQL backend

新增：

- `app/db/postgres.py`
- `app/memory/postgres_memory_repository.py`
- `references/postgres_init.sql`
- `tests/memory/test_postgres_memory_repository.py`

最低要求：

- 可构建 DSN。
- 可初始化 schema。
- repository 方法与 CSV 后端同语义。
- 没有真实 PostgreSQL 环境时，测试至少覆盖 DSN/schema 生成；真实集成测试可通过环境变量启用。

在这些完成前，不要宣称 PostgreSQL 可运行。

### P1-2：执行 forbidden_claims

修改：

- `app/reply/reply_builder.py`
- `tests/reply/test_reply_builder.py`

要求：

- 回复层读取 `constraints.forbidden_claims`。
- 对库存、价格、发货、售后承诺类未验证声明做拦截或保守改写。
- 未知 `reply_strategy` 不应完全静默吞掉，至少要可测试地降级。

### P1-3：修正文档

修改：

- `README.md`
- `docs/project-summary.md`
- `docs/plans/2026-04-15-session-rag-storage-design.md`

要求：

- 把“已完成离线 MVP”改成“单轮离线演示版”。
- 把“双后端都可运行”改成“配置已预留，主线未实现”。
- 把 `features.rag = true` 解释为规划/预留，或改成与实际一致的配置。
- 明确当前只是本地字符串命中，不是 session RAG。

## 6. 关键文件清单

下一次重点读这些文件：

- `scripts/prepare_request.py`
- `scripts/generate_reply.py`
- `app/models.py`
- `app/data/knowledge_loader.py`
- `app/data/catalog_loader.py`
- `app/parsers/url_parser.py`
- `app/parsers/image_parser.py`
- `app/constraints/constraint_builder.py`
- `app/reply/reply_builder.py`
- `config/default.json`
- `tests/test_models.py`
- `tests/constraints/test_constraint_builder.py`
- `tests/reply/test_reply_builder.py`

下一次预计新增这些文件：

- `app/memory/__init__.py`
- `app/memory/memory_repository.py`
- `app/memory/csv_memory_repository.py`
- `app/memory/memory_extractor.py`
- `tests/memory/test_csv_memory_repository.py`
- `tests/memory/test_memory_extractor.py`
- `tests/scripts/test_prepare_request.py`
- `app/db/postgres.py`
- `app/memory/postgres_memory_repository.py`
- `references/postgres_init.sql`
- `tests/memory/test_postgres_memory_repository.py`

## 7. 验收标准

只有同时满足以下条件，才允许把项目状态从“单轮离线演示版”升级：

- message 存储已闭环。
- memory 抽取已闭环。
- memory 检索已闭环。
- constraints 已在 `prepare_request.py` 中真实生成。
- `reply_strategy` 已在主链路真实派生。
- reply 层能按策略生成澄清、冲突确认、上下文回复。
- session close 后不再实时召回。
- 至少 CSV 后端真实可运行。
- PostgreSQL 如被声明可运行，必须有实现、初始化 SQL 和测试。
- 文档表述与代码状态一致。

## 8. 必跑验证

### 单元测试

```bash
python -m pytest tests/test_models.py -v
python -m pytest tests/constraints/test_constraint_builder.py -v
python -m pytest tests/reply/test_reply_builder.py -v
python -m pytest tests/memory/test_csv_memory_repository.py -v
python -m pytest tests/memory/test_memory_extractor.py -v
python -m pytest tests/scripts/test_prepare_request.py -v
```

如实现 PostgreSQL：

```bash
python -m pytest tests/memory/test_postgres_memory_repository.py -v
```

### 全量测试

```bash
python -m pytest -q
```

### CLI 验证

至少验证：

- text 输入可生成 memory 或合理澄清策略。
- URL 输入仍能命中 catalog。
- 冲突 memory 可生成 `reply_strategy = resolve_conflict`。
- 缺失必需字段可生成 `reply_strategy = ask_for_clarification`。
- closed session 不参与 `memory_hits`。

## 9. 风险排序

1. session memory 存储不存在，真实多轮对话会立即失败。
2. PostgreSQL 是伪配置，切换后不可用。
3. `memory_hits/constraints/reply_strategy` 字段存在但主链路不生成，会误导上层。
4. text 输入缺少实体抽取，自然语言场景几乎无法命中。
5. 知识检索是朴素 substring，存在误召回风险。
6. `forbidden_claims` 不执行，未来规则约束可能失效。
7. session 生命周期不存在，关闭后召回/写入边界失效。
8. CSV 并发与损坏恢复未设计。
9. 测试覆盖太窄，不能证明真实可运行。
10. 文档混写计划能力和现有能力，容易导致错误上线或错误承诺。

## 10. 执行注意事项

- 不要把 `.worktrees/session-rag-storage/` 下的实验实现直接复制到主线；必须逐文件核对、重跑测试。
- 不要在没有实现 PostgreSQL 前继续写“双后端可运行”。
- 不要用当前 `5 passed` 证明项目可以真实试运行。
- 不要先做 OCR、浏览器自动化或插件；当前 P0 是 session memory、存储和测试闭环。
- 不要继续新增宏大规划文档；下一次应直接进入实现。
- 如需提交，提交前必须确认是否包含用户已有未提交改动。
