# 2026-04-14 ecommerce-customer-workflow 离线 MVP 设计

## 背景
当前 `ecommerce-customer-workflow` 仍是最小 skill 骨架，唯一可执行入口为 `scripts/validate_request.py`，只能做最基础的请求校验与标准化。为了先快速做出可演示、可验证的 MVP，本轮只建设离线能力，不接入京东后台自动化。

## 目标
在不破坏现有 `validate_request.py` 行为的前提下，实现一个离线客服工作流 MVP，支持以下输入：
- 纯文本
- 京东商品 URL
- 本地图片路径

并产出以下结果：
- 统一的 `prepared` 结构化请求对象
- 基于本地商品、FAQ、规则的可审核中文客服回复草稿

## 范围
### 本轮实现
1. 新增 `scripts/prepare_request.py` 作为统一高层入口
2. 新增统一数据模型模块 `app/models.py`
3. 新增 URL 解析器 `app/parsers/url_parser.py`
4. 新增图片解析器 `app/parsers/image_parser.py`
5. 新增本地数据加载模块：
   - `app/data/catalog_loader.py`
   - `app/data/knowledge_loader.py`
6. 新增回复生成模块：
   - `app/reply/reply_builder.py`
   - `scripts/generate_reply.py`
7. 更新 skill 文档、配置与示例，使文档承诺与实际实现一致

### 本轮不实现
- 京东后台浏览器自动化
- 自动发送客服消息
- 淘宝支持
- 联网抓取商品详情
- 完整 RAG
- 多轮会话编排
- 外部模型推理后端的强依赖

## 推荐架构
采用单体脚本编排 + 轻量模块化结构。

### 1. 输入准备层
入口：`scripts/prepare_request.py`

职责：
- 接受文本 / URL / 图片路径输入
- 识别 `source_type`
- 归一化为统一请求结构
- 调用 URL / 图片解析器提取线索
- 调用本地知识加载器进行补齐
- 输出稳定 JSON

### 2. 知识补齐层
模块：
- `app/parsers/url_parser.py`
- `app/parsers/image_parser.py`
- `app/data/catalog_loader.py`
- `app/data/knowledge_loader.py`

职责：
- URL 最小识别：提取京东商品 ID、SKU 候选、页面线索
- 图片最小识别：抽取 OCR 文本和商品实体候选
- 加载本地商品、FAQ、规则数据
- 产出 `knowledge_hits`

### 3. 回复生成层
入口：`scripts/generate_reply.py`
模块：`app/reply/reply_builder.py`

职责：
- 读取 `prepared` 结果
- 基于命中的商品、FAQ、规则生成回复草稿
- 缺少关键事实时输出保守回复
- 输出 `facts_used`

## 统一数据契约
### prepare_request 输出
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
    "user_message": "这款还有黑色吗？",
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

### generate_reply 输出
```json
{
  "ok": true,
  "reply_draft": "您好，这款商品当前可确认的信息如下……",
  "reply_reasoning_summary": "基于商品资料与 FAQ 生成保守回复草稿",
  "facts_used": [
    "catalog:title",
    "faq:shipping"
  ]
}
```

## 解析策略
### URL
- 仅支持京东商品 URL 的最小识别
- 提取商品 ID / SKU 候选 / URL 原始信息
- 不执行页面抓取
- 不依赖登录态
- 非京东 URL 返回明确错误 JSON

### 图片
- 仅支持本地图片路径
- 第一版优先做 OCR/文本线索提取
- 提取标题、规格、颜色、型号等候选
- 无可靠识别结果时返回“待人工补充”而非猜测

### 文本
- 允许只有用户消息
- 当缺少明确商品线索时，仍生成统一结构
- 允许 `knowledge_hits` 为空

## 回复生成策略
第一版采用规则模板优先，不依赖外部模型。

生成原则：
- 只基于 `prepared` 中可证实事实输出
- 有商品和 FAQ / rules 命中时，整合成中文客服草稿
- 缺关键信息时，输出保守回复，例如请用户补充型号、规格、订单信息
- 禁止编造库存、价格、发货承诺、平台规则和售后承诺

## 错误处理原则
所有脚本必须输出稳定 JSON，不抛出裸异常。

统一错误场景包括：
- 非法 JSON
- 缺少必填字段
- 非京东 URL
- 非法图片路径
- 图片无法识别
- 未命中商品
- 数据源缺失或为空

## 验证标准
1. `scripts/validate_request.py` 原有成功与失败行为保持不变
2. `scripts/prepare_request.py` 能处理：
   - 一个京东 URL
   - 一个本地图片路径
   - 一个纯文本请求
3. 三类输入均返回统一 JSON，且包含 `prepared`
4. `scripts/generate_reply.py` 能输出：
   - `reply_draft`
   - `reply_reasoning_summary`
   - `facts_used`
5. 错误路径返回明确 JSON，而不是非结构化报错

## 设计选择理由
本轮选择“单体脚本编排 + 轻量模块化”而不是纯脚本堆砌或完整服务化，原因是：
- 能最快产出可运行 MVP
- 不破坏现有 skill 骨架
- 后续接入京东浏览器执行层时可以继续沿用统一契约
- 保持输入层、知识层、回复层边界清晰，避免首版过度设计

## 后续扩展点
在本轮离线 MVP 通过后，可继续按同一契约上扩：
1. 增加京东浏览器读取与填充层
2. 增加显式确认后发送能力
3. 增加更强的图片理解后端
4. 增加模型增强回复生成
5. 扩展淘宝等平台适配层
