def settings2meta(settings, section_name="Skill Settings"):
    """ generates basic settingsmeta """
    fields = []

    for k, v in settings.items():
        if k.startswith("_"):
            continue
        if isinstance(v, bool):
            fields.append({
                "name": k,
                "type": "checkbox",
                "label": k,
                "value": str(v).lower()
            })
        if isinstance(v, str):
            fields.append({
                "name": k,
                "type": "text",
                "label": k,
                "value": v
            })
        if isinstance(v, int):
            fields.append({
                "name": k,
                "type": "number",
                "label": k,
                "value": str(v)
            })
    return {
        "skillMetadata": {
            "sections": [
                {
                    "name": section_name,
                    "fields": fields
                }
            ]
        }
    }