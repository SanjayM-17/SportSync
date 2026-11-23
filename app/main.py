from fastapi import FastAPI
from app.routers.booking import router as booking_router

app = FastAPI(
    title="SportSync API",
    description="Smart Campus Sports Resource Allocation and Recommendation System",
    version="1.0.0"
)

app.include_router(booking_router)


@app.get("/")
def home():
    return {
        "project": "SportSync",
        "message": "Welcome to SportSync!",
        "status": "Backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}