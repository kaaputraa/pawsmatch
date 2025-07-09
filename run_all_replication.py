# adopt_project/run_all_replication.py

# Impor fungsi replikasi dari skrip terpisah
# Pastikan kedua file ini berada di direktori yang sama atau dapat diimpor
from replicate_to_sqlite import run_sqlite_replication
from replicate_to_supabase import run_supabase_replication

import datetime
import os

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Memulai semua proses replikasi...")

    # Jalankan replikasi ke SQLite
    try:
        print(f"[{datetime.datetime.now()}] Menjalankan replikasi ke SQLite...")
        run_sqlite_replication()
        print(f"[{datetime.datetime.now()}] Replikasi SQLite selesai.")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ERROR saat menjalankan replikasi SQLite: {e}")
        # Anda bisa menambahkan logging lebih detail di sini

    # Jalankan replikasi ke Supabase
    try:
        print(f"[{datetime.datetime.now()}] Menjalankan replikasi ke Supabase...")
        run_supabase_replication()
        print(f"[{datetime.datetime.now()}] Replikasi Supabase selesai.")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ERROR saat menjalankan replikasi Supabase: {e}")
        # Anda bisa menambahkan logging lebih detail di sini

    print(f"[{datetime.datetime.now()}] Semua proses replikasi selesai.")