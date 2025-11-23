import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db.mongo import connect_to_mongo, close_mongo_connection, get_db
from routers.types_routers.login_logout_router import user_router
from routers.types_routers.admin_router import admin_router
from routers.types_routers.platform_router import platform_router
from routers.types_routers.mission_router import mission_router
from routers.types_routers.user_router import user_crud_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Merhavim Backend",
    version="0.1.0"
)

os.makedirs("static/tts", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],      
    allow_credentials=True,     
    allow_methods=["*"],       
    allow_headers=["*"],      
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    db = get_db()
    await db["users"].create_index("id", unique=True)
    
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    
@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(user_router)
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(mission_router)
app.include_router(user_crud_router)