from fastapi import FastAPI

from app.auth.routers import router as auth_router
from app.content.routers import router as content_router
# from app.interactions.routers import router as interactions_router
from fastapi.middleware.cors import CORSMiddleware

from app.interactions.models import VideoReaction, CommentReaction


app = FastAPI()

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



