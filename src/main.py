import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.v1.routers import router as v1_api_router
from tasks.tasks import run_background_processes
from views.pages import router as pages


@asynccontextmanager
async def lifespan(app: FastAPI):
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
