FIELDS = ("name", "service", "date", "time", "notes")

REQUIRED_FIELDS = ("name", "service", "date", "time")

def merge_draft(draft: dict, extracted: dict) -> dict:
    merged = dict(draft)
    for field in FIELDS:
        value = extracted.get(field) 
        if value is not None:
            merged[field] = value

    return merged


def missing_fields(draft: dict) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not draft.get(field)]