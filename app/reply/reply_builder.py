from __future__ import annotations

from typing import Any

from app.models import build_reply_response

SAFE_FALLBACK = "您好，目前我这边还无法确认您咨询的具体商品信息。您可以补充商品链接、商品截图，或提供型号/规格，我再帮您继续核实。"


def _flatten_facts(knowledge_hits: dict[str, list[dict[str, Any]]]) -> tuple[list[str], list[str]]:
    fact_lines: list[str] = []
    fact_keys: list[str] = []
    for source_name in ("catalog", "faq", "rules"):
        for item in knowledge_hits.get(source_name, []):
            field = str(item.get("field", "info"))
            value = str(item.get("value", "")).strip()
            if not value:
                continue
            fact_lines.append(f"{field}：{value}")
            fact_keys.append(f"{source_name}:{field}")
    return fact_lines, fact_keys


def build_reply_draft(prepared: dict[str, Any]) -> dict[str, Any]:
    user_message = str(prepared.get("user_message", "")).strip()
    knowledge_hits = prepared.get("knowledge_hits") or {"catalog": [], "faq": [], "rules": []}
    fact_lines, fact_keys = _flatten_facts(knowledge_hits)

    if not fact_lines:
        return build_reply_response(
            SAFE_FALLBACK,
            "缺少足够事实信息，返回保守澄清式草稿",
            [],
        )

    intro = "您好，结合当前可确认的信息，先为您整理如下："
    detail = "\n".join(f"- {line}" for line in fact_lines[:5])
    closing = "如果您想确认库存、具体发货时效或订单相关情况，建议再提供商品规格或订单信息，我继续帮您核实。"
    if user_message:
        closing = f"关于您提到的“{user_message}”，目前我能先确认以上信息。{closing}"

    reply_text = f"{intro}\n{detail}\n{closing}"
    return build_reply_response(
        reply_text,
        "基于本地商品/FAQ/规则命中结果生成保守回复草稿",
        fact_keys,
    )
