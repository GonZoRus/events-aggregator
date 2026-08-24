from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from events_aggregator.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)

async_session_maker = async_sessionmaker(
	engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
	async with async_session_maker() as session:
		yield session
