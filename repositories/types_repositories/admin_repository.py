from repositories.types_repositories.user_repository import UserRepository

class AdminRepository(UserRepository):
    def __init__(self):
        super().__init__()
        self.collection = self.collection.database["admins"]