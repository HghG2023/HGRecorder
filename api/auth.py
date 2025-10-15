from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from scripts.path_control import PM
from scripts.logger import logger
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory=str(PM.get_env("TEMPLATES_PATH")))

# ---- 权限校验依赖 ----
def verify_auth(request: Request):
    cookie_name = PM.get_env("COOKIE_NAME")
    if request.cookies.get(cookie_name) != "true":
        logger.warning(f"未授权访问：{request.client.host}")
        raise HTTPException(status_code=401, detail="未授权，请先登录")
    return True

# ---- 登录页面 ----
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

# ---- 登录验证 ----
@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, password: str = Form(...)):
    if password == PM.get_env("PASSWORD"):
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(key=PM.get_env("COOKIE_NAME"), value="true", httponly=True, max_age=3600 * 24 * 7)
        logger.info(f"登录成功：{request.client.host}")
        return resp
    logger.warning(f"登录失败：{request.client.host}")
    return templates.TemplateResponse("login.html", {"request": request, "error": "密码错误！"})
