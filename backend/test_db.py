import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_tables():
    engine = create_async_engine('postgresql+asyncpg://clauseiq_user:clauseiq_pass@localhost:5432/clauseiq_db')
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result.fetchall()]
            print("TABLES IN clauseiq_db:", tables)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(check_tables())
