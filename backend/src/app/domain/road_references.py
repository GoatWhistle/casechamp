import re

LOOKALIKES = str.maketrans("abcehkmoptxy", "авсенкмортху")


def compact(value: str) -> str:
    return re.sub(r"[^a-zа-яё0-9]", "", value.casefold())


def reference_key(value: str) -> str:
    return compact(value).translate(LOOKALIKES).replace("ё", "е")


def reference_parts(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def lookup_keys(value: str) -> list[str]:
    return sorted({compact(value), reference_key(value)} - {""})


def shared_reference(references: set[str], requested: str) -> list[str]:
    parts = {part for reference in references for part in reference_parts(reference)}
    wanted = reference_key(requested)
    direct = sorted(part for part in parts if reference_key(part) == wanted)
    if direct:
        return direct
    common = (
        set.intersection(
            *(
                {reference_key(part) for part in reference_parts(reference)}
                for reference in references
            )
        )
        if references
        else set()
    )
    if len(common) == 1:
        key = next(iter(common))
        return sorted(part for part in parts if reference_key(part) == key)
    return []
