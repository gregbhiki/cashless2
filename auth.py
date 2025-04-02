from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from functools import wraps

def add_session_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

def login_required(route_func):
    @wraps(route_func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request") or args[0]
        if request.session.get("logged_in") != True:
            return RedirectResponse(url="/login", status_code=303)
        return await route_func(*args, **kwargs)
    return wrapper
