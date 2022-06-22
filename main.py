import uvicorn
from app.settings import SERVER_PORT

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="127.0.0.1", port=SERVER_PORT)
