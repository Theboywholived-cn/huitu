from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes_auth import router as auth_router
from app.api.routes_projects import router as projects_router
from app.api.routes_templates import router as templates_router
from app.api.routes_admin import router as admin_router
from app.db.database import engine, Base, SessionLocal
from app.db.models import User
from app.core.config import settings
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and admin user
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if not exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print(f"Admin user '{settings.ADMIN_USERNAME}' created.")
    finally:
        db.close()
    
    yield
    # Shutdown
    pass


app = FastAPI(
    title="ECharts Lab API",
    description="Private ECharts Lab API for chart templates and projects",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
