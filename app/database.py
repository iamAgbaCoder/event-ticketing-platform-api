# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from sqlalchemy.orm import DeclarativeBase
# from config import get_settings

# settings = get_settings()


# class Base(DeclarativeBase):
#     pass


# engine = create_async_engine(
#     settings.database_url,
#     echo=settings.debug,
#     future=True,
#     # pool_pre_ping=True,
#     # pool_size=10,
#     # max_overflow=20,
# )

# AsyncSessionLocal = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )


# async def get_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close()


from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import get_settings
from utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class Base(DeclarativeBase):
    pass


# --- NEW: Create engine factory to allow fallback ---
async def create_engine_with_fallback():
    """
    Try connecting to the main database. If it fails, fallback to SQLite.
    """
    try:
        logger.info(f"Attempting connection to main DB: {settings.database_url}")
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
        # Try to test connection
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Connected to main database successfully.")
        return engine, False  # Not SQLite
    except Exception as e:
        logger.error(f"Failed to connect to main database: {e}")
        logger.warning("Falling back to SQLite...")

        # Fallback to SQLite
        sqlite_url = "sqlite+aiosqlite:///./fallback.db"
        engine = create_async_engine(sqlite_url, echo=True, future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Using SQLite fallback database.")
        return engine, True  # SQLite mode


# --- Initialize placeholders (to be populated during startup) ---
engine = None
AsyncSessionLocal = None
IS_SQLITE = False


# --- Setup function to be called in FastAPI startup ---
async def setup_database():
    global engine, AsyncSessionLocal, IS_SQLITE
    engine, IS_SQLITE = await create_engine_with_fallback()

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info(f"Database setup complete. Using SQLite: {IS_SQLITE}")


# --- Dependency for DB sessions ---
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
