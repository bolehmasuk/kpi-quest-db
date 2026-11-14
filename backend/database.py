import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def fetch_all_data():
    supabase = init_connection()
    res_karyawan = supabase.table("karyawan").select("*").order("id").execute()
    res_tugas = supabase.table("tugas").select("*").order("id").execute()
    return res_karyawan.data, res_tugas.data

def add_new_task(karyawan_id: int, deskripsi: str, bobot_xp: int):
    supabase = init_connection()
    supabase.table("tugas").insert({
        "karyawan_id": karyawan_id,
        "deskripsi": deskripsi,
        "bobot_xp": bobot_xp,
        "selesai": False
    }).execute()

def update_task_status(task_id: int, selesai: bool):
    supabase = init_connection()
    supabase.table("tugas").update({"selesai": selesai}).eq("id", task_id).execute()
