from sqlalchemy.ext.asyncio import (
	AsyncSession, create_async_engine, async_sessionmaker)



DATABASE_URL = "postgresql+asyncpg://events_user:password_db@localhost:5433/events"

engine = create_async_engine(DATABASE_URL)

async_session_maker = async_sessionmaker(
	engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
	async with async_session_maker() as session:
		yield session
