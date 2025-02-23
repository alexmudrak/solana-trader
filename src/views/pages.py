from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "chart.html",
        {"request": request},
    )


@router.get(
    "/create-trader", response_class=HTMLResponse, include_in_schema=False
)
async def read_create_trader(request: Request):
    return templates.TemplateResponse(
        "create_trader.html",
        {"request": request},
    )
