# Windows UI Automation 适配层方向设计

## 1. 文档目的

本文档定义 `ecommerce-customer-workflow` 下一阶段的 Windows UI Automation 适配层方向方案。目标是在现有 UI 感知层与 Phase A 已有链路之上，引入真实 Windows 窗口与可访问控件树的读取能力，并在不执行填充和发送的前提下，验证输入框可聚焦能力。

本文档解决的是方向、模块职责、数据边界与动作边界，不展开逐步编码细节。

---

## 2. 目标定义

这一阶段的目标不是直接做“真实自动回复”，而是做一个真实系统适配桥接层，使系统能够：

1. 读取当前活动窗口
2. 判断是否疑似京东客服工作台
3. 读取真实 Windows UI Automation / Accessibility tree
4. 转换为当前 perception pipeline 可消费的节点结构
5. 继续产出标准 `desktop_context`
6. 定位输入框并尝试聚焦
7. 返回聚焦结果

当前阶段明确不做：

- 自动填充输入框
- 自动点击发送
- 自动批量切换会话
- 直接依赖 OCR 作为主通路

---

## 3. 推荐技术路线

推荐采用：

> 真实 Windows UI Automation 读取为主，输入框聚焦能力独立为动作层，OCR 仍然作为后续兜底，不在本阶段主通路内承担核心职责。

原因：

- 当前 perception pipeline 已能消费结构化节点与区域信息
- 现阶段最缺的不是业务逻辑，而是真实系统数据入口
- 输入框聚焦是最安全、最必要的第一动作能力
- 读取与聚焦分层可以避免过早把动作能力和解析能力耦死

---

## 4. 总体架构位置

推荐数据流如下：

```text
真实当前活动窗口
  -> windows_window_probe
  -> windows_ui_tree_adapter
  -> region_classifier
  -> jd_workspace_parser
  -> desktop_context
  -> launcher / prepare_mapper / reply_composer / fill_action

同时：
  -> windows_input_focus
  -> focus_result
```

解释：

- `desktop_context` 仍然是主输出
- `focus_result` 是动作能力输出
- 聚焦结果不改变 `desktop_context` 结构
- 聚焦成功也不意味着允许填充或发送

---

## 5. 推荐模块拆分

### 5.1 `windows_window_probe`

职责：

- 读取当前前台窗口
- 获取窗口标题、句柄、进程名、bounds、是否激活
- 输出平台候选识别结果

它只回答：

- 当前是不是值得解析的目标窗口

它不负责：

- 读取控件树
- 分类区域
- 聚焦输入框

---

### 5.2 `windows_ui_tree_adapter`

职责：

- 从真实 Windows UI Automation API 中读取控件树
- 将原始控件对象转换为标准化节点结构

建议标准化字段包括：

- `role`
- `name`
- `text`
- `bounds`
- `editable`
- `clickable`
- `visible`
- `children`
- 必要时的 `automation_id` / `control_type`

它只负责“真实系统控件 -> 标准节点”的转换。

---

### 5.3 `windows_region_input_builder`

职责：

- 对接真实节点与现有 `region_classifier`
- 补充必要的 `region_hint` 或结构提示
- 保证真实 Automation 节点能进入现有 perception pipeline

它不负责：

- 回复逻辑
- fill action
- send action

---

### 5.4 `windows_input_focus`

职责：

- 在真实 UI Automation 节点中定位输入框
- 判断输入框是否可聚焦
- 执行 focus
- 返回聚焦结果

建议输出：

```json
{
  "ok": true,
  "focused": true,
  "target_role": "edit",
  "target_name": "输入框",
  "reason": ""
}
```

如果失败，应明确说明失败原因，例如：

- `input_box_not_found`
- `input_box_not_focusable`
- `focus_api_failed`

---

### 5.5 `windows_perception_bridge`

职责：

- 串联：
  - `windows_window_probe`
  - `windows_ui_tree_adapter`
  - `region_classifier`
  - `jd_workspace_parser`
  - `windows_input_focus`
- 生成统一桥接结果

建议输出包括：

- `probe_result`
- `desktop_context`
- `focus_result`

---

## 6. 与现有系统的边界关系

这一阶段必须严格遵守以下边界：

### 6.1 不重写 perception 解析层

不应重写：

- `region_classifier`
- `jd_workspace_parser`
- `desktop_context` 契约

真实 Windows 适配层的职责是：

> 给这些模块提供真实输入，而不是替代它们。

### 6.2 不重写 Phase A 回复链路

不应重写：

- `launcher`
- `prepare_mapper`
- `reply_composer`
- `fill_action`

真实 Windows 适配层的职责不是生成回复，而是让真实界面能进入既有回复链路。

### 6.3 动作能力独立

聚焦输入框能力必须与填充动作能力分离。

当前阶段允许：

- 找输入框
- 聚焦输入框
- 验证聚焦成功

当前阶段不允许：

- 自动写入文本
- 自动点击发送

---

## 7. 第一版实现范围

### 7.1 必须实现

- 真实当前窗口探测
- 真实 UI Automation 节点标准化输出
- 与 `region_classifier` 的桥接
- 与 `jd_workspace_parser` 的桥接
- 输入框定位
- 输入框聚焦
- 聚焦结果输出

### 7.2 可以延后实现

- OCR 真实接入
- 多窗口枚举
- 后台窗口切换
- 输入框文本回读
- 复杂商品面板多状态细化
- 多会话列表自动切换

---

## 8. 置信度与动作安全边界

这一阶段仍必须保留置信度控制：

- `windows_window_probe` 给窗口级置信度
- 真实节点桥接后沿用 perception 层已有置信度机制
- 当窗口置信度不足时，不应继续做聚焦动作
- 当输入框识别不稳定时，不应强行执行 focus

动作安全边界原则：

- 识别失败时宁可返回失败，不要猜
- 聚焦失败时宁可退出，不要转向坐标硬点
- 自动写入和自动发送仍然禁止

---

## 9. 推荐测试策略

### 9.1 适配器单元测试

测试真实适配器输出的标准字段结构是否符合预期。

### 9.2 桥接集成测试

验证真实适配输出能够进入：

- `region_classifier`
- `jd_workspace_parser`
- `launcher`

### 9.3 动作测试

验证：

- 输入框能被定位
- 可聚焦时返回 `focused = true`
- 不可聚焦时返回明确失败原因

### 9.4 不做的测试

当前阶段不做：

- 自动填充测试
- 自动发送测试
- 批量会话遍历测试

---

## 10. 与未来阶段的关系

这个 Windows UI Automation 适配层完成后，系统将从：

> 结构化样本驱动的 UI 感知层

升级为：

> 能读取真实 Windows 窗口与真实控件树的桌面客服助手

但它仍然只是“真实读取 + 聚焦”阶段，不代表已经进入“真实写入 + 发送”阶段。

后续路线应是：

1. 真实读取
2. 真实聚焦
3. 真实填充
4. 人工确认发送
5. 显式受控发送

不能跳步骤。

---

## 实现入口

Windows UI Automation 适配层第一版从结构化前台窗口结果、标准化 Automation 节点和显式 focus result 合同开始，不直接连接真实 Windows UI Automation API。

这样可以让适配层先保持确定性与可测试性，同时保留长期架构目标：未来真实 Windows Automation backend 可以向 `windows_window_probe`、`windows_ui_tree_adapter`、`windows_input_focus` 提供数据，而无需改变下游 `region_classifier -> jd_workspace_parser -> launcher` 的合同。

---

## 11. 结论

下一阶段应按以下方向推进：

> 在保持 perception pipeline 与 Phase A 既有链路不变的前提下，新增一个严格分层的 Windows UI Automation 适配层，把真实当前窗口与真实控件树转换为标准节点输入与 `desktop_context`，并增加输入框聚焦能力作为第一动作能力。

这一步是系统从“可测试骨架”走向“真实后台环境接入”的关键桥梁，同时仍保持动作边界安全可控。
