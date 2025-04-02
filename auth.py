from starlette.responses import RedirectResponse
from fastapi import Request
from functools import wraps
import inspect
from starlette.middleware.sessions import SessionMiddleware

def add_session_middleware(app):
    app.add_middleware(SessionMiddleware, secret_key="supersecretkey")


def login_required(route_func):
    if inspect.iscoroutinefunction(route_func):
        @wraps(route_func)
        async def async_wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request or not request.session.get("logged_in"):
                return RedirectResponse(url="/login", status_code=303)
            return await route_func(*args, **kwargs)
        return async_wrapper
    else:
        @wraps(route_func)
        def sync_wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request or not request.session.get("logged_in"):
                return RedirectResponse(url="/login", status_code=303)
            return route_func(*args, **kwargs)
        return sync_wrapper

