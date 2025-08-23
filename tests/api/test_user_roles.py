from apps.api.app.dependencies import User


def test_user_roles_are_independent() -> None:
    """Ensure User instances do not share roles lists."""
    user_one = User(sub="1")
    user_two = User(sub="2")
    user_one.roles.append("admin")

    assert user_one.roles == ["admin"]
    assert user_two.roles == []
