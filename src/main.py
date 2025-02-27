import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from api.v1.routers import router as v1_api_router
from tasks.tasks import run_background_processes
from views.pages import router as pages


def setup_logger():
    logger.remove()
    logger.opt(colors=True)
    logger.level("FETCHER", no=38, color="<light-black>")
    logger.level("ANALYZER", no=39, color="<light-white>")
    logger.level("SELL", no=40, color="<red>")
    logger.level("BUY", no=41, color="<green>")
    logger.level("INDICATOR", no=42, color="<light-yellow>")

    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<light-black>{time:YYYY-MM-DD at HH:mm:ss}</light-black> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>",
        backtrace=True,
        diagnose=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    app.state.check_prices_task = asyncio.create_task(
        run_background_processes()
    )
    yield
    app.state.check_prices_task.cancel()
    await app.state.check_prices_task


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="templates/static"), name="static")
app.include_router(v1_api_router, prefix="/api/v1")
app.include_router(pages)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
