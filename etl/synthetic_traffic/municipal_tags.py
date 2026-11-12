def municipal_source_confirmed(tags):
    fields = {
        "name",
        "official_name",
        "alt_name",
        "description",
        "official_status",
        "designation",
    }
    return "omkmo:code" in tags or any(
        "муниципал" in value.casefold() for key, value in tags.items() if key in fields
    )
