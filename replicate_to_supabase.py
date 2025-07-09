import psycopg2
import json
import os
import pandas as pd
from sqlalchemy import create_engine, text
import datetime

# --- Konfigurasi Database ---
# URL koneksi ke Railway PostgreSQL (Sumber)
RAILWAY_DB_URL = "postgresql://postgres:HzsdMMPymOdGjpGrYIxurgkniRswnGqD@interchange.proxy.rlwy.net:31663/railway"

# URL koneksi ke Supabase PostgreSQL (Target)
# Pastikan ini adalah URL Supabase Anda
SUPABASE_DB_URL = "postgresql://postgres.havzfbesxhqzzrohcjeo:root@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

# --- Fungsi untuk mengelola last_processed_log_id di Supabase ---
def get_last_processed_log_id_supabase(supabase_engine):
    query = text("SELECT last_log_id FROM public.replication_progress WHERE consumer_name = 'supabase_replication'")
    with supabase_engine.connect() as conn:
        result = conn.execute(query).scalar_one_or_none()
        return result if result is not None else 0

def save_last_processed_log_id_supabase(supabase_engine, log_id):
    query = text(
        "INSERT INTO public.replication_progress (consumer_name, last_log_id, last_updated) "
        "VALUES ('supabase_replication', :log_id, NOW()) "
        "ON CONFLICT (consumer_name) DO UPDATE SET last_log_id = EXCLUDED.last_log_id, last_updated = EXCLUDED.last_updated"
    )
    with supabase_engine.connect() as conn:
        conn.execute(query, {"log_id": log_id})
        conn.commit()

# --- Fungsi Utama Replikasi ---
def run_supabase_replication():
    source_engine = None
    target_engine = None
    try:
        # Koneksi ke Railway (Sumber)
        source_engine = create_engine(RAILWAY_DB_URL)
        # Koneksi ke Supabase (Target)
        target_engine = create_engine(SUPABASE_DB_URL)

        last_id = get_last_processed_log_id_supabase(target_engine)
        print(f"[{os.path.basename(__file__)}] Memulai replikasi. Terakhir diproses log_id: {last_id}")

        # Ambil perubahan dari tabel public.change_log
        query = text(f"SELECT * FROM public.change_log WHERE log_id > :last_id ORDER BY log_id ASC")
        
        with source_engine.connect() as source_conn:
            changes_df = pd.read_sql(query, source_conn, params={"last_id": last_id})

        if changes_df.empty:
            print(f"[{os.path.basename(__file__)}] Tidak ada perubahan baru untuk direplikasi.")
            return

        max_log_id_in_batch = changes_df['log_id'].max()

        print(f"[{os.path.basename(__file__)}] Ditemukan {len(changes_df)} perubahan baru. Memproses...")
        
        with target_engine.connect() as target_conn:
            trans = target_conn.begin() # Mulai transaksi
            try:
                for index, row in changes_df.iterrows():
                    table_name = row['table_name']
                    op_type = row['operation_type']
                    record_id = row['record_id_pk']
                    new_data = json.loads(row['new_data']) if pd.notna(row['new_data']) and row['new_data'] else None
                    # old_data = json.loads(row['old_data']) if pd.notna(row['old_data']) and row['old_data'] else None

                    print(f"[{os.path.basename(__file__)}] Memproses {op_type} pada tabel '{table_name}' ID: {record_id}")

                    if op_type == 'I': # Insert
                        if new_data:
                            # Menggunakan Pandas to_sql untuk menyisipkan data
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
                save_last_processed_log_id_supabase(target_engine, max_log_id_in_batch)
                print(f"[{os.path.basename(__file__)}] ✅ Replikasi ke Supabase selesai. last_log_id baru: {max_log_id_in_batch}")

            except Exception as e:
                trans.rollback() # Rollback jika ada kesalahan
                print(f"[{os.path.basename(__file__)}] ❌ Error saat mereplikasi ke Supabase: {e}")
                raise # Re-raise exception untuk penanganan lebih lanjut
    except Exception as e:
        print(f"[{os.path.basename(__file__)}] ❌ Error koneksi atau inisialisasi: {e}")
    finally:
        if source_engine:
            source_engine.dispose()
        if target_engine:
            target_engine.dispose()

if __name__ == "__main__":
    run_supabase_replication()