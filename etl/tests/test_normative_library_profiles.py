from normative_civic_sources import municipal_service


def test_regional_and_institutional_libraries_do_not_enter_local_service() -> None:
    assert municipal_service("library", "Курганская областная библиотека") == "regional_library"
    assert municipal_service("library", "Областная специальная библиотека") == "regional_library"
    assert (
        municipal_service("library", "Медицинский информационно-аналитический центр")
        == "institutional_library"
    )
    assert municipal_service("library", "Центральная городская библиотека") == "library"
    assert municipal_service("library", "Детская библиотека") == "children_library"
    assert municipal_service("library", "Библиотека КГСХА") == "institutional_library"
    assert municipal_service("school", "Областная школа") == "school"
