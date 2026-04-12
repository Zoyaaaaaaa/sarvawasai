from datetime import datetime
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# -------------------- DATABASE --------------------
try:
    from .services.database import connect_to_mongo, close_mongo_connection
except Exception:
    from backend.app.services.database import connect_to_mongo, close_mongo_connection  # type: ignore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
    except Exception as e:
        logging.error(f"MongoDB connection failed on startup: {e}")
        raise e
    yield
    # Shutdown
    try:
        await close_mongo_connection()
    except Exception as e:
        logging.warning(f"MongoDB connection failed on shutdown: {e}")


# -------------------- IMPORT ROUTERS --------------------
# Using absolute imports for consistency
try:
    from .routes import route, ai, schemes, users, auth, ml_similarity, legal_analysis
    from .routes import house_prediction
    from .routes.stepup import router as stepup_router
except Exception as e:
    logging.error(f"Critical import error in main.py: {e}")
    raise e


# -------------------- FASTAPI APP --------------------
app = FastAPI(
    title="React + FastAPI Project",
    lifespan=lifespan,  # 👈 Mongo hooked in here
)

# -------------------- CORS ----------
# Allow requests from localhost and GitHub Codespaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # GitHub Codespaces URLs
        "https://super-duper-couscous-v4x77545rpq2wgp6-5173.app.github.dev",
        "https://super-duper-couscous-v4x77545rpq2wgp6-5174.app.github.dev",
        "https://super-duper-couscous-v4x77545rpq2wgp6-3000.app.github.dev",
        # Localhost
        "https://sarvawasai-d2math1sb-zoya-hassans-projects.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    expose_headers=["Content-Type"],
    max_age=3600,
)

# -------------------- ROUTERS --------------------
app.include_router(auth.router)  # Twilio OTP verification routes
app.include_router(users.router)  # User signup/profile routes
app.include_router(route.router)
app.include_router(ai.router)
app.include_router(stepup_router)
app.include_router(legal_analysis.router)

app.include_router(schemes.router)  # Add the schemes router
app.include_router(ml_similarity.router)  # Add ML similarity router

app.include_router(house_prediction.router)

# Legal Analysis Router
try:
    app.include_router(legal_routes.router)  # Add legal document analysis router
    logging.info("Legal Analysis API routes registered successfully")
except Exception as e:
    logging.warning(f"Legal Analysis routes not available: {e}")

# -------------------- HEALTH CHECKS --------------------
@app.get("/")
async def root():
    return {"message": "FastAPI backend is running!"}


@app.get("/health")
async def overall_health():
    """Overall health check for all services"""
    try:
        from .routes.ai import ModelManager
        model_manager = ModelManager()
        model_loaded = model_manager.is_loaded
    except Exception:
        model_loaded = False

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": {"status": "active"},
            "rera_predictor": {
                "status": "active",
                "model_loaded": model_loaded
            },
            "housing_schemes": {
                "status": "active",
                "agent_configured": True
            },
            "database": {
                "status": "connected"
            }
        }
    }

