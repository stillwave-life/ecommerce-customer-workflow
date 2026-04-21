# ecommerce-customer-workflow

面向京东客服场景的 OpenClaw workflow 与桌面 assistant skill。

这个项目的目标是先把“客服代理”的三条基础链路做扎实：
1. 把文本、京东商品 URL、本地图片路径统一整理成结构化客服上下文并生成保守回复草稿。
2. 接收 `desktop_context`，启动京东客服桌面 assistant，生成回复并准备人工发送前的填充动作。
3. 在管理员环境中，通过普通 `AutoHotkey64.exe` 调用本地 AHK 执行器，把生成的回复填入当前打开的京东咚咚窗口。

当前版本不是全自动客服机器人，也不会自动发送消息。最新可运行主线是：输入客户问题文本 → 生成保守回复 → 以管理员权限调用 AHK 执行填充 → 人工确认发送。

## 项目定位

`ecommerce-customer-workflow` 是一个可以放入 OpenClaw `skills` 目录的 skill 包。

它当前解决的问题是：

1. 客服输入来源不统一，需要统一成标准 JSON 上下文。
2. 商品资料、FAQ、售后规则散落在不同文件里，需要统一命中和补齐。
3. 客服回复不能瞎编，需要基于已有事实生成保守草稿。
4. 京东桌面工作台是封闭 CEF 界面，普通外部注入不稳定，需要通过管理员环境下的 AHK 本地执行器完成填充。

## 当前推荐主流程

```text
客户问题文本
        │
        ▼
scripts/jd_generate_reply_and_fill_ahk.py
        │
        ├─ 构造最小 desktop_context
        ├─ launch_desktop_assistant
        ├─ 生成 reply_draft
        └─ fill_with_ahk
                │
                ▼
管理员环境下 AHK 自动填充京东输入框
                │
                ▼
人工确认发送
```

## 已实现能力

### 1. OpenClaw skill 包结构

项目包含：

- `SKILL.md`
- `_meta.json`
- `scripts/`
- `app/`
- `config/`
- `references/`
- `examples/`
- `shops/`
- `assets/`
- `templates/`

可以作为一个独立 skill 包复制到 OpenClaw 的 `skills` 目录中。

### 2. 最小请求校验与离线准备

入口：

```text
scripts/validate_request.py
scripts/prepare_request.py
scripts/generate_reply.py
```

支持：
- `text`
- `url`
- `image`

输出统一的 `prepared` 结构与保守回复草稿。

### 3. 桌面 assistant 合同链路

入口：

```text
scripts/jd_customer_service_start.py
```

作用：
- 接收 `desktop_context`
- 生成 `reply`
- 生成 `fill_action`
- 始终保持：
  - `send_policy = manual_only`
  - `auto_send_allowed = false`

### 4. AHK 自动填充入口

核心脚本：

```text
scripts/jd_fill_with_ahk.py
scripts/jd_generate_reply_and_fill_ahk.py
scripts/jd_force_paste_ahk.ahk
```

当前约束：
- 必须在管理员 PowerShell 中运行
- 默认使用：
  - `C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe`
- 不自动发送
- 通过诊断目录输出截图与 run.json
- `ok=true` / `executed=true` 仅表示链路执行完成，不代表视觉确认已填入；需结合 `after_input.png` 人工确认

### 5. AHK 诊断证据链

每次运行会输出：
- `diagnostics_path`
- `before_full.png`
- `after_full.png`
- `after_input.png`
- `run.json`

用于人工确认输入框是否真正出现目标文本。

## 常用命令

### 离线回复

```bash
python scripts/prepare_request.py '{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","user_message":"这件还有吗？"}'
python scripts/generate_reply.py '{"prepared":{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","product_ref":{"type":"product_id","value":"1001"},"user_message":"这件还有吗？","page_context":{},"parsed_entities":[],"knowledge_hits":{"catalog":[],"faq":[],"rules":[]}}}'
```

### 桌面 assistant 合同入口

```bash
python scripts/jd_customer_service_start.py '{"command":"京东客服启动","shop_id":"shop_001","session_id":"desktop-session-1","desktop_context":{"platform":"jd_customer_service","confidence":0.9,"active_customer":{"id":"manual_user","name":"manual_user"},"chat_context":{"latest_customer_message":"这款还有吗？","recent_messages":[],"contains_image":false},"product_context":{"tab_active":false,"items":[]},"user_order_context":{"user_labels":[],"orders":[],"service_forms":[]},"input_context":{"editable":true,"has_smart_reply":false,"send_button_visible":true,"existing_text":""}}}'
```

### 管理员环境下直接 AHK 填充

```powershell
python scripts/jd_fill_with_ahk.py "测试填充123"
```

### 管理员环境下生成回复并填充

```powershell
python scripts/jd_generate_reply_and_fill_ahk.py "这款还有吗？"
```

## 演示与验收口径

- `ahk_executed=true`：Python/AHK 链路执行完成。
- `fill_visually_confirmed=false`：未经过截图或人工确认，不声称填充成功。
- 需要查看：
  - `after_input.png`
  - `after_full.png`
- 发送始终保留人工确认，不做自动发送。

## 当前未实现项

- 自动发送客服消息
- 稳定的京东页面 OCR 主链路
- 直接 DOM / DevTools 接入
- 淘宝支持
- 实时联网抓取商品详情
- 完整 RAG
├─ docs/
│  └─ plans/
├─ examples/
│  ├─ generate_reply.example.json
│  ├─ prepare_request.example.json
│  └─ request.json
├─ references/
│  ├─ architecture.md
│  ├─ integration.md
│  └─ model-handoff.md
├─ scripts/
│  ├─ generate_reply.py
│  ├─ prepare_request.py
│  └─ validate_request.py
├─ shops/
│  └─ default/
│     ├─ faq.md
│     ├─ products.csv
│     └─ rules.md
└─ templates/
   └─ reply_prompt.txt
```

## 快速开始

### 1. 复制到 OpenClaw skills 目录

把整个目录复制到：

```text
OpenClaw/skills/ecommerce-customer-workflow
```

确保不是只复制 `SKILL.md`，而是复制整个文件夹。

### 2. 测试最小校验入口

Windows：

```bash
py -3 scripts/validate_request.py "{\"shop_id\":\"shop_001\",\"session_id\":\"sess_001\",\"product_ref\":{\"type\":\"sku\",\"value\":\"SKU001\"},\"user_message\":\"这件黑色M码还有吗？\"}"
```

Linux / macOS：

```bash
python3 scripts/validate_request.py '{"shop_id":"shop_001","session_id":"sess_001","product_ref":{"type":"sku","value":"SKU001"},"user_message":"这件黑色M码还有吗？"}'
```

### 3. 测试京东 URL 输入

Windows：

```bash
py -3 scripts/prepare_request.py "{\"shop_id\":\"shop_001\",\"session_id\":\"sess_001\",\"source_type\":\"url\",\"source_value\":\"https://item.jd.com/1001.html\",\"user_message\":\"这款还有吗？\"}"
```

Linux / macOS：

```bash
python3 scripts/prepare_request.py '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://item.jd.com/1001.html","user_message":"这款还有吗？"}'
```

### 4. 测试文本输入

```bash
py -3 scripts/prepare_request.py "{\"shop_id\":\"shop_001\",\"session_id\":\"sess_001\",\"source_type\":\"text\",\"source_value\":\"黑色M码\",\"user_message\":\"这件还有吗？\"}"
```

### 5. 测试桌面 assistant 入口

```bash
py -3 scripts/jd_customer_service_start.py "{\"command\":\"京东客服启动\",\"shop_id\":\"shop_001\",\"session_id\":\"desktop-session-1\",\"desktop_context\":{\"platform\":\"jd_customer_service\",\"confidence\":0.9,\"active_customer\":{\"id\":\"jd_4a3d4c80e30ef\",\"name\":\"jd_4a3d4c80e30ef\"},\"chat_context\":{\"latest_customer_message\":\"这款还有吗？\",\"recent_messages\":[],\"contains_image\":false},\"product_context\":{\"tab_active\":false,\"items\":[]},\"user_order_context\":{\"user_labels\":[],\"orders\":[],\"service_forms\":[]},\"input_context\":{\"editable\":true,\"has_smart_reply\":false,\"send_button_visible\":true,\"existing_text\":\"\"}}}"
```

### 7. 导出老板电脑诊断日志

如果老板电脑没有系统级 Python，但 OpenClaw 能执行本 skill 的 Python 脚本，优先让 OpenClaw 直接调用：

```json
{"probe_payload":{"backend":{"type":"windows_uia","live":true}}}
```

对应脚本：

```text
scripts/jd_customer_service_export_diagnostics.py
```

输出会包含：
- `probe_result`
- `diagnostics_report`
- `desktop_context`
- `focus_result`

把完整 JSON 导出结果发回来，就可以继续做京东专用稳定化。

### 8. 测试回复生成

```bash
py -3 scripts/generate_reply.py "{\"prepared\":{\"shop_id\":\"shop_001\",\"session_id\":\"sess_001\",\"source_type\":\"text\",\"source_value\":\"黑色M码\",\"product_ref\":{\"type\":\"product_id\",\"value\":\"1001\"},\"user_message\":\"这件还有吗？\",\"page_context\":{},\"parsed_entities\":[],\"knowledge_hits\":{\"catalog\":[{\"source\":\"catalog\",\"field\":\"title\",\"value\":\"黑色外套\"}],\"faq\":[{\"source\":\"faq\",\"field\":\"matched_line\",\"value\":\"SKU001 商品发货时效以页面实际展示为准。\"}],\"rules\":[]}}}"
```

## 配置说明

主配置文件：

```text
config/default.json
```

当前包含：

- skill 名称
- 版本号
- 平台标识
- 默认商品 / FAQ / rules 数据源
- 支持的输入类型
- 当前启用能力
- 保守回复策略

## 数据源说明

### 商品表

```text
shops/default/products.csv
```

示例字段：

```csv
sku,product_id,title,color,size,model
SKU001,1001,黑色外套,黑色,M,JK-001
```

### FAQ

```text
shops/default/faq.md
```

用于存放常见问题答案。

### 规则

```text
shops/default/rules.md
```

用于存放售后、发货、平台规则等约束。

## 当前边界

当前版本不实现：

- 京东客服后台自动化
- 自动登录
- 验证码处理
- 风控绕过
- 自动发送客服消息
- 大规模抓取
- 实时库存查询
- 实时价格查询
- 淘宝支持
- 多平台适配
- 完整 RAG
- 多轮会话状态管理

## 安全原则

这个项目默认遵循人工审核优先：

1. 先生成结构化上下文
2. 再生成回复草稿
3. 回复内容必须人工可审
4. 不做自动发送
5. 不做绕过平台规则的能力

## 项目最终形态设想

这个 skill 做完整之后，大概会变成一个分层客服代理系统：

```text
用户输入 / 客服会话 / 商品链接 / 商品截图
        │
        ▼
输入识别层
- 文本识别
- 京东 URL 识别
- OCR / 多模态图片识别
        │
        ▼
结构化编排层
- 商品 ID / SKU / 型号抽取
- 商品资料补齐
- FAQ 命中
- 售后与发货规则命中
        │
        ▼
回复生成层
- 规则模板
- 可选本地模型 / API 模型
- 事实引用
- 风险词与承诺校验
        │
        ▼
人工审核层
- 展示 prepared
- 展示 facts_used
- 展示 reply_draft
- 人工修改确认
        │
        ▼
京东执行层
- 读取已登录客服后台当前会话
- 填充回复框
- 默认不发送
- 显式确认后发送
```

最终目标不是让系统绕过人工，而是把客服处理拆成可检查、可确认、可追踪的步骤。

## 后续路线

### 阶段 1：当前已完成

- skill 包结构
- 文本 / URL / 图片路径输入
- prepared 结构
- 本地知识补齐
- 保守回复草稿

### 阶段 2：图片识别增强

- 接入 OCR
- 从商品图 / 聊天截图抽取标题、型号、颜色、规格
- 对低置信度识别结果标记为人工确认

### 阶段 3：回复生成增强

- 接入本地模型或 Claude / 其他模型后端
- 保留规则模板作为兜底
- 增加事实引用和回复风险检查

### 阶段 4：Windows UIA 桌面工作台接入

- 读取真实前台窗口
- 枚举并标准化 Windows UIA 控件树
- 将控件树转换为 `desktop_context`
- 通过 diagnostics、candidate ranking、action gate、focus verification 控制风险
- 只准备 manual-only 填充动作，不自动发送

### 阶段 5：多平台扩展

- 保持 `prepare_request` / `generate_reply` 契约不变
- 增加平台适配器
- 先扩展淘宝、拼多多等平台的 URL 和页面适配

## GitHub 项目描述建议

英文：

```text
Offline OpenClaw skill MVP for JD customer-service workflow.
```

中文：

```text
面向京东客服场景的 OpenClaw 离线 workflow skill MVP，用于统一输入、知识补齐和客服回复草稿生成。
```

## License

未指定。上传 GitHub 前建议补充明确许可证，例如 MIT、Apache-2.0，或保持私有仓库。
