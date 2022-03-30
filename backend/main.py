from pydantic.main import BaseModel
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home() -> str:
    return "Working."

class My_Number_Class(BaseModel):
    number: int

@app.post("/square")
def square(data:My_Number_Class):
    number = data.number
    return str(number*number)

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
