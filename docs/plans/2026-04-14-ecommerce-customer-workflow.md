# Ecommerce Customer Workflow Offline MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an offline MVP of the `ecommerce-customer-workflow` skill that accepts text, JD product URLs, and local image paths, produces a unified prepared payload, and generates a conservative customer-service reply draft from local knowledge.

**Architecture:** Keep `scripts/validate_request.py` unchanged as the backward-compatible minimum validator, then add a higher-level `scripts/prepare_request.py` orchestrator plus small `app/` modules for models, parsers, data loading, and reply building. The MVP is deliberately offline-first: no browser automation, no live crawling, no model dependency required for success.

**Tech Stack:** Python 3, standard library JSON/path/url parsing, optional OCR adapter fallback logic, OpenClaw skill structure, markdown/json assets.

---

### Task 1: Add shared data model helpers

**Files:**
- Create: `app/models.py`
- Modify: `scripts/prepare_request.py`
- Modify: `scripts/generate_reply.py`

**Step 1: Write the failing test**

Create a temporary executable check in the shell that imports `app.models` and validates a minimal prepared payload shape.

```python
from app.models import build_prepared_result

result = build_prepared_result(
    shop_id="shop_001",
    session_id="sess_001",
    source_type="text",
    source_value="这件还有吗",
    user_message="这件还有吗"
)
assert result["shop_id"] == "shop_001"
assert result["source_type"] == "text"
assert result["knowledge_hits"] == {"catalog": [], "faq": [], "rules": []}
```

**Step 2: Run test to verify it fails**

Run: `python3 -c "from app.models import build_prepared_result"`
Expected: FAIL with `ModuleNotFoundError` or import failure because `app/models.py` does not exist yet.

**Step 3: Write minimal implementation**

Create `app/models.py` with:
- UTF-8 safe helpers for normalized strings
- factory functions for:
  - `build_product_ref()`
  - `build_prepared_result()`
  - `build_error_response()`
  - `build_reply_response()`
- default empty structures for `page_context`, `parsed_entities`, `knowledge_hits`

Code should return plain dictionaries, not introduce dataclasses unless they clearly reduce duplication.

**Step 4: Run test to verify it passes**

Run:
`python3 -c "from app.models import build_prepared_result; r=build_prepared_result(shop_id='shop_001', session_id='sess_001', source_type='text', source_value='x', user_message='x'); assert r['knowledge_hits']=={'catalog': [], 'faq': [], 'rules': []}; print('ok')"`
Expected: PASS and print `ok`.

**Step 5: Commit**

```bash
git add app/models.py
git commit -m "feat: add workflow payload helpers"
```

### Task 2: Implement JD URL parsing

**Files:**
- Create: `app/parsers/url_parser.py`
- Modify: `app/models.py`
- Test: manual shell checks with `python3 -c`

**Step 1: Write the failing test**

```python
from app.parsers.url_parser import parse_product_url

parsed = parse_product_url("https://item.jd.com/1001.html")
assert parsed["ok"] is True
assert parsed["product_ref"]["type"] == "product_id"
assert parsed["product_ref"]["value"] == "1001"
```

Also define a failure expectation:

```python
failed = parse_product_url("https://example.com/demo")
assert failed["ok"] is False
assert "jd" in failed["error"].lower()
```

**Step 2: Run test to verify it fails**

Run: `python3 -c "from app.parsers.url_parser import parse_product_url"`
Expected: FAIL because module does not exist.

**Step 3: Write minimal implementation**

Create `app/parsers/url_parser.py` using `urllib.parse` and regex.
Implementation requirements:
- accept only `jd.com` product URLs for MVP
- support extracting product id from patterns like `item.jd.com/1001.html`
- return stable JSON-like dicts with:
  - `ok`
  - `product_ref`
  - `page_context`
  - `parsed_entities`
  - `error`
- include original URL and hostname in `page_context`
- do not fetch network content

**Step 4: Run test to verify it passes**

Run:
`python3 -c "from app.parsers.url_parser import parse_product_url; r=parse_product_url('https://item.jd.com/1001.html'); assert r['ok'] and r['product_ref']['value']=='1001'; f=parse_product_url('https://example.com/x'); assert not f['ok']; print('ok')"`
Expected: PASS and print `ok`.

**Step 5: Commit**

```bash
git add app/parsers/url_parser.py
git commit -m "feat: add JD product URL parser"
```

### Task 3: Implement local image parsing fallback

**Files:**
- Create: `app/parsers/image_parser.py`
- Test: manual shell checks with `python3 -c`

**Step 1: Write the failing test**

```python
from app.parsers.image_parser import parse_product_image

result = parse_product_image("missing-file.png")
assert result["ok"] is False
assert "path" in result["error"].lower()
```

And define a graceful-success contract for real files:

```python
result = parse_product_image("assets/sample.png")
assert "parsed_entities" in result
assert "page_context" in result
```

**Step 2: Run test to verify it fails**

Run: `python3 -c "from app.parsers.image_parser import parse_product_image"`
Expected: FAIL because module does not exist.

**Step 3: Write minimal implementation**

Create `app/parsers/image_parser.py` with MVP behavior:
- validate local file path exists
- record file name, suffix, absolute path in `page_context`
- attempt OCR only if a local OCR dependency is available
- if OCR backend is unavailable, return:
  - `ok: true`
  - empty `parsed_entities`
  - status in `page_context` explaining OCR unavailable / manual supplement needed
- if file path is invalid, return `ok: false`
- never invent extracted product facts

Keep OCR adapter isolated to one helper function so future upgrades do not disturb the CLI contract.

**Step 4: Run test to verify it passes**

Run:
`python3 -c "from app.parsers.image_parser import parse_product_image; r=parse_product_image('missing-file.png'); assert not r['ok']; print('ok')"`
Expected: PASS and print `ok`.

If a real local image exists, run an extra verification against that path and confirm the function returns structured output without crashing.

**Step 5: Commit**

```bash
git add app/parsers/image_parser.py
git commit -m "feat: add local image parsing fallback"
```

### Task 4: Implement local knowledge loaders

**Files:**
- Create: `app/data/catalog_loader.py`
- Create: `app/data/knowledge_loader.py`
- Modify: `config/default.json`
- Test: manual shell checks with `python3 -c`

**Step 1: Write the failing test**

```python
from app.data.catalog_loader import load_catalog_entries
from app.data.knowledge_loader import load_knowledge_hits

catalog = load_catalog_entries("config/default.json")
knowledge = load_knowledge_hits(
    config_path="config/default.json",
    product_ref={"type": "product_id", "value": "1001"},
    parsed_entities=[]
)
assert isinstance(catalog, list)
assert set(knowledge.keys()) == {"catalog", "faq", "rules"}
```

**Step 2: Run test to verify it fails**

Run: `python3 -c "from app.data.catalog_loader import load_catalog_entries"`
Expected: FAIL because module does not exist.

**Step 3: Write minimal implementation**

Create `app/data/catalog_loader.py` to:
- read `config/default.json`
- resolve `default_data_sources.catalog`
- support missing file as empty list, not crash
- support simple `.csv` parsing if file exists

Create `app/data/knowledge_loader.py` to:
- load FAQ and rules text paths from config
- return `knowledge_hits = {catalog: [], faq: [], rules: []}` by default
- attempt exact/contains matches using `product_ref.value` and parsed entity values
- expose matched snippets as structured dictionaries with `source`, `field`, `value`

Update `config/default.json` to add only MVP configuration fields that are actually used, for example:
- JD platform marker
- image parsing toggle
- conservative reply mode toggle

Do not add unused future flags.

**Step 4: Run test to verify it passes**

Run:
`python3 -c "from app.data.catalog_loader import load_catalog_entries; from app.data.knowledge_loader import load_knowledge_hits; c=load_catalog_entries('E:/ai skills/openclaw help skills/ecommerce-customer-workflow/config/default.json'); k=load_knowledge_hits(config_path='E:/ai skills/openclaw help skills/ecommerce-customer-workflow/config/default.json', product_ref={'type':'product_id','value':'1001'}, parsed_entities=[]); assert isinstance(c, list); assert set(k.keys())=={'catalog','faq','rules'}; print('ok')"`
Expected: PASS and print `ok`.

**Step 5: Commit**

```bash
git add app/data/catalog_loader.py app/data/knowledge_loader.py config/default.json
git commit -m "feat: add local catalog and knowledge loading"
```

### Task 5: Build prepare_request orchestrator

**Files:**
- Create: `scripts/prepare_request.py`
- Modify: `scripts/validate_request.py`
- Modify: `app/models.py`
- Modify: `app/parsers/url_parser.py`
- Modify: `app/parsers/image_parser.py`
- Modify: `app/data/knowledge_loader.py`

**Step 1: Write the failing test**

Define shell assertions for three inputs.

```python
import json, subprocess
payload = json.dumps({
    "shop_id": "shop_001",
    "session_id": "sess_001",
    "source_type": "url",
    "source_value": "https://item.jd.com/1001.html",
    "user_message": "这款还有吗？"
}, ensure_ascii=False)
```

Expected checks:
- response has `ok: true`
- response has `prepared`
- response has `action_plan`
- `prepared.source_type == 'url'`

Also define one invalid input test with non-JD URL returning `ok: false`.

**Step 2: Run test to verify it fails**

Run: `python3 scripts/prepare_request.py '{"shop_id":"shop_001"}'`
Expected: FAIL because script does not exist.

**Step 3: Write minimal implementation**

Create `scripts/prepare_request.py` that:
- accepts one JSON CLI argument
- supports `source_type` in `text`, `url`, `image`
- accepts fallback legacy `product_ref` payloads when present
- normalizes minimal required fields
- dispatches to:
  - URL parser
  - image parser
  - plain-text path
- fills `prepared`
- loads `knowledge_hits`
- emits stable JSON with:
  - `ok`
  - `prepared`
  - `action_plan`
  - `error`

Keep `scripts/validate_request.py` behavior unchanged except for any import-safe refactor strictly needed to reuse normalization helpers.

**Step 4: Run test to verify it passes**

Run three commands:

1. URL input
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://item.jd.com/1001.html","user_message":"这款还有吗？"}'`

Expected: PASS with JSON containing `"ok": true` and `"prepared"`.

2. Text input
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","user_message":"这件还有吗？"}'`

Expected: PASS with `prepared.source_type = text`.

3. Invalid URL input
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://example.com/demo","user_message":"这是什么？"}'`

Expected: PASS with JSON `"ok": false` and stable `error` string.

**Step 5: Commit**

```bash
git add scripts/prepare_request.py scripts/validate_request.py app/models.py app/parsers/url_parser.py app/parsers/image_parser.py app/data/knowledge_loader.py
git commit -m "feat: add offline request preparation workflow"
```

### Task 6: Build conservative reply generator

**Files:**
- Create: `app/reply/reply_builder.py`
- Create: `scripts/generate_reply.py`
- Reuse: `assets/reply_prompt.txt`
- Reuse: `templates/reply_prompt.txt`

**Step 1: Write the failing test**

```python
from app.reply.reply_builder import build_reply_draft

prepared = {
    "shop_id": "shop_001",
    "session_id": "sess_001",
    "source_type": "text",
    "source_value": "黑色M码",
    "product_ref": {"type": "product_id", "value": "1001"},
    "user_message": "这件还有吗？",
    "page_context": {},
    "parsed_entities": [],
    "knowledge_hits": {
        "catalog": [{"source": "catalog", "field": "title", "value": "黑色外套"}],
        "faq": [{"source": "faq", "field": "shipping", "value": "发货时效以页面为准"}],
        "rules": []
    }
}
reply = build_reply_draft(prepared)
assert reply["ok"] is True
assert reply["reply_draft"]
assert reply["facts_used"]
```

**Step 2: Run test to verify it fails**

Run: `python3 -c "from app.reply.reply_builder import build_reply_draft"`
Expected: FAIL because module does not exist.

**Step 3: Write minimal implementation**

Create `app/reply/reply_builder.py` to:
- read `prepared`
- flatten usable facts from `knowledge_hits`
- generate conservative Chinese reply text
- if there are no decisive facts, default to a safe clarification-style reply
- return:
  - `ok`
  - `reply_draft`
  - `reply_reasoning_summary`
  - `facts_used`

Create `scripts/generate_reply.py` to:
- accept one JSON CLI argument or a `prepared` wrapper payload
- validate presence of `prepared`
- call `build_reply_draft`
- print stable JSON UTF-8 output

Do not call any external model in this task.

**Step 4: Run test to verify it passes**

Run:
`python3 -c "from app.reply.reply_builder import build_reply_draft; prepared={'shop_id':'shop_001','session_id':'sess_001','source_type':'text','source_value':'黑色M码','product_ref':{'type':'product_id','value':'1001'},'user_message':'这件还有吗？','page_context':{},'parsed_entities':[],'knowledge_hits':{'catalog':[{'source':'catalog','field':'title','value':'黑色外套'}],'faq':[{'source':'faq','field':'shipping','value':'发货时效以页面为准'}],'rules':[]}}; r=build_reply_draft(prepared); assert r['ok'] and r['reply_draft'] and r['facts_used']; print('ok')"`
Expected: PASS and print `ok`.

Then run end-to-end:
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/generate_reply.py" '{"prepared":{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","product_ref":{"type":"product_id","value":"1001"},"user_message":"这件还有吗？","page_context":{},"parsed_entities":[],"knowledge_hits":{"catalog":[{"source":"catalog","field":"title","value":"黑色外套"}],"faq":[{"source":"faq","field":"shipping","value":"发货时效以页面为准"}],"rules":[]}}}'`
Expected: PASS with JSON containing `reply_draft` and `facts_used`.

**Step 5: Commit**

```bash
git add app/reply/reply_builder.py scripts/generate_reply.py
git commit -m "feat: add conservative customer reply generator"
```

### Task 7: Update skill docs, metadata, and examples

**Files:**
- Modify: `SKILL.md`
- Modify: `_meta.json`
- Modify: `config/default.json`
- Modify: `references/architecture.md`
- Modify: `references/integration.md`
- Create: `examples/prepare_request.example.json`
- Create: `examples/generate_reply.example.json`
- Reuse: `assets/request.example.json`

**Step 1: Write the failing test**

Define review checks instead of unit tests:
- `SKILL.md` must mention offline MVP only
- all documented script paths must exist
- docs must not promise JD browser execution
- examples must match actual CLI contracts

**Step 2: Run test to verify it fails**

Manual review of current docs should fail because they still describe only the old validator and do not document the new MVP flow.

**Step 3: Write minimal implementation**

Update docs to reflect the real state after Tasks 1-6:
- `SKILL.md`
  - describe supported inputs: text / JD URL / local image path
  - describe outputs: `prepared` and `reply_draft`
  - state that browser execution is not in this MVP
- `_meta.json`
  - bump version
  - keep metadata aligned with skill scope
- `references/architecture.md`
  - update core layers to reflect input preparation / knowledge enrichment / reply generation
- `references/integration.md`
  - update recommended call flow: `prepare_request.py` -> `generate_reply.py`
- add examples matching real payloads

**Step 4: Run test to verify it passes**

Run manual verification:
- open each updated file
- confirm every documented script exists on disk
- confirm examples can be passed into the scripts without shape mismatch

Then run:
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" "$(python3 -c 'import json; print(json.dumps(json.load(open(r"E:/ai skills/openclaw help skills/ecommerce-customer-workflow/examples/prepare_request.example.json", encoding="utf-8")), ensure_ascii=False))')"`

Expected: PASS with structured JSON.

**Step 5: Commit**

```bash
git add SKILL.md _meta.json config/default.json references/architecture.md references/integration.md examples/prepare_request.example.json examples/generate_reply.example.json
git commit -m "docs: align skill docs with offline MVP"
```

### Task 8: Run end-to-end verification and regression checks

**Files:**
- Test: `scripts/validate_request.py`
- Test: `scripts/prepare_request.py`
- Test: `scripts/generate_reply.py`
- Test: `examples/prepare_request.example.json`
- Test: `examples/generate_reply.example.json`

**Step 1: Write the failing test**

Prepare a verification checklist with exact commands covering:
- legacy validator success
- legacy validator failure
- prepare request from URL
- prepare request from text
- prepare request from invalid URL
- prepare request from invalid image path
- generate reply from prepared payload

**Step 2: Run test to verify it fails**

Before implementation completes, at least some commands must fail because files or modules are missing.

**Step 3: Write minimal implementation**

No new code in this task unless a verification failure reveals a real defect. Fix only the exact defect exposed by the failing verification command.

**Step 4: Run test to verify it passes**

Run these commands and record outputs:

1. Legacy success
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/validate_request.py" '{"shop_id":"shop_001","session_id":"sess_001","product_ref":{"type":"sku","value":"SKU001"},"user_message":"这件黑色M码还有吗？"}'`
Expected: `"ok": true`

2. Legacy failure
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/validate_request.py" '{"shop_id":"","session_id":"sess_001","product_ref":{"type":"sku","value":"SKU001"},"user_message":"x"}'`
Expected: `"ok": false`

3. URL prepare success
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://item.jd.com/1001.html","user_message":"这款还有吗？"}'`
Expected: `"ok": true`

4. Text prepare success
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","user_message":"这件还有吗？"}'`
Expected: `"ok": true`

5. Invalid URL failure
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://example.com/demo","user_message":"这是什么？"}'`
Expected: `"ok": false`

6. Invalid image path failure
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/prepare_request.py" '{"shop_id":"shop_001","session_id":"sess_001","source_type":"image","source_value":"missing-file.png","user_message":"这个商品是什么？"}'`
Expected: `"ok": false`

7. Reply generation success
`python3 "E:/ai skills/openclaw help skills/ecommerce-customer-workflow/scripts/generate_reply.py" "$(python3 -c 'import json; print(json.dumps(json.load(open(r"E:/ai skills/openclaw help skills/ecommerce-customer-workflow/examples/generate_reply.example.json", encoding="utf-8")), ensure_ascii=False))')"`
Expected: `"ok": true` with `reply_draft` and `facts_used`

**Step 5: Commit**

```bash
git add .
git commit -m "test: verify offline workflow MVP"
```
