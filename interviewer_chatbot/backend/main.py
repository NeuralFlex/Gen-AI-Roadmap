from fastapi import FastAPI
from routes.start_interview import router as start_interview_router
from routes.continue_interview import router as continue_interview_router

app = FastAPI()

app.include_router(start_interview_router)
app.include_router(continue_interview_router)


@app.get("/")
async def root():
    return {"message": "Interview API is running 🚀"}
