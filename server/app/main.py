import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.config import settings
from modules.auth.router import router as auth_router
from modules.users.router import router as user_router

class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=UTF8JSONResponse,
)
app.include_router(auth_router)
app.include_router(user_router)
@app.get("/health")
def healthServer():
    return {
        "status" :  True ,
        "message" :  "Server is runing"
    }