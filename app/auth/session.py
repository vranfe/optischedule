from app.database.models import User, UserRole

class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.current_user = None
        return cls._instance

    def login(self, user: User):
        self.current_user = user

    def logout(self):
        self.current_user = None

    @property
    def is_authenticated(self) -> bool:
        return self.current_user is not None

    @property
    def role(self) -> UserRole:
        return self.current_user.role if self.current_user else None

    @property
    def username(self) -> str:
        return self.current_user.username if self.current_user else ""

    @property
    def teacher_id(self):
        return self.current_user.teacher_id if self.current_user else None

    @property
    def student_id(self):
        return self.current_user.student_id if self.current_user else None

session = SessionManager()
