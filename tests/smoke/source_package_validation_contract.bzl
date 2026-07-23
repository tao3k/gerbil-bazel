"""Load-time contracts for fail-closed source-package digest validation."""

load("//gerbil:repository_validation.bzl", "is_hex_digest")

def _expect(value, message):
    if not value:
        fail(message)

def source_package_validation_contract():
    _expect(is_hex_digest("a" * 64, 64), "lowercase SHA-256 must be accepted")
    _expect(is_hex_digest("A1" * 32, 64), "uppercase SHA-256 must be accepted")
    _expect(not is_hex_digest("", 64), "empty SHA-256 must be rejected")
    _expect(not is_hex_digest("a" * 63, 64), "short SHA-256 must be rejected")
    _expect(not is_hex_digest("g" * 64, 64), "non-hex SHA-256 must be rejected")
    _expect(not is_hex_digest(None, 64), "non-string SHA-256 must be rejected")
