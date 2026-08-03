from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.auth.routers import router as auth_router
from app.content.routers import router as content_router
# from app.interactions.routers import router as interactions_router
from fastapi.middleware.cors import CORSMiddleware

from app.interactions.models import VideoReaction, CommentReaction

from sqlalchemy.exc import OperationalError


app = FastAPI()

@app.exception_handler(OperationalError)
async def db_exception_handler(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable, please try again later"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(content_router)
# app.include_router(interactions_router)


@app.get("/")
async def root():
    return {"status": "ok"}



