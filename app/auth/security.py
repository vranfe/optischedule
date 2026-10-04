import re
import os
import hashlib
import hmac
import secrets

class PasswordPolicy:
    """
    Industry Standard Password Policy & Validation Service.
    Enforces enterprise security requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 numeric digit (0-9)
    - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?/)
    """
    MIN_LENGTH = 8
    SPECIAL_CHARS = r"""!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`"""

    @classmethod
    def validate_strength(cls, password: str) -> tuple[bool, list[str]]:
        """
        Validates password against enterprise complexity rules.
        :param password: The plain text password to validate
        :return: (is_valid: bool, error_messages: list[str])
        """
        errors = []
        if not password:
            return False, ["La contraseña no puede estar vacía."]

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Debe tener al menos {cls.MIN_LENGTH} caracteres (actual: {len(password)}).")

        if not re.search(r"[A-Z]", password):
            errors.append("Debe contener al menos una letra mayúscula (A-Z).")

        if not re.search(r"[a-z]", password):
            errors.append("Debe contener al menos una letra minúscula (a-z).")

        if not re.search(r"[0-9]", password):
            errors.append("Debe contener al menos un número (0-9).")

        if not re.search(f"[{cls.SPECIAL_CHARS}]", password):
            errors.append("Debe contener al menos un carácter especial (!@#$%^&*-_+=...).")

        return len(errors) == 0, errors

    @classmethod
    def hash_password(cls, raw_password: str) -> str:
        """
        Cryptographically hashes password using PBKDF2-HMAC-SHA256 with random 16-byte salt and 100,000 rounds.
        """
        if not raw_password:
            raise ValueError("Password cannot be empty")
        salt = os.urandom(16)
        iterations = 100_000
        key = hashlib.pbkdf2_hmac('sha256', raw_password.encode('utf-8'), salt, iterations)
        return f"pbkdf2:sha256:{iterations}${salt.hex()}${key.hex()}"

    @classmethod
    def verify_password(cls, raw_password: str, stored_hash_or_plain: str) -> bool:
        """
        Verifies a raw password against stored PBKDF2 hash (or fallback plaintext for migration).
        Uses constant-time comparison to prevent timing attacks.
        """
        if not raw_password or not stored_hash_or_plain:
            return False

        if stored_hash_or_plain.startswith("pbkdf2:sha256:"):
            try:
                parts = stored_hash_or_plain.split("$")
                if len(parts) != 3:
                    return False
                header, salt_hex, key_hex = parts
                iterations = int(header.split(":")[2])
                salt = bytes.fromhex(salt_hex)
                expected_key = bytes.fromhex(key_hex)
                actual_key = hashlib.pbkdf2_hmac('sha256', raw_password.encode('utf-8'), salt, iterations)
                return hmac.compare_digest(expected_key, actual_key)
            except Exception:
                return False
        else:
            # Plaintext fallback for legacy accounts
            return hmac.compare_digest(raw_password, stored_hash_or_plain)

    @classmethod
    def generate_compliant_password(cls, prefix: str = "UMB") -> str:
        """
        Generates a secure password guaranteed to satisfy all policy rules.
        """
        specials = "!@#$%*&_-"
        digits = "23456789"
        upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        lower = "abcdefghijkmnopqrstuvwxyz"
        
        part1 = prefix
        part2 = "".join(secrets.choice(upper) for _ in range(2))
        part3 = "".join(secrets.choice(lower) for _ in range(3))
        part4 = "".join(secrets.choice(digits) for _ in range(2))
        part5 = "".join(secrets.choice(specials) for _ in range(2))
        return f"{part1}{part2}{part3}{part4}{part5}"
