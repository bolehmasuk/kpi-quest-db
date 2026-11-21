import streamlit as st
from backend.database import fetch_all_data, add_new_task, update_task_status
from backend.kpi_logic import (
    calculate_daily_kpi,
    get_period_analytics,
    generate_sharp_jpg_report,
    compare_employees_data
)
from frontend.ui_components import (
    render_sidebar,
    render_daily_tab,
    render_analytics_tab,
    render_comparison_tab
)

st.set_page_config(page_title="KPI Quest - Dashboard Karyawan", page_icon="🎯", layout="wide")

karyawan_list, tugas_list = fetch_all_data()

if not karyawan_list:
    st.warning("Belum ada data karyawan di database.")
    st.stop()

karyawan_aktif, tanggal_str = render_sidebar(karyawan_list, on_add_task=add_new_task)

st.header(f"Halo, {karyawan_aktif['nama']}! 👋", anchor=False)
st.caption(f"Divisi: **{karyawan_aktif['divisi']}** | Peran: **{karyawan_aktif['role'].capitalize()}**")

tab1, tab2, tab3 = st.tabs([
    "🎯 Misi Harian (To-Do)",
    "📊 Statistik & Download JPG",
    "🏆 Perbandingan Kontribusi Tim"
])

with tab1:
    kpi_harian = calculate_daily_kpi(tugas_list, karyawan_aktif["id"], tanggal_str)
    render_daily_tab(
        karyawan_aktif, tanggal_str, kpi_harian,
        on_toggle_task=update_task_status,
        tugas_list=tugas_list,
        get_analytics_fn=get_period_analytics,
        generate_jpg_fn=generate_sharp_jpg_report
    )


with tab2:
    render_analytics_tab(
        karyawan_aktif, tugas_list,
        get_analytics_fn=get_period_analytics,
        generate_jpg_fn=generate_sharp_jpg_report
    )

with tab3:
    render_comparison_tab(karyawan_list, tugas_list, compare_fn=compare_employees_data)
