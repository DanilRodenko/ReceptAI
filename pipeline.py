FIELDS = ("name", "service", "date", "time", "notes")


def merge_draft(draft: dict, extracted: dict) -> dict:
    merged = dict(draft)
    for field in FIELDS:
        value = extracted.get(field) 
        if value is not None:
            merged[field] = value

    return merged