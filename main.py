from fastapi import FastAPI
from db.mongo import connect_to_mongo, close_mongo_connection
from routers.types_routers.user_router import user_router
from routers.types_routers.admin_router import admin_router
from routers.types_routers.platform_router import platform_router
from routers.types_routers.mission_router import mission_router

app = FastAPI(
    title="Merhavim Backend",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    
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
