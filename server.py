import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(app ="app.main:app", host="0.0.0.0", port=8008)
    # uvicorn.run(app ="app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

