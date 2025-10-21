from fastapi import APIRouter, Depends, Query, HTTPException
from api.auth import verify_auth
from scripts.DBprocessor import ProcessDB

router = APIRouter(prefix="/api/events", tags=["Events"])
db = ProcessDB()

@router.post("/", dependencies=[Depends(verify_auth)])
async def create_event(data: dict):
    event_id = db.create_event(data)
    if event_id == -1:
        raise HTTPException(500, "创建事件失败")
    return {"event_id": event_id, "msg": "事件创建成功"}

@router.get("/{event_id}", dependencies=[Depends(verify_auth)])
async def get_event(event_id: int):
    result = db.read_event(event_id)
    if not result:
        raise HTTPException(404, "事件不存在")
    return result

from pydantic import BaseModel
from fastapi import HTTPException


@router.put("/{event_id}", dependencies=[Depends(verify_auth)])
async def update_event(event_id: int, data: dict):
    ok = db.update_event(event_id, data)
    if not ok:
        raise HTTPException(500, "更新失败")
    return {"msg": "事件更新成功", "event_id": event_id}

@router.delete("/{event_id}", dependencies=[Depends(verify_auth)])
async def delete_event(event_id: int):
    ok = db.delete_event(event_id)
    if not ok:
        raise HTTPException(500, "删除失败")
    return {"msg": "事件删除成功", "event_id": event_id}

@router.get("/", dependencies=[Depends(verify_auth)])
async def search_events(
    start_time: str = Query(None),
    end_time: str = Query(None),
    min_importance: int = Query(None)
):
    results = db.search_events_all(start_time=start_time, end_time=end_time, min_importance=min_importance)
    return {"count": len(results), "events": results}
