from fastapi import FastAPI
from app.api.routes import clients, auth, appointments, services, notifications
import os
import resend
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise RuntimeError("RESEND_API_KEY environment variable is not set.")
resend.api_key = RESEND_API_KEY


app = FastAPI(title="Manicure Booking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://tudominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(appointments.router,
                   prefix="/appointments", tags=["appointments"])
app.include_router(services.router, prefix="/services", tags=["services"])
app.include_router(notifications.router,
                   prefix="/notifications", tags=["notifications"])
