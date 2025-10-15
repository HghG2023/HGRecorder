from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from scripts.get_date_formate import today
from scripts.path_control import PM
from scripts.unique_string_generate import unique_name
from bbcLearning import bbc
from scripts.logger import logger

# 引入数据库处理类
from scripts.DBprocessor import ProcessDB
from fastapi import Depends

# ----------------- 新增一个依赖函数 -----------------
def verify_auth(request: Request):
    cookie_name = PM.get_env("COOKIE_NAME")
    if request.cookies.get(cookie_name) != "true":
        logger.warning(f"Unauthorized DB access attempt from {request.client.host}")
        raise HTTPException(status_code=401, detail="未授权，请先登录")
    return True

def complete_str(liststr):
    if len(liststr) == 1:
        return liststr[0]
    elif len(liststr) > 1:
        return '、'.join(liststr)
    else:
        return '无'


TEMPLATE_DIR = PM.get_env("TEMPLATES_PATH")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

def create_app() -> FastAPI:
    app = FastAPI(title="HGRecorder API", debug=True)
    db = ProcessDB()

    # ----------------- 数据库 API -----------------
    @app.post("/api/events/", dependencies=[Depends(verify_auth)])
    async def create_event(data: dict):
        event_id = db.create_event(data)
        if event_id == -1:
            raise HTTPException(500, "创建事件失败")
        return {"event_id": event_id, "msg": "事件创建成功"}

    @app.get("/api/events/{event_id}", dependencies=[Depends(verify_auth)])
    async def get_event(event_id: int):
        result = db.read_event(event_id)
        if not result:
            raise HTTPException(404, "事件不存在")
        return result

    @app.put("/api/events/{event_id}", dependencies=[Depends(verify_auth)])
    async def update_event(event_id: int, data: dict):
        ok = db.update_event(event_id, data)
        if not ok:
            raise HTTPException(500, "更新失败")
        return {"msg": "事件更新成功", "event_id": event_id}

    @app.delete("/api/events/{event_id}", dependencies=[Depends(verify_auth)])
    async def delete_event(event_id: int):
        ok = db.delete_event(event_id)
        if not ok:
            raise HTTPException(500, "删除失败")
        return {"msg": "事件删除成功", "event_id": event_id}

    @app.get("/api/events/", dependencies=[Depends(verify_auth)])
    async def search_events(
        start_time: str = Query(None, description="起始时间 YYYY-MM-DD HH:MM:SS"),
        end_time: str = Query(None, description="结束时间 YYYY-MM-DD HH:MM:SS"),
        min_importance: int = Query(None, description="最低重要性")
    ):
        results = db.search_events(start_time=start_time, end_time=end_time, min_importance=min_importance)

        return {"count": len(results), "events": results}


    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        if request.cookies.get(PM.get_env("COOKIE_NAME")) != "true":
            logger.info(f"Unauthorized access attempt to the index page from {request.client.host}.")
            return RedirectResponse("/login")
        files = [f.name for f in Path(PM.get_env("UPLOAD_DIR_PATH")).iterdir() if f.is_file()]
        logger.info(f"Index page accessed from {request.client.host}. Files listed.")
        return templates.TemplateResponse("index.html", {"request": request, "files": files})

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        logger.info(f"Login page accessed from {request.client.host}.")
        return templates.TemplateResponse("login.html", {"request": request, "error": None})

    @app.post("/login", response_class=HTMLResponse)
    async def login_post(request: Request, password: str = Form(...)):
        if password == PM.get_env("PASSWORD"):
            resp = RedirectResponse("/", status_code=303)
            resp.set_cookie(key=PM.get_env("COOKIE_NAME"), value="true", httponly=True, max_age=3600 * 24 * 7)
            
            logger.info(f"Login successful from {request.client.host}.")
            return resp
        logger.warning(f"Failed login attempt with incorrect password from {request.client.host}.")
        return templates.TemplateResponse("login.html", {"request": request, "error": "密码错误，请重试！"})

    
    @app.get("/daily/", response_class=HTMLResponse)
    async def daily_page(request: Request,
        start_time: str = Query(None, description="起始时间 YYYY-MM-DD HH:MM:SS"),
        end_time: str = Query(None, description="结束时间 YYYY-MM-DD HH:MM:SS"),
        min_importance: int = Query(None, description="最低重要性")
    ):
        events = db.search_events(start_time=start_time, end_time=end_time, min_importance=min_importance)
        return templates.TemplateResponse("daily.html", {"request": request, "events": events})
    
    @app.get("/learn/", response_class=HTMLResponse)
    async def learn_page(request: Request):
        article = bbc.doing
        if article is None:
            raise HTTPException(404, "文章不存在")
        else:
            # 标准化路径格式
            if 'path_audio' in article:
                # 确保路径以 userdata/ 开头，并使用正斜杠
                article['path_audio'] = article['path_audio'].replace('\\', '/')
                if not article['path_audio'].startswith('userdata/'):
                    article['path_audio'] = 'userdata/' + article['path_audio']
            
            if 'path_pdf' in article:
                article['path_pdf'] = article['path_pdf'].replace('\\', '/')
                if not article['path_pdf'].startswith('userdata/'):
                    article['path_pdf'] = 'userdata/' + article['path_pdf']

            return templates.TemplateResponse("learn.html", {"request": request, "article": article})

    @app.get("/userdata/{file_path:path}")
    async def get_userdata_file(file_path: str):
        USERDATA_DIR = Path(PM.get_env("USERDATA_DIR_PATH"))

        # 修正：在文件路径前添加 "userdata/" 前缀
        corrected_path = "userdata" / Path(file_path)
        full_path = USERDATA_DIR / corrected_path
  
        # 安全检查
        try:
            full_path.resolve().relative_to(USERDATA_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        # 检查文件是否存在
        if not full_path.exists() or not full_path.is_file():
            # # 列出可能的文件位置
            # if USERDATA_DIR.exists():
            #     print(f"USERDATA_DIR 下的 userdata 目录: {list((USERDATA_DIR / 'userdata').glob('**/*')) if (USERDATA_DIR / 'userdata').exists() else '不存在'}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {full_path}")
        
        # 根据文件类型设置响应
        if file_path.endswith('.pdf'):
            return FileResponse(full_path, media_type='application/pdf')
        elif file_path.endswith('.mp3'):
            return FileResponse(full_path, media_type='audio/mpeg')
        else:
            return FileResponse(full_path)

    return app


