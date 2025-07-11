import psycopg2
import sqlite3
import pandas as pd
import json
import os
from sqlalchemy import create_engine, text

# --- Konfigurasi Database ---
# URL koneksi ke Railway PostgreSQL (Sumber)
# Pastikan ini adalah PUBLIC URL dari Railway Anda
RAILWAY_DB_URL = "postgresql://postgres:HzsdMMPymOdGjpGrYIxurgkniRswnGqD@interchange.proxy.rlwy.net:31663/railway"

# Path ke database SQLite (Target)
SQLITE_DB_PATH = "warehouse.db"

# Nama file untuk menyimpan ID log terakhir yang diproses
LAST_LOG_ID_FILE_SQLITE = "last_log_id_sqlite.txt"

# --- Fungsi untuk mengelola last_processed_log_id ---
def get_last_processed_log_id(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read().strip()
                return int(content) if content else 0
        return 0
    except (ValueError, FileNotFoundError):
        return 0

def save_last_processed_log_id(file_path, log_id):
    with open(file_path, 'w') as f:
        f.write(str(log_id))

# --- Fungsi Utama Replikasi ---
def run_sqlite_replication():
    source_engine = None
    target_engine = None
    try:
        # Koneksi ke Railway (Sumber)
        source_engine = create_engine(RAILWAY_DB_URL)
        # Koneksi ke SQLite (Target)
        target_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')

        last_id = get_last_processed_log_id(LAST_LOG_ID_FILE_SQLITE)
        print(f"[{os.path.basename(__file__)}] Memulai replikasi. Terakhir diproses log_id: {last_id}")

        # Ambil perubahan dari tabel public.change_log
        # Menggunakan text() untuk memastikan string kueri diinterpretasikan dengan benar oleh SQLAlchemy
        query = text(f"SELECT * FROM public.change_log WHERE log_id > :last_id ORDER BY log_id ASC")
        
        with source_engine.connect() as source_conn:
            changes_df = pd.read_sql(query, source_conn, params={"last_id": last_id})

        if changes_df.empty:
            print(f"[{os.path.basename(__file__)}] Tidak ada perubahan baru untuk direplikasi.")
            return

        max_log_id_in_batch = changes_df['log_id'].max()
        
        print(f"[{os.path.basename(__file__)}] Ditemukan {len(changes_df)} perubahan baru. Memproses...")

        with target_engine.connect() as target_conn:
            # Mulai transaksi untuk memastikan atomicity
            trans = target_conn.begin()
            try:
                for index, row in changes_df.iterrows():
                    table_name = row['table_name']
                    op_type = row['operation_type']
                    record_id = row['record_id_pk']
                    new_data = json.loads(row['new_data']) if pd.notna(row['new_data']) and row['new_data'] else None
                    # old_data = json.loads(row['old_data']) if pd.notna(row['old_data']) and row['old_data'] else None # Tidak selalu dibutuhkan

                    print(f"[{os.path.basename(__file__)}] Memproses {op_type} pada tabel '{table_name}' ID: {record_id}")

                    if op_type == 'I': # Insert
                        if new_data:
                            pd.DataFrame([new_data]).to_sql(table_name, target_conn, if_exists='append', index=False)
                    elif op_type == 'U': # Update
                        if new_data:
                            # Implementasi UPDATE: hapus baris lama berdasarkan PK, lalu masukkan baris baru
                            # ASUMSI: Primary key di tabel tujuan juga bernama 'id'
                            target_conn.execute(text(f"DELETE FROM {table_name} WHERE id = :record_id"), {"record_id": record_id})
                            pd.DataFrame([new_data]).to_sql(table_name, target_conn, if_exists='append', index=False)
                    elif op_type == 'D': # Delete
                        # ASUMSI: Primary key di tabel tujuan juga bernama 'id'
                        target_conn.execute(text(f"DELETE FROM {table_name} WHERE id = :record_id"), {"record_id": record_id})
                    else:
                        print(f"[{os.path.basename(__file__)}] Operasi tidak dikenal: {op_type}")
                
                trans.commit() # Commit transaksi jika semua berhasil
                save_last_processed_log_id(LAST_LOG_ID_FILE_SQLITE, max_log_id_in_batch)
                print(f"[{os.path.basename(__file__)}] ✅ Replikasi ke SQLite selesai. last_log_id baru: {max_log_id_in_batch}")

            except Exception as e:
                trans.rollback() # Rollback jika ada kesalahan
                print(f"[{os.path.basename(__file__)}] ❌ Error saat mereplikasi ke SQLite: {e}")
                raise # Re-raise exception untuk penanganan lebih lanjut
    except Exception as e:
        print(f"[{os.path.basename(__file__)}] ❌ Error koneksi atau inisialisasi: {e}")
    finally:
        if source_engine:
            source_engine.dispose()
        if target_engine:
            target_engine.dispose()

if __name__ == "__main__":
    run_sqlite_replication()