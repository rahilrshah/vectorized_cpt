from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Vectorized CPT API", description="Medical coding API")

@app.get("/")
def read_root():
    return {"message": "Vectorized CPT API is running", "status": "ok"}

@app.get("/api/status")
def health_check():
    return {"status": "ok", "service": "vectorized-cpt"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)