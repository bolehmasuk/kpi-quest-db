import streamlit as st
import plotly.express as px
import pandas as pd

def render_sidebar(karyawan_list: list, on_add_task):
    with st.sidebar:
        st.title("🎯 KPI Quest")
        st.caption("Sistem Penilaian Kinerja Interaktif")
        st.divider()

        opsi_karyawan = {f"{k['nama']} ({k['divisi']})": k for k in karyawan_list}
        pilihan_label = st.selectbox("👤 Lihat Dashboard Milik:", list(opsi_karyawan.keys()))
        karyawan_aktif = opsi_karyawan[pilihan_label]

        st.divider()
        st.subheader("➕ Tambah Misi KPI Baru")
        with st.form("form_tugas_baru", clear_on_submit=True):
            tugas_baru = st.text_input("Deskripsi Tugas / Target")
            bobot_baru = st.slider("Bobot Poin (XP)", min_value=10, max_value=100, value=25, step=5)
            submit_tugas = st.form_submit_button("Simpan ke Database")

            if submit_tugas and tugas_baru:
                on_add_task(karyawan_aktif["id"], tugas_baru, bobot_baru)
                st.success("Misi baru berhasil ditambahkan!")
                st.rerun()

        return karyawan_aktif

def render_kpi_header(karyawan_aktif: dict, kpi_metrics: dict):
    st.header(f"Halo, {karyawan_aktif['nama']}! 👋")
    st.write(f"Divisi: **{karyawan_aktif['divisi']}** | Status Peran: **{karyawan_aktif['role'].capitalize()}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Skor KPI Saat Ini", f"{kpi_metrics['skor_kpi']}%")
    col2.metric("Perolehan XP", f"⚡ {kpi_metrics['xp_didapat']} / {kpi_metrics['total_xp']} XP")
    col3.metric("Level Performa", kpi_metrics['level'])

    st.write("**Progres Penyelesaian Target KPI:**")
    st.progress(kpi_metrics['skor_kpi'] / 100)
    st.divider()

def render_todo_list(kpi_metrics: dict, on_toggle_task):
    st.subheader("📋 Daftar Misi Harian (To-Do List)")
    tugas_user = kpi_metrics["tugas_user"]

    if not tugas_user:
        st.info("Belum ada tugas untuk karyawan ini. Tambahkan melalui menu di sebelah kiri.")
        return

    for t in tugas_user:
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            status_baru = st.checkbox(
                t["deskripsi"],
                value=t["selesai"],
                key=f"chk_{t['id']}"
            )
            if status_baru != t["selesai"]:
                on_toggle_task(t["id"], status_baru)
                st.rerun()
        with c2:
            st.markdown(f"**+{t['bobot_xp']} XP**")

    if kpi_metrics["skor_kpi"] == 100 and kpi_metrics["total_xp"] > 0:
        st.balloons()
        st.success("🎉 Sempurna! Seluruh target KPI telah tercapai 100%!")

def render_leaderboard(df_grafik: pd.DataFrame):
    st.subheader("🏅 Klasemen XP Tim (Leaderboard)")
    fig = px.bar(
        df_grafik,
        x="Total XP",
        y="Nama",
        orientation="h",
        text="Total XP",
        color="Total XP",
        color_continuous_scale="Tealgrn"
    )
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
