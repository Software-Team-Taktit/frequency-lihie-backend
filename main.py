from fastapi import FastAPI
from db.mongo import connect_to_mongo, close_mongo_connection

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