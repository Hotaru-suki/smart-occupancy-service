from fastapi import APIRouter, Depends, Request, Response, status

from app.infrastructure.logging.json_logger import logger
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    PasswordChangeResponse,
    RegisterRequest,
    RegisterResponse,
    SessionResponse,
)
from app.security.auth import (
    ensure_allowed_origin,
    get_client_id,
    get_cookie_settings,
    get_optional_user,
    require_authenticated_user,
)
from app.services.auth_service import auth_service
from app.security.session_manager import session_manager


def _login_failed_response(
    response: Response,
    status_code: int,
    retry_after_sec: int | None = None,
    remaining_attempts: int | None = None,
):
    response.status_code = status_code
    if retry_after_sec is not None:
        response.headers["Retry-After"] = str(retry_after_sec)
    return LoginResponse(
        authenticated=False,
        username=None,
        role=None,
        expires_at=None,
        retry_after_sec=retry_after_sec,
        remaining_attempts=remaining_attempts,
    )


def create_auth_router():
    router = APIRouter()

    @router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
    def register(payload: RegisterRequest, request: Request, response: Response):
        ensure_allowed_origin(request.headers.get("origin"))
        result = auth_service.register_user(
            username=payload.username,
            password=payload.password,
            role=payload.role,
            admin_registration_code=payload.admin_registration_code,
        )
        if not result.created:
            response.status_code = status.HTTP_200_OK

        logger.info(
            f"注册处理完成: username={result.username}, created={result.created}",
            extra={"event": "auth_register_completed"},
        )
        return RegisterResponse(
            success=True,
            username=result.username,
            role=result.role,
            created=result.created,
        )

    @router.post("/auth/login", response_model=LoginResponse)
    def login(payload: LoginRequest, request: Request, response: Response):
        ensure_allowed_origin(request.headers.get("origin"))
        client_id = get_client_id(request)
        attempts, retry_after = session_manager.get_fail_state(client_id, payload.username)
        if attempts >= session_manager.fail_max_attempts:
            return _login_failed_response(
                response=response,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                retry_after_sec=retry_after,
                remaining_attempts=0,
            )

        identity = auth_service.authenticate_user(
            payload.username,
            payload.password,
            expected_role=payload.role,
        )
        if identity is None:
            attempts, retry_after = session_manager.register_login_failure(client_id, payload.username)
            remaining_attempts = max(session_manager.fail_max_attempts - attempts, 0)
            is_limited = attempts >= session_manager.fail_max_attempts
            logger.warning(
                f"登录失败: client_id={client_id}, attempts={attempts}",
                extra={"event": "auth_login_failed"},
            )
            return _login_failed_response(
                response=response,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS if is_limited else status.HTTP_401_UNAUTHORIZED,
                retry_after_sec=retry_after if is_limited else None,
                remaining_attempts=remaining_attempts,
            )

        session_manager.clear_login_failures(client_id, payload.username)
        session = session_manager.create_session(username=identity.username, role=identity.role)
        response.set_cookie(value=session["token"], **get_cookie_settings())

        logger.info(
            f"登录成功: username={identity.username}, role={identity.role}",
            extra={"event": "auth_login_succeeded"},
        )
        return LoginResponse(
            authenticated=True,
            username=session["username"],
            role=session["role"],
            expires_at=session["expires_at"],
        )

    @router.get("/auth/session", response_model=SessionResponse)
    def get_session(request: Request):
        user = get_optional_user(request)
        if user is None:
            return SessionResponse(authenticated=False)
        return SessionResponse(
            authenticated=True,
            username=user.username,
            role=user.role,
            expires_at=user.expires_at,
        )

    @router.patch("/auth/password", response_model=PasswordChangeResponse)
    def change_password(
        payload: ChangePasswordRequest,
        request: Request,
        user=Depends(require_authenticated_user),
    ):
        ensure_allowed_origin(request.headers.get("origin"))
        updated = auth_service.change_password(
            username=user.username,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        logger.info(
            f"密码修改成功: username={updated.username}",
            extra={"event": "auth_password_changed"},
        )
        return PasswordChangeResponse(success=True, username=updated.username)

    @router.post("/auth/logout", response_model=SessionResponse)
    def logout(request: Request, response: Response):
        ensure_allowed_origin(request.headers.get("origin"))
        token = request.cookies.get(session_manager.cookie_name)
        session_manager.destroy_session(token)
        response.delete_cookie(session_manager.cookie_name, path="/")
        return SessionResponse(authenticated=False)

    return router
