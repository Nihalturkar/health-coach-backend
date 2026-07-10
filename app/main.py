from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.redis import init_redis, close_redis
from app.utils.firebase import init_firebase
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.routers import auth as auth_router
from app.routers import profile as profile_router
from app.routers import tracking as tracking_router
from app.routers import progress as progress_router
from app.routers import grocery as grocery_router
from app.routers import notifications as notifications_router
from app.routers import diet as diet_router
from app.routers import workout as workout_router
from app.routers import ai as ai_router
from app.routers import sync as sync_router

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    init_firebase()

    # Schedule cron jobs
    from app.tasks.weekly_review_cron import run_weekly_review_for_all
    from app.tasks.otp_cleanup_cron import cleanup_expired_otps

    scheduler.add_job(run_weekly_review_for_all, "cron", day_of_week="sun", hour=21, minute=0)
    scheduler.add_job(cleanup_expired_otps, "cron", hour=3, minute=0)
    scheduler.start()

    yield

    scheduler.shutdown()
    await close_redis()


app = FastAPI(title="AI Health Coach API", version="1.0.0", lifespan=lifespan)

# Middleware (order matters — outermost first)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=100)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(profile_router.router, prefix="/api/v1")
app.include_router(tracking_router.router, prefix="/api/v1")
app.include_router(progress_router.router, prefix="/api/v1")
app.include_router(grocery_router.router, prefix="/api/v1")
app.include_router(notifications_router.router, prefix="/api/v1")
app.include_router(diet_router.router, prefix="/api/v1")
app.include_router(workout_router.router, prefix="/api/v1")
app.include_router(ai_router.router, prefix="/api/v1")
app.include_router(sync_router.router, prefix="/api/v1")


@app.get("/health")
@app.head("/health")
@app.get("/")
@app.head("/")
async def health():
    return {"status": "ok"}
