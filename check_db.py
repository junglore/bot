import asyncio
import asyncpg

async def check_tables():
    conn = await asyncpg.connect('postgresql://postgres:Ankita@007@localhost:5432/Junglore_KE')
    
    # Check if users table exists
    result = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
    """)
    
    print("Users table structure:")
    for row in result:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    await conn.close()

asyncio.run(check_tables())
