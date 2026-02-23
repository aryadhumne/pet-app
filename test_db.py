import psycopg2

try:
    conn = psycopg2.connect(
        host="aws-0-YOUR-REGION.pooler.supabase.com",
        database="postgres",
        user="postgres",
        password="YOUR_PASSWORD",
        port="6543"
    )
    print("✅ Connected successfully!")
    conn.close()

except Exception as e:
    print("❌ Connection failed:")
    print(e)