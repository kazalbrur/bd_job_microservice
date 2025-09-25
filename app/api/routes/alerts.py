from fastapi import APIRouter, Request
from typing import List
from pydantic import BaseModel

from app.main import limiter

alert_router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
	id: int
	user_id: int
	keywords: str


@alert_router.get("/", response_model=List[AlertResponse])
@limiter.limit("20/minute")
async def list_alerts(request: Request):
	return []
