import streamlit as st
from backend.database import fetch_all_data, add_new_task, update_task_status
from backend.kpi_logic import calculate_user_kpi, prepare_leaderboard_df
from frontend.ui_components import (
    render_sidebar,
    render_kpi_header,
    render_todo_list,
    render_leaderboard
)

# 1. Konfigurasi Halaman
st.set_page_config(page_title="KPI Quest - Dashboard Karyawan", page_icon="🎯", layout="wide")

# 2. Ambil Data dari Backend
karyawan_list, tugas_list = fetch_all_data()

if not karyawan_list:
    st.warning("Belum ada data karyawan di database.")
    st.stop()

# 3. Render Sidebar & Dapatkan Karyawan Terpilih
karyawan_aktif = render_sidebar(karyawan_list, on_add_task=add_new_task)

# 4. Proses Logika KPI di Backend
kpi_metrics = calculate_user_kpi(tugas_list, karyawan_aktif["id"])
df_leaderboard = prepare_leaderboard_df(karyawan_list, tugas_list)

# 5. Render Tampilan Utama Frontend
render_kpi_header(karyawan_aktif, kpi_metrics)

col_kiri, col_kanan = st.columns([1.4, 1])
with col_kiri:
    render_todo_list(kpi_metrics, on_toggle_task=update_task_status)
with col_kanan:
    render_leaderboard(df_leaderboard)
