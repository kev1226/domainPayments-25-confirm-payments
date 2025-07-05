from fastapi import FastAPI
from app.controllers.payment_controller import payment_router
from app.config import PORT
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o ["http://localhost:5500"] si lo quieres restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(payment_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
