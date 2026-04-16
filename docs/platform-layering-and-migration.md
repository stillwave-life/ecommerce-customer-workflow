# 平台分层与迁移路线说明

## 1. 文档目的

本文档用于说明 `ecommerce-customer-workflow` 当前与 OpenClaw skills 生态的关系，以及未来如何迁移为独立脚本、桌面工具或其他 AI Agent 可调用能力。

核心结论：

> 当前项目以 OpenClaw skill 作为第一宿主，但核心能力必须保持平台无关，避免被任何单一运行环境绑定。

---

## 2. 当前定位

当前项目仍然是 OpenClaw skills 生态中的一个京东客服 workflow skill。

它当前承担的角色是：

- 提供 OpenClaw 可识别的 skill 包结构
- 提供标准入口说明与资源组织
- 提供客服 workflow 的输入、准备、回复、填充动作合同
- 为后续桌面感知与真实后台辅助操作提供第一宿主

但项目真正有长期价值的部分，不是 OpenClaw 壳子本身，而是内部可复用能力层。

---

## 3. 分层原则

后续所有开发都应遵循以下分层原则：

```text
平台入口层
  -> 能力编排层
  -> UI 感知层
  -> 客服业务层
  -> 知识与回复层
  -> 动作合同层
```

其中：

- 平台入口层可以更换
- 能力编排层应尽量保持稳定
- UI 感知层不应依赖 OpenClaw
- 客服业务层不应依赖具体桌面软件
- 回复生成与动作合同必须保持可测试、可复用、可迁移

---

## 4. 当前 OpenClaw 宿主层

OpenClaw 当前主要承担：

- 触发入口
- skill 发现
- workflow 调度
- 用户口令进入点

例如当前目标口令：

> 京东客服启动

在 OpenClaw 中，这个口令可以映射到：

- `scripts/jd_customer_service_start.py`
- 或未来的 OpenClaw runtime hook
- 或更细分的 `jd-cs-launch` skill

OpenClaw 层不应该直接承载复杂业务逻辑。它只负责把请求转交给 `app/` 内部能力模块。

---

## 5. 平台无关核心能力层

当前已经形成的平台无关核心包括：

- `desktop_context`
- `prepared`
- `reply_draft`
- `facts_used`
- `fill_action`
- `constraints`
- `reply_strategy`

这些对象是未来迁移的关键。

只要外部系统能构造或消费这些结构，就可以接入本项目能力。

---

## 6. 推荐代码边界

建议长期保持以下边界：

```text
app/
  desktop/
    context.py
    launcher.py
    prepare_mapper.py
    reply_composer.py
    fill_action.py
    perception/
      window_probe.py
      ui_tree_reader.py
      region_classifier.py
      jd_workspace_parser.py
      ocr_fallback.py
  data/
  constraints/
  reply/
  parsers/

scripts/
  jd_customer_service_start.py
  prepare_request.py
  generate_reply.py
```

未来如果需要进一步平台化，可以再增加：

```text
app/integrations/
  openclaw/
  cli/
  desktop_app/
  mcp/
  agent_sdk/
```

注意：

- `app/desktop/perception/` 不应该调用 OpenClaw API
- `app/reply/` 不应该知道自己被 OpenClaw、CLI 还是其他 Agent 调用
- `scripts/` 可以作为薄入口，但不应堆积核心逻辑

---

## 7. 未来迁移路线

### 7.1 迁移为独立脚本

最简单的迁移方式是继续扩展 `scripts/`。

可能入口：

- `scripts/jd_customer_service_start.py`
- `scripts/scan_jd_workspace.py`
- `scripts/fill_jd_reply.py`

适用场景：

- 本地调试
- 单机使用
- 人工辅助客服
- 不依赖 OpenClaw 的最小版本

迁移成本低，因为当前核心能力已经在 `app/` 内，而不是写死在 OpenClaw skill 描述里。

---

### 7.2 迁移为桌面工具

后续可以把项目封装成桌面应用或托盘工具。

可能形态：

- 后台常驻进程
- 快捷键或语音口令触发
- 自动识别当前京东客服窗口
- 弹出候选回复面板
- 一键填充输入框
- 人工确认发送

适用场景：

- 长期真人客服辅助
- 非开发人员使用
- 更稳定的桌面产品化

该路线需要新增桌面 UI 与窗口权限管理，但不需要重写客服核心逻辑。

---

### 7.3 迁移为 MCP Server

可以将核心能力封装为 MCP 工具，让不同大模型客户端调用。

可能工具：

- `scan_jd_workspace`
- `parse_jd_context`
- `compose_jd_reply`
- `build_fill_action`

适用场景：

- Claude Desktop / Claude Code
- 其他支持 MCP 的 Agent 客户端
- 多模型协作

该路线适合长期生态化。

---

### 7.4 迁移为通用 AI Agent 工具集

未来也可以接入其他 Agent 框架。

可能宿主：

- Claude Agent SDK
- OpenAI Agents SDK
- LangGraph
- 自研 Agent 调度器
- FastAPI Agent 服务

迁移方式：

- 把 `app/` 内函数包装为工具函数
- 保持输入输出 JSON 契约不变
- 由外部 Agent 决定何时调用、如何串联

这种方式最灵活，但也最需要清晰的边界与协议文档。

---

## 8. 迁移时不应改变的核心协议

无论未来迁移到哪里，都应尽量保持以下协议不变：

### 8.1 `desktop_context`

表示从当前客服工作台界面识别出的上下文。

包括：

- 当前平台
- 置信度
- 当前客户
- 聊天上下文
- 商品上下文
- 用户/订单上下文
- 输入框上下文

### 8.2 `prepared`

表示客服回复生成前的标准请求对象。

包括：

- `shop_id`
- `session_id`
- `source_type`
- `source_value`
- `product_ref`
- `user_message`
- `knowledge_hits`
- `constraints`
- `reply_strategy`

### 8.3 `reply_draft`

表示可审核客服回复草稿。

必须继续包含：

- 回复文本
- 生成依据摘要
- 使用到的事实来源

### 8.4 `fill_action`

表示页面动作合同。

当前阶段必须保持：

- `send_policy = manual_only`
- `auto_send_allowed = false`
- 只允许填充，不允许自动发送

---

## 9. 当前不应做的事情

为了保持可迁移性，当前阶段不应做：

- 把核心逻辑写死在 OpenClaw skill 描述文件里
- 让 `app/` 内核心模块直接依赖 OpenClaw runtime
- 让 UI 感知层直接生成最终回复
- 让回复生成层直接控制鼠标键盘
- 为某一个 Agent 框架写死数据结构
- 在没有适配层的情况下引入平台专属 API

---

## 10. 推荐演进顺序

建议后续按以下顺序推进：

1. 继续完成 OpenClaw skill 版本
2. 保持 `app/` 作为平台无关核心
3. 补齐 UI 感知层
4. 增加 CLI 脚本入口
5. 再考虑桌面工具或 MCP Server
6. 最后再适配其他 Agent 框架

这样可以先保证当前目标落地，同时避免后续迁移成本过高。

---

## 11. 结论

本项目当前仍然是 OpenClaw skills 生态中的京东客服 workflow skill。

但它不应该被设计成只能在 OpenClaw 内运行。正确方向是：

> OpenClaw 是第一宿主，`app/` 是可迁移能力核心，`scripts/` 是轻量入口，未来可通过适配层迁移到独立脚本、桌面工具、MCP Server 或其他 AI Agent 框架。

只要后续继续保持“平台入口层”和“核心能力层”分离，这个项目就不会被 OpenClaw 绑定，可以自然演进为真正的软件化京东客服助手。
