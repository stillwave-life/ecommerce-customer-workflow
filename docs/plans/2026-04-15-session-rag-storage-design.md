# 会话级临时 RAG 存储设计

## 目标

本设计用于 `ecommerce-customer-workflow` 的下一阶段：实现一个带生命周期管理的会话级临时 RAG 存储系统。

系统目标不是构建永久用户画像，也不是全局知识库，而是在人工客服接管窗口内：

1. 记录客户与客服的对话消息
2. 从对话中抽取结构化记忆
3. 在用户表达模糊时检索当前会话历史记忆
4. 将检索结果转成约束条件
5. 用约束条件限制客服回复草稿
6. 会话结束后停止检索，并按策略释放或归档数据

---

## 设计结论

采用方案 B：结构化记忆 + 检索召回 + 约束层。

同时采用双后端存储：

- CSV：默认兼容模式，适合无数据库环境、本地演示和快速试用
- PostgreSQL：正式部署模式，后续可接 pgvector 实现完整向量检索

系统必须支持会话生命周期管理。RAG 存储只在人工接管窗口期内激活，会话结束后默认不再参与实时召回。

---

## 核心业务场景

客服工作流如下：

1. 客户进入人工客服流程
2. OpenClaw 开始检测当前人工会话
3. 检测谁发送了消息、发送了什么内容
4. 保存当前消息
5. 抽取记忆并更新约束
6. 如当前问题模糊，则检索当前会话历史记忆
7. 生成受约束的客服回复草稿
8. 人工客服审核或修改
9. 当前人工窗口结束后，会话关闭，RAG 实时检索停止

---

## 存储后端

### CSV 模式

CSV 模式是默认兼容模式。

用途：

- 客户没有 PostgreSQL
- 本地离线测试
- 快速演示
- 验证完整链路

CSV 模式必须支持：

- 消息存储
- 记忆存储
- 约束快照存储
- 会话状态存储
- 当前 session 内的基础检索

CSV 模式不要求实现真正向量索引。第一版可以使用：

- 最近消息优先
- 关键词重叠
- 实体重叠
- 简单文本相似度

### PostgreSQL 模式

PostgreSQL 是正式部署模式。

用途：

- 多会话稳定存储
- 更可靠查询
- 后续接 pgvector
- 生产环境扩展

PostgreSQL 模式必须支持：

- 会话、消息、记忆、约束入库
- 按 session 查询
- 会话状态过滤
- embedding 字段预留
- pgvector 初始化和配置路径预留

第一版允许 PostgreSQL 先使用文本相似检索，但架构不能写死，必须保留向量检索接口。

---

## 配置设计

`config/default.json` 应增加存储配置：

```json
{
  "storage_backend": "csv",
  "storage": {
    "csv": {
      "base_dir": "data/memory_store",
      "retention_days": 7
    },
    "postgres": {
      "host": "localhost",
      "port": 5432,
      "database": "ecommerce_customer_workflow",
      "user": "postgres",
      "password": "",
      "retention_days": 7,
      "enable_pgvector": false
    }
  }
}
```

默认使用 `csv`，避免客户必须先安装 PostgreSQL。

---

## 数据模型

### 会话

会话用于描述一个人工客服窗口期。

字段：

- `id`
- `shop_id`
- `session_id`
- `customer_id`
- `status`
- `started_at`
- `last_message_at`
- `ended_at`
- `expires_at`

`status` 可选值：

- `active`
- `closed`
- `expired`

### 消息

消息用于保存每轮原始对话。

字段：

- `id`
- `shop_id`
- `session_id`
- `role`
- `message_text`
- `source_type`
- `source_value`
- `parsed_entities`
- `created_at`

`role` 第一版支持：

- `customer`
- `agent`
- `system`

### 记忆

记忆是从消息中抽取出的可复用信息单元。

字段：

- `id`
- `shop_id`
- `session_id`
- `message_id`
- `memory_type`
- `memory_text`
- `memory_payload`
- `embedding`
- `confidence`
- `created_at`

第一版 `memory_type`：

- `product_fact`
- `sku_fact`
- `spec_fact`
- `issue_fact`
- `after_sales_fact`
- `shipping_fact`
- `preference_fact`
- `open_question`
- `resolved_fact`

### 约束快照

约束快照表示当前会话可用于生成回复的状态。

字段：

- `id`
- `shop_id`
- `session_id`
- `constraint_key`
- `constraint_value`
- `status`
- `source_memory_id`
- `updated_at`

`status` 可选值：

- `confirmed`
- `candidate`
- `conflicted`
- `unknown`

---

## 生命周期管理

RAG 存储不是永久激活。它必须跟随人工客服会话生命周期。

### 状态流转

1. 转人工后创建或恢复 session
   - `status = active`
   - `started_at = now`

2. 每次收到消息
   - 写入消息
   - 更新 `last_message_at`
   - 抽取记忆
   - 更新约束

3. 会话结束
   - `status = closed`
   - `ended_at = now`
   - `expires_at = now + retention_days`

4. 到期清理
   - `status = expired`
   - 或归档 / 删除消息、记忆、约束

### 实时检索规则

实时回复生成只能检索：

- 当前 `session_id`
- 当前 `shop_id`
- `status = active`

已关闭或过期会话默认不参与实时召回。

---

## 写入链路

每次新消息进入后：

1. 校验输入
2. 解析 source
3. 确保 session 处于 active
4. 保存原始消息
5. 抽取结构化记忆
6. 保存记忆
7. 如是 PostgreSQL + pgvector 模式，则生成并保存 embedding
8. 更新 session constraints
9. 更新 `last_message_at`

---

## 读取链路

当用户当前问题需要上下文时：

1. 判断是否触发记忆检索
2. 读取 active session 的约束快照
3. 在当前 session 内检索相关记忆
4. 合并当前输入、历史记忆、约束快照
5. 输出 constraints
6. 将 constraints 传给回复生成器

---

## 模糊问题触发条件

第一版至少支持以下触发条件：

- 当前消息包含：这个、那个、之前、刚才、上次、继续、还是
- 当前消息缺少商品、型号、规格等关键实体
- 当前消息依赖前文才有意义
- 当前输入与已有约束存在冲突可能

---

## 约束输出结构

建议 `prepared` 中增加：

```json
{
  "memory_hits": [],
  "constraints": {
    "confirmed": [],
    "candidate": [],
    "conflicted": [],
    "missing": [],
    "forbidden_claims": []
  },
  "reply_strategy": ""
}
```

`constraints` 是回复生成的直接依据。

---

## 模块拆分

新增模块：

```text
app/db/
  postgres.py

app/memory/
  memory_extractor.py
  memory_repository.py
  csv_memory_repository.py
  postgres_memory_repository.py

app/vector/
  embedding_service.py
  vector_repository.py
  fallback_memory_searcher.py

app/constraints/
  constraint_builder.py
```

现有文件调整：

- `scripts/prepare_request.py`
  - 增加消息持久化、记忆抽取、约束生成、记忆检索

- `scripts/generate_reply.py`
  - 读取 `memory_hits`、`constraints`、`reply_strategy`

- `app/reply/reply_builder.py`
  - 改成基于约束的回复策略与文案生成

- `app/data/knowledge_loader.py`
  - 第一版保留现有逻辑，后续可接收 constraints 优化命中

---

## PostgreSQL 安装与升级路径

默认不要求客户安装 PostgreSQL。

正式部署时提供 PostgreSQL 路径：

1. 安装 PostgreSQL
2. 创建数据库 `ecommerce_customer_workflow`
3. 执行初始化 SQL
4. 如需要向量检索，安装 pgvector
5. 配置 `storage_backend = postgres`
6. 配置数据库连接参数
7. 重启或重新运行 skill

第一版应提供初始化 SQL，但不能让 CSV 模式依赖它。

---

## 第一版不做

第一版明确不做：

- 跨 session 召回
- 跨客户长期画像
- 全局长期记忆
- 复杂知识图谱
- 自动摘要压缩
- 多向量库支持
- 市场/竞品知识库
- 回复风格自动学习
- 自动发送消息

---

## 验收标准

### 1. 消息可持久化
连续输入多轮消息后，能在 CSV 或 PostgreSQL 中看到完整历史消息。

### 2. 记忆可抽取
输入：

- 我要黑色的
- 256G 也可以
- 如果黑色没货白色也行

系统能生成：

- `color = 黑色`
- `size = 256G`
- `fallback_color = 白色`

### 3. 模糊问题能触发检索
继续输入：

- 那这个呢？

系统能识别该问题依赖前文，并检索当前 active session 的历史记忆。

### 4. 检索结果能约束回复
如果约束缺失，回复应优先追问。

如果约束冲突，回复应提示确认。

不能在缺少事实时编造商品、库存、价格、发货、售后承诺。

### 5. 会话结束后不再实时召回
会话关闭后：

- 不再写入新记忆
- 不再参与实时检索
- constraints 冻结
- 到期后归档或删除

### 6. 双后端都可运行
同一业务流程下：

- `storage_backend = csv` 可运行
- `storage_backend = postgres` 可运行

允许检索能力不同，但接口和输出结构必须一致。
