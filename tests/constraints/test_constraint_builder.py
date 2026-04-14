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
