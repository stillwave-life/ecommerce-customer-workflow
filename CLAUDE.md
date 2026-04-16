# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Commands

This repository is a pure Python offline OpenClaw skill package. No separate build step is currently defined.

### Run workflow entrypoints

Use `python3` on Linux/macOS and `py -3` on Windows if `python3` is unavailable.

Validate the original minimal request contract:

```bash
python3 scripts/validate_request.py '{"shop_id":"shop_001","session_id":"sess_001","product_ref":{"type":"sku","value":"SKU001"},"user_message":"这件黑色M码还有吗？"}'
```

Prepare a unified customer-service request from text input:

```bash
python3 scripts/prepare_request.py '{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","user_message":"这件还有吗？"}'
```

Prepare a unified request from a JD product URL:

```bash
python3 scripts/prepare_request.py '{"shop_id":"shop_001","session_id":"sess_001","source_type":"url","source_value":"https://item.jd.com/1001.html","user_message":"这款还有吗？"}'
```

Generate a conservative Chinese reply draft from a prepared payload:

```bash
python3 scripts/generate_reply.py '{"prepared":{"shop_id":"shop_001","session_id":"sess_001","source_type":"text","source_value":"黑色M码","product_ref":{"type":"product_id","value":"1001"},"user_message":"这件还有吗？","page_context":{},"parsed_entities":[],"knowledge_hits":{"catalog":[{"source":"catalog","field":"title","value":"黑色外套"}],"faq":[],"rules":[]}}}'
```

Start the Phase A desktop assistant contract with a parsed desktop context payload:

```bash
python3 scripts/jd_customer_service_start.py '{"command":"京东客服启动","shop_id":"shop_001","session_id":"desktop-session-1","desktop_context":{"platform":"jd_customer_service","confidence":0.9,"active_customer":{"id":"jd_4a3d4c80e30ef","name":"jd_4a3d4c80e30ef"},"chat_context":{"latest_customer_message":"这款还有吗？","recent_messages":[],"contains_image":false},"product_context":{"tab_active":false,"items":[]},"user_order_context":{"user_labels":[],"orders":[],"service_forms":[]},"input_context":{"editable":true,"has_smart_reply":false,"send_button_visible":true,"existing_text":""}}}'
```

### Run tests

Run all tests:

```bash
python3 -m pytest tests
```

Run one test file:

```bash
python3 -m pytest tests/reply/test_reply_builder.py
```

Run one test function:

```bash
python3 -m pytest tests/reply/test_reply_builder.py::test_build_reply_draft_answers_with_context_and_memory_hints
```

The repository currently has no discovered project-level lint or formatter configuration.

## High-Level Architecture

`ecommerce-customer-workflow` is an offline OpenClaw workflow skill MVP for JD customer-service scenarios. It does not automate JD backend operations, send customer messages, scrape live product pages, or query real-time stock/prices. Its purpose is to normalize customer-service inputs, enrich them with local shop knowledge, and produce conservative, auditable Chinese reply drafts.

Main data flow:

```text
text / JD product URL / local image path
        -> scripts/prepare_request.py
        -> app/parsers/*
        -> app/data/*
        -> prepared payload
        -> scripts/generate_reply.py
        -> app/reply/reply_builder.py
        -> reply_draft + facts_used
```

Phase A desktop-assistant flow:

```text
parsed desktop_context
        -> scripts/jd_customer_service_start.py
        -> app/desktop/launcher.py
        -> app/desktop/prepare_mapper.py
        -> app/desktop/reply_composer.py
        -> app/desktop/fill_action.py
        -> fill_action (manual send only)
```

UI perception flow:

```text
structured window probe / UI node inputs
        -> app/desktop/perception/window_probe.py
        -> app/desktop/perception/ui_tree_reader.py
        -> app/desktop/perception/region_classifier.py
        -> app/desktop/perception/jd_workspace_parser.py
        -> desktop_context
        -> Phase A desktop-assistant flow
```

Windows adapter flow:

```text
structured foreground window / normalized automation nodes
        -> app/desktop/windows_adapter/foreground_window.py
        -> app/desktop/windows_adapter/ui_node_adapter.py
        -> app/desktop/windows_adapter/region_input_bridge.py
        -> app/desktop/windows_adapter/input_focus.py
        -> app/desktop/windows_adapter/perception_bridge.py
        -> desktop_context + focus_result
        -> launcher / reply / fill_action
```


- `scripts/validate_request.py` validates the original minimal input contract with `shop_id`, `session_id`, `product_ref`, and `user_message`.
- `scripts/prepare_request.py` is the main preparation entrypoint. It validates base fields, normalizes `source_type`, calls the relevant parser, loads local knowledge, and returns the canonical `prepared` structure.
- `scripts/generate_reply.py` accepts either a raw prepared object or `{ "prepared": ... }`, then delegates reply generation to `app/reply/reply_builder.py`.
- `scripts/jd_customer_service_start.py` is the Phase A desktop assistant entrypoint. It accepts a parsed `desktop_context` payload and returns launch/reply/fill-action results.
- `app/models.py` defines shared response builders and the canonical `build_prepared_result()` shape, including `knowledge_hits`, `memory_hits`, `constraints`, `reply_strategy`, and `session_status`.
- `app/parsers/url_parser.py` supports minimal JD product URL parsing and extracts `product_id` from URLs like `https://item.jd.com/1001.html`.
- `app/parsers/image_parser.py` currently validates local image paths and returns file metadata. OCR is intentionally stubbed out and should not be treated as implemented.
- `app/data/catalog_loader.py` and `app/data/knowledge_loader.py` load local product, FAQ, and rule data from paths declared in `config/default.json`, then perform simple candidate matching.
- `app/constraints/constraint_builder.py` merges stored constraints, newly extracted memories, and retrieved memory hits into `confirmed`, `candidate`, `conflicted`, and `missing` groups.
- `app/reply/reply_builder.py` implements conservative reply strategies: ask for clarification, resolve conflicts, answer with grounded context, or fall back when facts are insufficient.
- `app/desktop/windows_adapter/foreground_window.py` defines the foreground-window contract for Windows adapter inputs.
- `app/desktop/windows_adapter/ui_node_adapter.py` normalizes Windows automation nodes into the internal node format.
- `app/desktop/windows_adapter/region_input_bridge.py` bridges Windows nodes into perception-region inputs.
- `app/desktop/windows_adapter/input_focus.py` defines safe input-focus result contracts.
- `app/desktop/windows_adapter/perception_bridge.py` packages probe results, desktop context, and focus results into a unified adapter output.

## Data and Configuration

- `config/default.json` declares the skill name, supported source types, default data sources, storage-related settings, feature flags, and conservative reply policy.
- Default shop knowledge lives under `shops/default/`:
  - `products.csv` for structured catalog rows
  - `faq.md` for FAQ text
  - `rules.md` for after-sales, shipping, and platform rules
- Example input payloads live under `examples/` and `assets/request.example.json`.
- `SKILL.md` is the OpenClaw-facing skill description and should stay consistent with the implemented offline workflow.

## Important Boundaries

- Current implementation is offline and local-file based.
- `config/default.json` contains future-facing storage and RAG settings, but the presence of a flag does not mean a complete production backend exists.
- JD URL parsing is intentionally minimal and does not fetch page contents.
- Image input does not perform OCR yet; it only records local file metadata and marks manual review when no parsed entities are available.
- Reply generation must remain conservative: missing evidence should produce clarification language, not guessed business facts.
- Phase A desktop assistant accepts an already parsed `desktop_context`; it does not directly capture the screen yet.
- UI perception currently starts from structured probe results, node lists, and classified region inputs; a live Windows UI Automation backend is not implemented yet.
- Windows adapter currently starts from structured foreground-window results, normalized automation nodes, and focus-result contracts; a live Windows UI Automation backend is not implemented yet.
- Phase A may return a `fill_action`, but `fill_action.auto_send_allowed` must always remain `false`.
