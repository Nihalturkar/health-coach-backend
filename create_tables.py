"""One-time script to create all tables on production database."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def create():
    from app.database import engine, Base
    from app.models import *  # Import all models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("All tables created!")
    await engine.dispose()

asyncio.run(create())
