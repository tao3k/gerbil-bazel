"""Shared validation helpers for repository rules."""

def is_hex_digest(value, length):
    """Returns whether value is a hexadecimal digest of the requested length."""
    if type(value) != "string" or len(value) != length:
        return False
    for character in value.elems():
        if character.lower() not in "0123456789abcdef":
            return False
    return True

def require_hex_digest(value, length, description):
    """Returns a normalized digest or fails closed with a useful error."""
    if not is_hex_digest(value, length):
        fail("{} must contain {} hexadecimal characters".format(description, length))
    return value.lower()
