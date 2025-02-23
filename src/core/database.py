from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from core.settings import settings

# TODO: echo state should be linked to APP_MODE
engine = create_async_engine(
    settings.app_db_url,
    echo=False,
    pool_size=20,
    max_overflow=50,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_session():
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception as e:
            print(e)
            await session.rollback()
            raise
        finally:
            try:
                await session.commit()
            except Exception as e:
                print(e)
            await session.close()
