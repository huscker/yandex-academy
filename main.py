import uvicorn
from app.settings import SERVER_PORT

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=SERVER_PORT)
