import psycopg2
import sqlite3
import pandas as pd

# Koneksi ke Railway PostgreSQL (ganti dengan URL kamu)
source_conn = psycopg2.connect(
    "postgresql://postgres:HzsdMMPymOdGjpGrYIxurgkniRswnGqD@interchange.proxy.rlwy.net:31663/railway"
)

# Koneksi ke SQLite (lokal)
target_conn = sqlite3.connect("warehouse.db")

# Tabel-tabel yang akan direplikasi
tables = ["adoption_user", "adoption_animal", "adoption_appointment"]

for table in tables:
    print(f"📥 Mengambil data dari tabel: {table}")
    df = pd.read_sql(f"SELECT * FROM {table}", source_conn)
    
    print(f"📦 Menyimpan ke SQLite: {table}")
    df.to_sql(table, target_conn, if_exists='replace', index=False)

print("✅ Replikasi selesai. Data tersedia di warehouse.db")

# Tutup koneksi
source_conn.close()
target_conn.close()
