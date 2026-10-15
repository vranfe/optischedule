from sqlalchemy.orm import joinedload
from app.database.database import get_db, SessionLocal
from app.database.models import User
from app.auth.session import session
from app.auth.security import PasswordPolicy

class AuthService:
    @staticmethod
    def authenticate(username, password):
        db = SessionLocal()
        try:
            user = db.query(User).options(
                joinedload(User.teacher),
                joinedload(User.student)
            ).filter(User.username == username.strip()).first()
            if user and PasswordPolicy.verify_password(password.strip(), user.password):
                session.login(user)
                return True, user
            return False, None
        finally:
            db.close()

    @staticmethod
    def logout():
        session.logout()

    @staticmethod
    def update_password(user_id: int, new_password: str) -> tuple[bool, str]:
        """
        Validates password against enterprise complexity rules, hashes it with PBKDF2, and updates user.
        """
        is_valid, errors = PasswordPolicy.validate_strength(new_password)
        if not is_valid:
            return False, "\n• " + "\n• ".join(errors)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "Usuario no encontrado."
            user.password = PasswordPolicy.hash_password(new_password)
            db.commit()
            return True, "Contraseña actualizada exitosamente."
        except Exception as e:
            db.rollback()
            return False, f"Error en base de datos: {e}"
        finally:
            db.close()
