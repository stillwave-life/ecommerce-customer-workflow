# ecommerce-customer-workflow

面向京东客服场景的 OpenClaw 离线 workflow skill MVP。

这个项目的目标是先把“客服代理”的基础工作流做扎实：把文本、京东商品 URL、本地图片路径统一整理成结构化客服上下文，再基于本地商品资料、FAQ、规则生成可审核的中文客服回复草稿。

当前版本不是全自动客服机器人，也不会直接操作京东后台。它更像一个安全、可验证、可继续扩展的客服工作流底座。

## 项目定位

`ecommerce-customer-workflow` 是一个可以放入 OpenClaw `skills` 目录的 skill 包。

它当前解决的问题是：

1. 客服输入来源不统一，需要统一成标准 JSON 上下文
2. 商品资料、FAQ、售后规则散落在不同文件里，需要统一命中和补齐
3. 客服回复不能瞎编，需要基于已有事实生成保守草稿
4. 后续要接浏览器、OCR、模型推理，需要先有稳定的数据契约

## 当前整体流程

```text
文本 / 京东商品 URL / 本地图片路径
        │
        ▼
scripts/prepare_request.py
        │
        ├─ URL 解析：提取京东商品 ID
        ├─ 图片解析：校验本地图片路径，预留 OCR 扩展
        ├─ 文本输入：直接归一化
        └─ 本地知识补齐：catalog / FAQ / rules
        │
        ▼
统一 prepared 结构
        │
        ▼
scripts/generate_reply.py
        │
        ▼
可审核中文客服回复草稿
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

### 2. 最小请求校验

入口：

```text
scripts/validate_request.py
```

用于兼容原始最小输入契约：

```json
{
  "shop_id": "shop_001",
  "session_id": "sess_001",
  "product_ref": {
    "type": "sku",
    "value": "SKU001"
  },
  "user_message": "这件黑色M码还有吗？"
}
```

### 3. 离线请求准备

入口：

```text
scripts/prepare_request.py
```

支持三类输入：

- `text`：纯文本
- `url`：京东商品 URL
- `image`：本地图片路径

输出统一结构：

```json
{
  "ok": true,
  "prepared": {
    "shop_id": "shop_001",
    "session_id": "sess_001",
    "source_type": "url",
    "source_value": "https://item.jd.com/1001.html",
    "product_ref": {
      "type": "product_id",
      "value": "1001"
    },
    "user_message": "这款还有吗？",
    "page_context": {},
    "parsed_entities": [],
    "knowledge_hits": {
      "catalog": [],
      "faq": [],
      "rules": []
    }
  },
  "action_plan": [
    "review_prepared_request",
    "generate_reply"
  ]
}
```

### 4. 京东商品 URL 最小识别

模块：

```text
app/parsers/url_parser.py
```

当前支持类似：

```text
https://item.jd.com/1001.html
```

会提取：

```json
{
  "type": "product_id",
  "value": "1001"
}
```

当前不会做：

- 页面抓取
- 登录态读取
- 反爬绕过
- 价格 / 库存实时查询

### 5. 本地图片路径输入

模块：

```text
app/parsers/image_parser.py
```

当前实现的是保守 MVP：

- 校验图片路径是否存在
- 输出文件名、路径、后缀等结构化上下文
- 预留 OCR 扩展点
- 如果没有 OCR 结果，不会编造商品信息

后续可以在这里接入 OCR 或多模态识别。

### 6. 本地知识补齐

模块：

```text
app/data/catalog_loader.py
app/data/knowledge_loader.py
```

默认数据源：

```text
shops/default/products.csv
shops/default/faq.md
shops/default/rules.md
```

当前支持：

- 读取商品 CSV
- 读取 FAQ 文本
- 读取 rules 文本
- 根据商品 ID、SKU、实体候选进行简单命中
- 返回结构化 `knowledge_hits`

### 7. 客服回复草稿生成

入口：

```text
scripts/generate_reply.py
```

模块：

```text
app/reply/reply_builder.py
```

当前是规则模板生成，不依赖外部模型。

生成原则：

- 只使用 `knowledge_hits` 中已经确认的事实
- 缺少事实时输出保守澄清回复
- 不编造库存
- 不编造价格
- 不编造发货承诺
- 不编造平台规则
- 不编造售后承诺

示例输出：

```json
{
  "ok": true,
  "reply_draft": "您好，结合当前可确认的信息，先为您整理如下：...",
  "reply_reasoning_summary": "基于本地商品/FAQ/规则命中结果生成保守回复草稿",
  "facts_used": [
    "catalog:title",
    "faq:matched_line"
  ]
}
```

## 目录结构

```text
ecommerce-customer-workflow/
├─ SKILL.md
├─ _meta.json
├─ app/
│  ├─ models.py
│  ├─ data/
│  │  ├─ catalog_loader.py
│  │  └─ knowledge_loader.py
│  ├─ parsers/
│  │  ├─ image_parser.py
│  │  └─ url_parser.py
│  └─ reply/
│     └─ reply_builder.py
├─ assets/
│  ├─ reply_prompt.txt
│  └─ request.example.json
├─ config/
│  └─ default.json
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

### 5. 测试回复生成

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

### 阶段 4：京东后台半自动执行

- 使用浏览器自动化读取已登录页面
- 自动填充回复框
- 默认不发送
- 用户显式确认后才发送

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
