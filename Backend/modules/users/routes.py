from flask import Blueprint, request
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies
from common.responses import success_response
from modules.users.schemas import validate_update_user_input
from modules.users.service import UserService

users_bp = Blueprint("users", __name__)


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    return success_response(
        message="User profile retrieved successfully.",
        data=current_user.to_dict(),
        status_code=200,
    )


@users_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_current_user():
    data = request.get_json(silent=True) or {}
    validated_data = validate_update_user_input(data)
    result = UserService.update_profile(current_user, validated_data)
    return success_response(
        message="Profile updated successfully.",
        data=result,
        status_code=200,
    )


@users_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_current_user():
    UserService.delete_account(current_user)
    response = success_response(
        message="Account deletion request received.",
        status_code=200,
    )
    unset_jwt_cookies(response)
    return response
