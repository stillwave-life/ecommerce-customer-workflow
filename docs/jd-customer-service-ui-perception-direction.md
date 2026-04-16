# 京东客服 UI 感知层方向设计

## 1. 文档目的

本文档定义 `ecommerce-customer-workflow` 下一阶段的 UI 感知层方向方案。目标是在现有 Phase A 已完成的 `desktop_context -> prepared -> reply -> fill_action` 骨架之上，补齐“真实京东客服工作台界面 -> desktop_context”的生产链路。

本文档只解决方向、分层、模块职责、输入输出边界与技术路线，不直接展开逐步编码实施细节。

---

## 2. 设计目标

下一阶段目标不是继续增强回复生成本身，而是构建一个能够从真实京东客服工作台界面中提取结构化上下文的 UI 感知层。

目标系统应能完成：

1. 探测当前活动窗口
2. 判断当前是否为京东客服工作台
3. 读取 UI Automation / Accessibility tree
4. 从可访问控件中识别聊天区、商品区、用户/订单区、输入区
5. 将识别结果组装成标准 `desktop_context`
6. 将 `desktop_context` 交给现有 Phase A 链路继续处理

---

## 3. 推荐技术路线

推荐采用：

> UI Automation / Accessibility 优先，OCR 作为兜底，坐标点击不是主通路。

这是当前阶段最稳的路线，原因如下：

- 京东客服后台界面结构较规整，存在明显区域与控件层级
- 若可访问控件可读，文字提取与按钮状态判断会比纯 OCR 更稳定
- 输入框聚焦、发送按钮存在性、可编辑性等属性天然适合 UI Automation 读取
- OCR 更适合在控件文本缺失或图片消息存在时补足，而不是承担主链路

因此：

- **主通路**：UI Automation / Accessibility
- **辅助兜底**：OCR / screenshot
- **最后手段**：坐标级点击或固定区域补丁

---

## 4. 总体数据流

推荐数据流如下：

```text
当前活动窗口
  -> window_probe
  -> ui_tree_reader
  -> region_classifier
  -> jd_workspace_parser
  -> desktop_context
  -> launcher
  -> prepare_mapper
  -> reply_composer
  -> fill_action
```

这意味着下一阶段只新增左半段能力，不重写右半段 Phase A 既有链路。

---

## 5. 分层设计

### 5.1 窗口探测层 `window_probe`

职责：

- 获取当前活动窗口
- 读取窗口标题、进程名、大小、前台状态
- 输出平台识别初判
- 产出“是否疑似京东客服工作台”的初步置信度

它只回答：

- 当前窗口是不是候选目标
- 是否值得继续做深度解析

它不负责：

- 业务理解
- 回复生成
- 页面动作

---

### 5.2 可访问树读取层 `ui_tree_reader`

职责：

- 读取 UI Automation / Accessibility tree
- 拉取节点文本、控件类型、层级关系、bounds、可编辑性、可点击性
- 输出统一节点列表或树结构

它是 UI 感知层的原始数据来源。

它只回答：

- 页面上有哪些控件
- 每个控件具有什么结构信息

它不负责：

- 哪些节点属于聊天区
- 哪些文本是商品信息
- 哪些字段应进入 `desktop_context`

---

### 5.3 区域分类层 `region_classifier`

职责：

- 将原始节点划分为逻辑区域
- 输出会话列表区、聊天区、商品区、用户/订单区、输入区等区域结果

推荐输出区域：

- `conversation_list_region`
- `chat_region`
- `product_region`
- `user_order_region`
- `input_region`
- `send_button_region`

这是结构解释层，是 UI 感知链路里最关键的模块之一。

它只回答：

- 哪些节点属于哪个区域

它不回答：

- 客户到底问了什么
- 商品 SKU 是多少
- 应该回复什么

---

### 5.4 京东工作台解析层 `jd_workspace_parser`

职责：

- 从分类后的区域中提取当前客服上下文
- 生成标准 `desktop_context`

必须提取：

- `platform`
- `confidence`
- `active_customer`
- `chat_context`
- `product_context`
- `user_order_context`
- `input_context`

它负责从“界面结构”走向“业务上下文”，但仍然不涉及回复生成。

---

### 5.5 OCR 兜底层 `ocr_fallback`

职责：

- 当 UI Automation 无法拿到关键字段时，对特定区域截图并做 OCR
- 补足聊天文本、商品标题、订单摘要等缺失字段

触发条件建议为：

- `chat_context.latest_customer_message` 为空
- 商品卡片标题缺失
- 用户/订单区信息缺失但区域存在
- 输入区文本或按钮状态无法从控件树确认

OCR 是兜底层，不应成为第一实现的主依赖。

---

## 6. 下一阶段与 Phase A 的关系

下一阶段必须严格复用现有 Phase A 合约，而不是另起炉灶。

已存在且必须复用的对象：

- `app/desktop/context.py`
- `app/desktop/prepare_mapper.py`
- `app/desktop/reply_composer.py`
- `app/desktop/fill_action.py`
- `app/desktop/launcher.py`
- `scripts/jd_customer_service_start.py`

也就是说：

- UI 感知层的终点是 `desktop_context`
- 不是直接生成回复
- 不是直接操作输入框
- 不是绕过 Phase A

---

## 7. 推荐的模块边界

建议新增目录层次如下：

```text
app/desktop/
  context.py
  prepare_mapper.py
  reply_composer.py
  fill_action.py
  launcher.py
  perception/
    window_probe.py
    ui_tree_reader.py
    region_classifier.py
    jd_workspace_parser.py
    ocr_fallback.py
```

边界约束：

- `perception/` 只负责真实界面到 `desktop_context`
- 现有 `desktop/` 根目录模块继续负责 `desktop_context` 之后的链路

这样可以让“感知层”和“业务层”清晰分开。

---

## 8. 输入输出契约建议

### 8.1 `window_probe` 输出

```json
{
  "ok": true,
  "window_title": "evw10158991",
  "process_name": "jd-workbench.exe",
  "window_bounds": [0, 0, 1680, 1048],
  "platform_hint": "jd_customer_service",
  "confidence": 0.82
}
```

### 8.2 `ui_tree_reader` 输出

```json
{
  "ok": true,
  "nodes": [
    {
      "role": "edit",
      "name": "输入框",
      "text": "",
      "bounds": [360, 690, 970, 1010],
      "editable": true,
      "clickable": true,
      "children": []
    }
  ]
}
```

### 8.3 `region_classifier` 输出

```json
{
  "ok": true,
  "regions": {
    "conversation_list_region": [],
    "chat_region": [],
    "product_region": [],
    "user_order_region": [],
    "input_region": [],
    "send_button_region": []
  }
}
```

### 8.4 `jd_workspace_parser` 输出

最终必须符合现有 `desktop_context` 契约：

```json
{
  "platform": "jd_customer_service",
  "confidence": 0.91,
  "active_customer": {
    "id": "jd_4a3d4c80e30ef",
    "name": "jd_4a3d4c80e30ef"
  },
  "chat_context": {
    "latest_customer_message": "这款还有吗？",
    "recent_messages": [],
    "contains_image": true
  },
  "product_context": {
    "tab_active": true,
    "items": []
  },
  "user_order_context": {
    "user_labels": [],
    "orders": [],
    "service_forms": []
  },
  "input_context": {
    "editable": true,
    "has_smart_reply": true,
    "send_button_visible": true,
    "existing_text": ""
  }
}
```

---

## 9. 第一版识别范围

第一版 UI 感知层不追求“完整无误识别全部页面元素”，而追求“稳定地产出可用 `desktop_context`”。

第一版优先目标：

### 9.1 必须识别

- 当前是否为京东客服工作台
- 当前客户 ID / 名称
- 最近一条客户消息
- 输入框是否可编辑
- 发送按钮是否存在

### 9.2 尝试识别

- 商品标题
- SKU
- 库存状态
- 用户标签
- 历史订单摘要
- 服务单上下文

### 9.3 识别失败时的原则

- 返回空结构，不猜测
- 不阻塞主链路
- 允许回复层走保守澄清策略

这与当前项目“事实不足时保守回复”的设计完全一致。

---

## 10. 置信度与阻断策略

下一阶段必须显式引入置信度概念。

推荐：

- `window_probe` 给窗口级置信度
- `region_classifier` 给区域级置信度
- `jd_workspace_parser` 汇总为 `desktop_context.confidence`

使用原则：

- 高置信度：允许继续进入 `launcher`
- 低置信度：返回失败或人工审阅状态
- 不以低置信度结果直接驱动页面动作

这一步是后续“显式确认发送”与“受控自动化”的基础。

---

## 11. 测试策略建议

下一阶段应按三层测试组织：

### 11.1 单元测试

针对：

- `region_classifier`
- `jd_workspace_parser`
- 字段提取函数

输入应为模拟节点树或节点列表。

### 11.2 快照/样本测试

针对：

- 从实际京东后台样本导出的节点快照
- 若必要，再加截图样本配套 OCR 结果快照

目的是验证对真实界面结构的适配能力。

### 11.3 契约测试

针对：

- `desktop_context` 是否总能构造成合法结构
- 是否能被现有 `launcher -> prepare_mapper -> reply_composer` 消费

这类测试保证 UI 感知层不会破坏既有 Phase A 主链路。

---

## 12. 当前阶段明确不做

下一阶段仍明确不做：

- 自动发送
- 风控绕过
- 批量自动回复
- 无条件依赖 OCR 作为主链路
- 直接把坐标点击写死成第一实现
- 在 UI 感知层直接生成回复

这些都不属于 UI 感知层目标。

---

## 实现入口

UI 感知层第一版实现从结构化窗口探测结果、UI 节点列表和已分类区域输入开始，不直接连接真实 Windows UI Automation 后端。

这样可以先让解析管线保持确定性和可测试性，同时保留长期架构目标：未来真实 Windows UI Automation 适配器可以向 `window_probe`、`ui_tree_reader`、`region_classifier` 提供数据，而不需要修改下游 `jd_workspace_parser -> desktop_context -> launcher` 合同。

---

## 13. 结论

下一阶段应按以下方向推进：

> 以 UI Automation / Accessibility 为主通路，构建严格分层的 UI 感知层，把真实京东客服工作台界面稳定转换为 `desktop_context`，继续交由现有 Phase A 链路完成回复生成与填充动作准备。

这条路线与现有项目结构连续、风险可控、便于逐步增强，是当前最合适的下一步方向。
