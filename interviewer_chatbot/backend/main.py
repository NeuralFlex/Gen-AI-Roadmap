from fastapi import FastAPI
from routes.interview import router as interview_router

app = FastAPI()

app.include_router(interview_router)


@app.get("/")
async def root():
    return {"message": "Interview API is running 🚀"}
