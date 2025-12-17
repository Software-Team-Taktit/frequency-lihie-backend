from models.requests.user_request import UserCreateRequest, UserUpdateRequest, UserLogInRequest

class AdminCreateRequest(UserCreateRequest):
    pass
    
class AdminUpdateRequest(UserUpdateRequest):
    pass

class AdminLogInRequest(UserLogInRequest):
    pass