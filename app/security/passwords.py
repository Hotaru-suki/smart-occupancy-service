import base64
import hashlib
import hmac
import secrets


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    derived_b64 = base64.b64encode(derived).decode("ascii")
    return f"scrypt$16384$8$1${salt_b64}${derived_b64}"


def verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        return False

    _, n_value, r_value, p_value, salt_b64, derived_b64 = parts
    salt = base64.b64decode(salt_b64.encode("ascii"))
    expected = base64.b64decode(derived_b64.encode("ascii"))

    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=int(n_value),
        r=int(r_value),
        p=int(p_value),
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)
