from fastapi import FastAPI

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


app.include_router(auth_router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"status": "ok"}



