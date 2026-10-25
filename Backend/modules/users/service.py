from common.exceptions import ConflictError, NotFoundError
from modules.users.repository import UserRepository
from modules.auth.repository import AuthRepository


class UserService:
    @staticmethod
    def get_profile(user_id: str) -> dict:
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user.to_dict()

    @staticmethod
    def update_profile(user, data: dict) -> dict:
        if "username" in data:
            new_username = data["username"]
            if new_username.lower().strip() != user.normalized_username:
                existing = UserRepository.get_by_normalized_username(new_username)
                if existing and existing.id != user.id:
                    raise ConflictError("Username is already taken.")
                UserRepository.update_username(user, new_username)
        return {"username": user.username}

    @staticmethod
    def delete_account(user) -> None:
        UserRepository.mark_for_deletion(user)
        AuthRepository.revoke_all_user_sessions(user.id)
