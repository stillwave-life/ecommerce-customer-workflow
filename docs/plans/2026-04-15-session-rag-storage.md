# Session RAG Storage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a dual-backend session-scoped RAG storage layer that persists conversation messages, extracts reusable memories, derives session constraints, and feeds constrained reply generation.

**Architecture:** Keep the current request/reply scripts as orchestration entrypoints and add repository-based storage behind a backend selector (`csv` or `postgres`). Implement the MVP in small slices: config and models first, then CSV storage, then constraint/query flow, then PostgreSQL parity and reply integration. Retrieval must remain session-scoped and lifecycle-aware so only active sessions participate in real-time recall.

**Tech Stack:** Python, JSON/CSV file storage, PostgreSQL, optional pgvector-compatible interface, pytest

---

### Task 1: Add configuration and response model support

**Files:**
- Modify: `config/default.json`
- Modify: `app/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

```python
from app.models import build_prepared_result


def test_build_prepared_result_includes_memory_fields():
    prepared = build_prepared_result(
        shop_id="shop-1",
        session_id="session-1",
        source_type="text",
        source_value="这个怎么样",
        user_message="这个怎么样",
        memory_hits=[{"memory_type": "spec_fact", "memory_text": "客户提到256G"}],
        constraints={"confirmed": [], "candidate": [], "conflicted": [], "missing": [], "forbidden_claims": []},
        reply_strategy="ask_for_clarification",
    )

    assert prepared["memory_hits"][0]["memory_type"] == "spec_fact"
    assert prepared["constraints"]["missing"] == []
    assert prepared["reply_strategy"] == "ask_for_clarification"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_build_prepared_result_includes_memory_fields -v`
Expected: FAIL because `build_prepared_result()` does not accept the new fields yet.

**Step 3: Write minimal implementation**

Update `app/models.py` so `build_prepared_result()` accepts and returns:

```python
memory_hits: list[dict[str, Any]] | None = None,
constraints: dict[str, list[dict[str, Any]]] | None = None,
reply_strategy: str | None = None,
session_status: str | None = None,
```

and includes safe defaults:

```python
EMPTY_CONSTRAINTS = {
    "confirmed": [],
    "candidate": [],
    "conflicted": [],
    "missing": [],
    "forbidden_claims": [],
}
```

Update `config/default.json` to add:

```json
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
```

and set `features.rag` to `true`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_build_prepared_result_includes_memory_fields -v`
Expected: PASS

**Step 5: Commit**

```bash
git add config/default.json app/models.py tests/test_models.py
git commit -m "feat: add rag storage config and prepared fields"
```

---

### Task 2: Add backend selection and repository protocol

**Files:**
- Create: `app/memory/memory_repository.py`
- Create: `app/memory/__init__.py`
- Test: `tests/memory/test_memory_repository.py`

**Step 1: Write the failing test**

```python
from app.memory.memory_repository import create_memory_repository


def test_create_memory_repository_returns_csv_backend(tmp_path):
    config = {
        "storage_backend": "csv",
        "storage": {"csv": {"base_dir": str(tmp_path), "retention_days": 7}},
    }

    repository = create_memory_repository(config)

    assert repository.backend_name == "csv"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_memory_repository.py::test_create_memory_repository_returns_csv_backend -v`
Expected: FAIL because the repository module does not exist yet.

**Step 3: Write minimal implementation**

Create a protocol-style repository API in `app/memory/memory_repository.py` with methods:

```python
class MemoryRepository(Protocol):
    backend_name: str

    def ensure_session(self, *, shop_id: str, session_id: str, now: str) -> dict[str, Any]: ...
    def save_message(self, *, shop_id: str, session_id: str, role: str, message_text: str, source_type: str, source_value: str, parsed_entities: list[dict[str, Any]], created_at: str) -> dict[str, Any]: ...
    def save_memories(self, *, shop_id: str, session_id: str, message_id: str, memories: list[dict[str, Any]], created_at: str) -> list[dict[str, Any]]: ...
    def load_constraints(self, *, shop_id: str, session_id: str) -> list[dict[str, Any]]: ...
    def replace_constraints(self, *, shop_id: str, session_id: str, constraints: list[dict[str, Any]], updated_at: str) -> list[dict[str, Any]]: ...
    def search_memories(self, *, shop_id: str, session_id: str, query_text: str, limit: int) -> list[dict[str, Any]]: ...
    def close_session(self, *, shop_id: str, session_id: str, ended_at: str, expires_at: str) -> dict[str, Any]: ...
```

Add `create_memory_repository(config)` that dispatches to CSV or PostgreSQL implementations.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_memory_repository.py::test_create_memory_repository_returns_csv_backend -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/memory/__init__.py app/memory/memory_repository.py tests/memory/test_memory_repository.py
git commit -m "feat: add memory repository abstraction"
```

---

### Task 3: Implement CSV session/message storage

**Files:**
- Create: `app/memory/csv_memory_repository.py`
- Test: `tests/memory/test_csv_memory_repository.py`

**Step 1: Write the failing test**

```python
from app.memory.csv_memory_repository import CsvMemoryRepository


def test_csv_repository_persists_session_and_message(tmp_path):
    repository = CsvMemoryRepository(base_dir=tmp_path, retention_days=7)
    repository.ensure_session(shop_id="shop-1", session_id="session-1", now="2026-04-15T10:00:00Z")

    message = repository.save_message(
        shop_id="shop-1",
        session_id="session-1",
        role="customer",
        message_text="我要黑色的",
        source_type="text",
        source_value="我要黑色的",
        parsed_entities=[],
        created_at="2026-04-15T10:00:00Z",
    )

    assert message["role"] == "customer"
    assert (tmp_path / "sessions.csv").is_file()
    assert (tmp_path / "messages.csv").is_file()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_csv_repository_persists_session_and_message -v`
Expected: FAIL because the CSV repository does not exist yet.

**Step 3: Write minimal implementation**

Create `CsvMemoryRepository` that stores four files under `base_dir`:

- `sessions.csv`
- `messages.csv`
- `memories.csv`
- `constraints.csv`

Implement:
- `ensure_session()` to upsert active session rows
- `save_message()` to append message rows with generated IDs

Use simple CSV helpers with `csv.DictWriter` and JSON-encode `parsed_entities`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_csv_repository_persists_session_and_message -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/memory/csv_memory_repository.py tests/memory/test_csv_memory_repository.py
git commit -m "feat: add csv session and message storage"
```

---

### Task 4: Implement CSV memory storage and retrieval fallback

**Files:**
- Modify: `app/memory/csv_memory_repository.py`
- Test: `tests/memory/test_csv_memory_repository.py`

**Step 1: Write the failing test**

```python
def test_csv_repository_searches_session_memories_by_overlap(tmp_path):
    repository = CsvMemoryRepository(base_dir=tmp_path, retention_days=7)
    repository.ensure_session(shop_id="shop-1", session_id="session-1", now="2026-04-15T10:00:00Z")
    repository.save_memories(
        shop_id="shop-1",
        session_id="session-1",
        message_id="msg-1",
        memories=[
            {
                "memory_type": "spec_fact",
                "memory_text": "客户提到黑色256G",
                "memory_payload": {"field": "size", "value": "256G", "status": "candidate"},
                "confidence": 0.8,
            }
        ],
        created_at="2026-04-15T10:00:00Z",
    )

    hits = repository.search_memories(
        shop_id="shop-1",
        session_id="session-1",
        query_text="256G怎么样",
        limit=3,
    )

    assert hits[0]["memory_type"] == "spec_fact"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_csv_repository_searches_session_memories_by_overlap -v`
Expected: FAIL because `save_memories()` or `search_memories()` is incomplete.

**Step 3: Write minimal implementation**

Extend `CsvMemoryRepository` to:
- append `memories.csv` rows
- JSON-encode `memory_payload`
- implement `search_memories()` using session-scoped text overlap scoring
- sort by overlap score and recency
- ignore sessions not marked `active`

A minimal overlap scorer is sufficient, for example:

```python
def score(query_text: str, memory_text: str) -> int:
    query_tokens = {token for token in query_text.lower() if token.strip()}
    memory_tokens = {token for token in memory_text.lower() if token.strip()}
    return len(query_tokens & memory_tokens)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_csv_repository_searches_session_memories_by_overlap -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/memory/csv_memory_repository.py tests/memory/test_csv_memory_repository.py
git commit -m "feat: add csv memory retrieval fallback"
```

---

### Task 5: Implement memory extraction rules

**Files:**
- Create: `app/memory/memory_extractor.py`
- Test: `tests/memory/test_memory_extractor.py`

**Step 1: Write the failing test**

```python
from app.memory.memory_extractor import extract_memories


def test_extract_memories_from_entities_and_text():
    memories = extract_memories(
        user_message="我要黑色256G，如果没货白色也行",
        parsed_entities=[
            {"type": "color", "value": "黑色"},
            {"type": "size", "value": "256G"},
            {"type": "color", "value": "白色"},
        ],
    )

    fields = {(item["memory_payload"]["field"], item["memory_payload"]["value"]) for item in memories}

    assert ("color", "黑色") in fields
    assert ("size", "256G") in fields
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_memory_extractor.py::test_extract_memories_from_entities_and_text -v`
Expected: FAIL because the extractor does not exist yet.

**Step 3: Write minimal implementation**

Create `extract_memories(user_message, parsed_entities)` that returns compact memory records. Start with a simple mapping:

```python
ENTITY_FIELD_MAP = {
    "color": "color",
    "size": "size",
    "model": "model",
    "sku": "sku",
    "product_id": "product_id",
}
```

Emit records like:

```python
{
  "memory_type": "spec_fact",
  "memory_text": "客户提到颜色为黑色",
  "memory_payload": {"field": "color", "value": "黑色", "status": "candidate"},
  "confidence": 0.8,
}
```

If the message contains `如果没货` and a second color candidate, add a `preference_fact` memory for fallback choice.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_memory_extractor.py::test_extract_memories_from_entities_and_text -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/memory/memory_extractor.py tests/memory/test_memory_extractor.py
git commit -m "feat: add session memory extraction rules"
```

---

### Task 6: Implement constraint builder

**Files:**
- Create: `app/constraints/constraint_builder.py`
- Create: `app/constraints/__init__.py`
- Test: `tests/constraints/test_constraint_builder.py`

**Step 1: Write the failing test**

```python
from app.constraints.constraint_builder import build_constraints


def test_build_constraints_marks_conflicts_and_missing_fields():
    constraints = build_constraints(
        stored_constraints=[
            {"constraint_key": "color", "constraint_value": "黑色", "status": "candidate"}
        ],
        new_memories=[
            {"memory_payload": {"field": "color", "value": "白色", "status": "candidate"}}
        ],
        memory_hits=[],
        required_fields=["product_id"],
    )

    conflicted = {(item["key"], item["values"][0]) for item in constraints["conflicted"]}
    missing = {item["key"] for item in constraints["missing"]}

    assert ("color", "白色") in conflicted or ("color", "黑色") in conflicted
    assert "product_id" in missing
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/constraints/test_constraint_builder.py::test_build_constraints_marks_conflicts_and_missing_fields -v`
Expected: FAIL because the builder does not exist yet.

**Step 3: Write minimal implementation**

Create `build_constraints(stored_constraints, new_memories, memory_hits, required_fields)` that:
- groups values by field
- puts single confirmed/candidate values in `confirmed` or `candidate`
- puts multiple distinct values under `conflicted`
- adds absent required fields to `missing`
- always returns all buckets including `forbidden_claims`

Use an output shape like:

```python
{
  "confirmed": [{"key": "product_id", "value": "123"}],
  "candidate": [{"key": "size", "value": "256G"}],
  "conflicted": [{"key": "color", "values": ["黑色", "白色"]}],
  "missing": [{"key": "product_id", "reason": "required_for_reply"}],
  "forbidden_claims": [],
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/constraints/test_constraint_builder.py::test_build_constraints_marks_conflicts_and_missing_fields -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/constraints/__init__.py app/constraints/constraint_builder.py tests/constraints/test_constraint_builder.py
git commit -m "feat: add session constraint builder"
```

---

### Task 7: Integrate CSV-backed session RAG into request preparation

**Files:**
- Modify: `scripts/prepare_request.py`
- Modify: `app/models.py`
- Test: `tests/scripts/test_prepare_request.py`

**Step 1: Write the failing test**

```python
import json

from scripts.prepare_request import main


def test_prepare_request_returns_memory_hits_and_constraints(monkeypatch, tmp_path, capsys):
    config = {
        "storage_backend": "csv",
        "storage": {"csv": {"base_dir": str(tmp_path), "retention_days": 7}},
        "default_data_sources": {},
    }

    monkeypatch.setattr("scripts.prepare_request.CONFIG_PATH", tmp_path / "default.json")
    (tmp_path / "default.json").write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("sys.argv", [
        "prepare_request.py",
        json.dumps({
            "shop_id": "shop-1",
            "session_id": "session-1",
            "source_type": "text",
            "source_value": "这个怎么样",
            "user_message": "这个怎么样",
        }, ensure_ascii=False),
    ])

    main()
    output = json.loads(capsys.readouterr().out)

    assert output["ok"] is True
    assert "constraints" in output["prepared"]
    assert "memory_hits" in output["prepared"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_prepare_request.py::test_prepare_request_returns_memory_hits_and_constraints -v`
Expected: FAIL because `prepare_request.py` does not orchestrate the RAG pipeline yet.

**Step 3: Write minimal implementation**

Update `scripts/prepare_request.py` to:
- load the config JSON
- create a repository via `create_memory_repository(config)`
- ensure the session is active
- save the incoming message as role `customer`
- extract memories with `extract_memories(user_message, parsed_entities)`
- save memories
- load stored constraints
- if the message is ambiguous, call `search_memories()` with the current message text
- build merged constraints with `build_constraints(...)`
- persist flattened constraints with `replace_constraints(...)`
- pass `memory_hits`, `constraints`, `reply_strategy`, and `session_status` into `build_prepared_result()`

Use a minimal ambiguity detector such as:

```python
AMBIGUOUS_MARKERS = ("这个", "那个", "之前", "刚才", "上次", "继续", "还是")
```

Set `reply_strategy` to:
- `resolve_conflict` when conflicts exist
- `ask_for_clarification` when required fields are missing
- `answer_with_context` otherwise

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_prepare_request.py::test_prepare_request_returns_memory_hits_and_constraints -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/prepare_request.py app/models.py tests/scripts/test_prepare_request.py
git commit -m "feat: add csv session rag pipeline to request preparation"
```

---

### Task 8: Integrate constraint-aware reply strategies

**Files:**
- Modify: `app/reply/reply_builder.py`
- Modify: `scripts/generate_reply.py`
- Test: `tests/reply/test_reply_builder.py`

**Step 1: Write the failing test**

```python
from app.reply.reply_builder import build_reply_draft


def test_build_reply_draft_asks_for_clarification_when_constraints_missing():
    prepared = {
        "user_message": "这个怎么样",
        "knowledge_hits": {"catalog": [], "faq": [], "rules": []},
        "memory_hits": [{"memory_text": "客户之前问过256G版本"}],
        "constraints": {
            "confirmed": [],
            "candidate": [],
            "conflicted": [],
            "missing": [{"key": "product_id", "reason": "required_for_reply"}],
            "forbidden_claims": [],
        },
        "reply_strategy": "ask_for_clarification",
    }

    result = build_reply_draft(prepared)

    assert "补充" in result["reply_draft"] or "确认" in result["reply_draft"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/reply/test_reply_builder.py::test_build_reply_draft_asks_for_clarification_when_constraints_missing -v`
Expected: FAIL because the reply builder ignores the new strategy fields.

**Step 3: Write minimal implementation**

Update `app/reply/reply_builder.py` so it checks `prepared["reply_strategy"]` before flattening `knowledge_hits`:

- `ask_for_clarification` → ask for missing product/spec fields
- `resolve_conflict` → ask the customer to confirm the conflicting values
- `answer_with_context` → use existing knowledge-based summary plus current memory hints

Return `facts_used` from both `knowledge_hits` and `memory_hits` where appropriate.

**Step 4: Run test to verify it passes**

Run: `pytest tests/reply/test_reply_builder.py::test_build_reply_draft_asks_for_clarification_when_constraints_missing -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/reply/reply_builder.py scripts/generate_reply.py tests/reply/test_reply_builder.py
git commit -m "feat: add constraint-aware reply strategies"
```

---

### Task 9: Add session lifecycle close/expiry behavior

**Files:**
- Modify: `app/memory/csv_memory_repository.py`
- Test: `tests/memory/test_csv_memory_repository.py`

**Step 1: Write the failing test**

```python
def test_closed_session_is_excluded_from_memory_search(tmp_path):
    repository = CsvMemoryRepository(base_dir=tmp_path, retention_days=7)
    repository.ensure_session(shop_id="shop-1", session_id="session-1", now="2026-04-15T10:00:00Z")
    repository.save_memories(
        shop_id="shop-1",
        session_id="session-1",
        message_id="msg-1",
        memories=[{"memory_type": "spec_fact", "memory_text": "客户提到黑色", "memory_payload": {"field": "color", "value": "黑色", "status": "candidate"}, "confidence": 0.8}],
        created_at="2026-04-15T10:00:00Z",
    )
    repository.close_session(
        shop_id="shop-1",
        session_id="session-1",
        ended_at="2026-04-15T11:00:00Z",
        expires_at="2026-04-22T11:00:00Z",
    )

    hits = repository.search_memories(
        shop_id="shop-1",
        session_id="session-1",
        query_text="黑色怎么样",
        limit=3,
    )

    assert hits == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_closed_session_is_excluded_from_memory_search -v`
Expected: FAIL because lifecycle state is not enforced yet.

**Step 3: Write minimal implementation**

Update `CsvMemoryRepository` so:
- `close_session()` marks session `closed` and stores `ended_at` and `expires_at`
- `search_memories()` returns no results for non-active sessions
- `ensure_session()` can reopen only when explicitly called for new activity

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_csv_memory_repository.py::test_closed_session_is_excluded_from_memory_search -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/memory/csv_memory_repository.py tests/memory/test_csv_memory_repository.py
git commit -m "feat: enforce session lifecycle on csv retrieval"
```

---

### Task 10: Add PostgreSQL repository parity and schema bootstrap

**Files:**
- Create: `app/db/postgres.py`
- Create: `app/memory/postgres_memory_repository.py`
- Create: `references/postgres_init.sql`
- Test: `tests/memory/test_postgres_memory_repository.py`

**Step 1: Write the failing test**

```python
from app.memory.postgres_memory_repository import build_postgres_dsn


def test_build_postgres_dsn_from_config():
    dsn = build_postgres_dsn(
        {
            "host": "localhost",
            "port": 5432,
            "database": "ecommerce_customer_workflow",
            "user": "postgres",
            "password": "secret",
        }
    )

    assert dsn == "postgresql://postgres:secret@localhost:5432/ecommerce_customer_workflow"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/memory/test_postgres_memory_repository.py::test_build_postgres_dsn_from_config -v`
Expected: FAIL because the PostgreSQL repository does not exist yet.

**Step 3: Write minimal implementation**

Create:
- `app/db/postgres.py` with connection helper(s)
- `app/memory/postgres_memory_repository.py` with `PostgresMemoryRepository`
- `references/postgres_init.sql` with tables for sessions, messages, memories, constraints

Include an `embedding` column placeholder in SQL. If pgvector is enabled later, adjust the SQL in a follow-up task rather than blocking this MVP.

Implement at least:

```python
def build_postgres_dsn(config: dict[str, Any]) -> str:
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
```

and wire repository creation so `create_memory_repository(config)` returns the PostgreSQL implementation when configured.

**Step 4: Run test to verify it passes**

Run: `pytest tests/memory/test_postgres_memory_repository.py::test_build_postgres_dsn_from_config -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/db/postgres.py app/memory/postgres_memory_repository.py references/postgres_init.sql tests/memory/test_postgres_memory_repository.py
git commit -m "feat: add postgres session rag repository scaffold"
```

---

### Task 11: Add PostgreSQL install and usage documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/integration.md`
- Test: none

**Step 1: Write the documentation change**

Add a new section to `README.md` explaining:
- CSV is the default backend
- PostgreSQL is optional but recommended for formal deployments
- how to switch backends in `config/default.json`
- where `references/postgres_init.sql` is located

Add a new section to `docs/integration.md` explaining:
- install PostgreSQL
- create database
- run the SQL bootstrap
- enable the postgres backend
- expected lifecycle behavior for active/closed sessions

**Step 2: Review the docs for correctness**

Check that all file paths and config keys match the implementation exactly.

**Step 3: Commit**

```bash
git add README.md docs/integration.md
git commit -m "docs: add session rag backend setup instructions"
```

---

### Task 12: Run focused verification for the session RAG MVP

**Files:**
- Test: `tests/test_models.py`
- Test: `tests/memory/test_memory_repository.py`
- Test: `tests/memory/test_csv_memory_repository.py`
- Test: `tests/memory/test_memory_extractor.py`
- Test: `tests/constraints/test_constraint_builder.py`
- Test: `tests/scripts/test_prepare_request.py`
- Test: `tests/reply/test_reply_builder.py`
- Test: `tests/memory/test_postgres_memory_repository.py`

**Step 1: Run focused tests**

Run: `pytest tests/test_models.py tests/memory/test_memory_repository.py tests/memory/test_csv_memory_repository.py tests/memory/test_memory_extractor.py tests/constraints/test_constraint_builder.py tests/scripts/test_prepare_request.py tests/reply/test_reply_builder.py tests/memory/test_postgres_memory_repository.py -v`
Expected: PASS

**Step 2: Run a manual smoke test for CSV mode**

Run:

```bash
python scripts/prepare_request.py "{\"shop_id\":\"shop-1\",\"session_id\":\"session-1\",\"source_type\":\"text\",\"source_value\":\"我要黑色256G\",\"user_message\":\"我要黑色256G\"}"
```

Expected: JSON output containing `prepared.memory_hits`, `prepared.constraints`, and `prepared.reply_strategy`.

**Step 3: Run a follow-up ambiguity smoke test for CSV mode**

Run:

```bash
python scripts/prepare_request.py "{\"shop_id\":\"shop-1\",\"session_id\":\"session-1\",\"source_type\":\"text\",\"source_value\":\"这个怎么样\",\"user_message\":\"这个怎么样\"}"
```

Expected: JSON output containing non-empty `prepared.memory_hits` or a clarification-oriented `reply_strategy`.

**Step 4: Commit**

```bash
git add -u
git commit -m "test: verify session rag storage mvp"
```

---

### Task 13: Queue the deferred reply customization guide

**Files:**
- Create later: `docs/plans/2026-04-15-reply-customization-guide.md`

**Step 1: Record the follow-up**

Document that the reply customization guide is intentionally deferred until after the session RAG storage MVP is implemented and verified.

**Step 2: Leave implementation for the follow-up task**

No code change in this plan. This task exists to preserve the agreed backlog item only.
