from sleep_coach.release_version import DEFAULT_DEV_VERSION, resolve_release_version


def test_resolve_release_version_prefers_explicit_env_override():
    version = resolve_release_version(
        {
            "SLEEP_COACH_VERSION": "0.2.0",
            "GITHUB_REF_NAME": "v9.9.9",
        },
        tag_lookup=lambda: "v1.0.0",
    )

    assert version == "0.2.0"


def test_resolve_release_version_uses_github_tag_name():
    version = resolve_release_version(
        {"GITHUB_REF_NAME": "v0.1.3"},
        tag_lookup=lambda: None,
    )

    assert version == "0.1.3"


def test_resolve_release_version_uses_exact_git_tag_when_available():
    version = resolve_release_version({}, tag_lookup=lambda: "v1.4.5")

    assert version == "1.4.5"


def test_resolve_release_version_falls_back_to_dev_version():
    version = resolve_release_version({}, tag_lookup=lambda: None)

    assert version == DEFAULT_DEV_VERSION
