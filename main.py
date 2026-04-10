from fastapi import FastAPI, Depends
from database import get_db, engine, Base

from apps.auth.routers import router as auth_router
from apps.api.routers import router as api_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"status": "ok"}



