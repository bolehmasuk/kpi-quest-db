import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date, timedelta

def render_sidebar(karyawan_list: list, on_add_task):
    with st.sidebar:
        st.title("🎯 KPI Quest", anchor=False)
        st.caption("Sistem Penilaian Kinerja Interaktif")
        st.divider()

        opsi_karyawan = {f"{k['nama']} ({k['divisi']})": k for k in karyawan_list}
        pilihan_label = st.selectbox("👤 Pilih Profil Karyawan:", list(opsi_karyawan.keys()))
        karyawan_aktif = opsi_karyawan[pilihan_label]

        # Pemilih Tanggal Aktif (Bisa pilih hari ini s/d 3 bulan ke depan)
        tanggal_aktif = st.date_input("📅 Tanggal Misi Harian:", value=date.today())
        tanggal_str = tanggal_aktif.strftime("%Y-%m-%d")

        st.divider()
        st.subheader("➕ Tambah Misi KPI Baru", anchor=False)
        with st.form("form_tugas_baru", clear_on_submit=True):
            tugas_baru = st.text_input("Deskripsi Tugas / Target")
            bobot_baru = st.slider("Bobot Poin (XP)", min_value=10, max_value=100, value=25, step=5)
            submit_tugas = st.form_submit_button("Simpan ke Database")

            if submit_tugas and tugas_baru:
                on_add_task(karyawan_aktif["id"], tugas_baru, bobot_baru, tanggal_str)
                st.success(f"Misi untuk {tanggal_str} tersimpan!")
                st.rerun()

        return karyawan_aktif, tanggal_str

def render_daily_tab(karyawan_aktif: dict, tanggal_str: str, kpi_metrics: dict, on_toggle_task, tugas_list: list, get_analytics_fn, generate_jpg_fn):
    st.subheader(f"Misi Tanggal: {tanggal_str}", anchor=False)
    col1, col2, col3 = st.columns(3)
    col1.metric("Skor KPI Harian", f"{kpi_metrics['skor_kpi']}%")
    col2.metric("Perolehan XP", f"⚡ {kpi_metrics['xp_didapat']} / {kpi_metrics['total_xp']} XP")
    col3.metric("Level Harian", kpi_metrics['level'])

    st.progress(kpi_metrics['skor_kpi'] / 100)
    st.divider()

    tugas_user = kpi_metrics["tugas_user"]
    if not tugas_user:
        st.info(f"Belum ada misi terjadwal pada tanggal **{tanggal_str}**. Tambahkan lewat menu di sebelah kiri.")
        return

    for t in tugas_user:
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            status_baru = st.checkbox(t["deskripsi"], value=t["selesai"], key=f"chk_{t['id']}")
            if status_baru != t["selesai"]:
                on_toggle_task(t["id"], status_baru)
                st.rerun()
        with c2:
            st.markdown(f"**+{t['bobot_xp']} XP**")

    if kpi_metrics["skor_kpi"] == 100 and kpi_metrics["total_xp"] > 0:
        st.balloons()
        st.success("🎉 Sempurna! Seluruh target KPI pada tanggal ini telah tercapai 100%!")

    # Tambahan Tombol Download Ringkasan Misi Harian (.JPG)
    st.divider()
    df_harian = get_analytics_fn(tugas_list, karyawan_aktif["id"], tanggal_str, tanggal_str)
    if not df_harian.empty:
        jpg_harian = generate_jpg_fn(df_harian, karyawan_aktif["nama"], tanggal_str, tanggal_str)
        st.download_button(
            label="📸 Download Ringkasan Misi Harian (.JPG)",
            data=jpg_harian,
            file_name=f"Misi_Harian_{karyawan_aktif['nama'].replace(' ', '_')}_{tanggal_str}.jpg",
            mime="image/jpeg",
            key="btn_download_harian"
        )


def render_analytics_tab(karyawan_aktif: dict, tugas_list: list, get_analytics_fn, generate_jpg_fn):
    st.subheader(f"📊 Statistik & Rekap Kinerja: {karyawan_aktif['nama']}", anchor=False)
    
    default_start = date.today() - timedelta(days=7)
    rentang = st.date_input(
        "Pilih Rentang Tanggal Analisis:",
        value=(default_start, date.today()),
        key="range_analytics"
    )

    if len(rentang) != 2:
        st.warning("Silakan pilih tanggal mulai dan tanggal akhir pada kalender.")
        return

    start_str = rentang[0].strftime("%Y-%m-%d")
    end_str = rentang[1].strftime("%Y-%m-%d")

    df_period = get_analytics_fn(tugas_list, karyawan_aktif["id"], start_str, end_str)

    if df_period.empty:
        st.info(f"Tidak ada data tugas pada rentang **{start_str}** hingga **{end_str}**.")
        return

    # Metrik Ringkasan Periode
    total_xp = df_period["XP Diperoleh"].sum()
    target_xp = df_period["bobot_xp"].sum()
    selesai_count = len(df_period[df_period["selesai"] == True])
    skor_periode = int((total_xp / target_xp) * 100) if target_xp > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Rata-rata Skor KPI", f"{skor_periode}%")
    m2.metric("Total XP Terkumpul", f"⚡ {total_xp} / {target_xp} XP")
    m3.metric("Misi Diselesaikan", f"{selesai_count} dari {len(df_period)} Misi")

    # Visualisasi Grafik Tren XP Harian
    daily_df = df_period.groupby("tanggal", as_index=False)["XP Diperoleh"].sum()
    fig_trend = px.area(
        daily_df, x="tanggal", y="XP Diperoleh", markers=True,
        title="Grafik Tren Perolehan XP Harian",
        color_discrete_sequence=["#00CC96"]
    )
    fig_trend.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_trend, use_container_width=True)

    # Tabel Rincian Tugas
    st.markdown("**📋 Tabel Rincian Aktivitas & XP:**")
    tampil_df = df_period[["tanggal", "deskripsi", "bobot_xp", "XP Diperoleh", "Status"]].rename(
        columns={"tanggal": "Tanggal", "deskripsi": "Misi / Tugas", "bobot_xp": "Bobot XP"}
    )
    st.dataframe(tampil_df, use_container_width=True, hide_index=True)

    # Tombol Download Laporan Visual JPG
    jpg_data = generate_jpg_fn(df_period, karyawan_aktif["nama"], start_str, end_str)
    st.download_button(
        label="📸 Download Ringkasan Visual (.JPG Tajam & Ringan)",
        data=jpg_data,
        file_name=f"Laporan_KPI_{karyawan_aktif['nama'].replace(' ', '_')}_{start_str}_sd_{end_str}.jpg",
        mime="image/jpeg"
    )

def render_comparison_tab(karyawan_list: list, tugas_list: list, compare_fn):
    st.subheader("🏆 Perbandingan Kontribusi Antar Karyawan", anchor=False)

    default_start = date.today() - timedelta(days=30)
    rentang_tim = st.date_input(
        "Pilih Periode Evaluasi Tim:",
        value=(default_start, date.today()),
        key="range_team"
    )

    if len(rentang_tim) != 2:
        st.warning("Silakan pilih tanggal mulai dan tanggal akhir.")
        return

    start_str = rentang_tim[0].strftime("%Y-%m-%d")
    end_str = rentang_tim[1].strftime("%Y-%m-%d")

    df_comp = compare_fn(karyawan_list, tugas_list, start_str, end_str)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig_bar = px.bar(
            df_comp, x="Karyawan", y=["Total XP", "Target XP"],
            barmode="group", title="Perbandingan XP Tercapai vs Target XP",
            color_discrete_map={"Total XP": "#00CC96", "Target XP": "#636EFA"}
        )
        fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(
    fig_bar,
    use_container_width=True,
    config={"toImageButtonOptions": {"format": "jpeg", "filename": "Perbandingan_Kontribusi_Tim", "scale": 2}}
)


    with col_chart2:
        if df_comp["Total XP"].sum() > 0:
            fig_pie = px.pie(
                df_comp, names="Karyawan", values="Total XP",
                hole=0.45, title="Proporsi Kontribusi XP Tim (%)"
            )
            fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(
    fig_pie,
    use_container_width=True,
    config={"toImageButtonOptions": {"format": "jpeg", "filename": "Proporsi_Kontribusi_Tim", "scale": 2}}
)
        else:
            st.info("Belum ada perolehan XP tim pada periode ini untuk ditampilkan pada diagram proporsi.")

    st.markdown("**📊 Klasemen & Tabel Perbandingan Detail:**")
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
