from app.database.database import get_db
from app.database.models import User
from app.auth.session import session

class AuthService:
    @staticmethod
    def authenticate(username, password):
        db = next(get_db())
        user = db.query(User).filter(User.username == username.strip()).first()
        if user and user.password == password.strip():
            session.login(user)
            return True, user
        return False, None

    @staticmethod
    def logout():
        session.logout()
