from apps.api.app.utils.password import hash_password, verify_password


def test_hash_password_generates_unique_salt():
    password = "StrongPass1!"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    assert hashed1 != hashed2
    assert verify_password(password, hashed1)
    assert verify_password(password, hashed2)
    assert not verify_password("WrongPass1!", hashed1)
