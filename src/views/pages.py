from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "chart.html",
        {"request": request, "active_tab": "chart"},
    )


@router.get(
    "/create-pair", response_class=HTMLResponse, include_in_schema=False
)
async def read_create_pair(request: Request):
    return templates.TemplateResponse(
        "create_pair.html",
        {"request": request, "active_tab": "create-pair"},
    )


@router.get("/add-token", response_class=HTMLResponse, include_in_schema=False)
async def read_add_token(request: Request):
    return templates.TemplateResponse(
        "add_token.html",
        {"request": request, "active_tab": "add-token"},
    )
