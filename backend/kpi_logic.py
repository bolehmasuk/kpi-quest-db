import pandas as pd
import io
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calculate_daily_kpi(tugas_list: list, karyawan_id: int, tanggal_str: str) -> dict:
    tugas_user = [
        t for t in tugas_list 
        if t["karyawan_id"] == karyawan_id and str(t.get("tanggal")) == tanggal_str
    ]
    total_xp = sum(t["bobot_xp"] for t in tugas_user)
    xp_didapat = sum(t["bobot_xp"] for t in tugas_user if t["selesai"])
    skor_kpi = int((xp_didapat / total_xp) * 100) if total_xp > 0 else 0

    if skor_kpi >= 85:
        level = "🏆 Grandmaster"
    elif skor_kpi >= 60:
        level = "🔥 Achiever"
    elif skor_kpi >= 30:
        level = "⚡ Rising Star"
    else:
        level = "🌱 Rookie"

    return {
        "tugas_user": tugas_user,
        "total_xp": total_xp,
        "xp_didapat": xp_didapat,
        "skor_kpi": skor_kpi,
        "level": level
    }

def get_period_analytics(tugas_list: list, karyawan_id: int, start_str: str, end_str: str) -> pd.DataFrame:
    filtered = [
        t for t in tugas_list
        if t["karyawan_id"] == karyawan_id and start_str <= str(t.get("tanggal")) <= end_str
    ]
    if not filtered:
        return pd.DataFrame()
    
    df = pd.DataFrame(filtered)
    df["Status"] = df["selesai"].apply(lambda x: "✅ Selesai" if x else "⏳ Belum")
    df["XP Diperoleh"] = df.apply(lambda r: r["bobot_xp"] if r["selesai"] else 0, axis=1)
    return df

def generate_sharp_jpg_report(df_period: pd.DataFrame, nama_karyawan: str, start_str: str, end_str: str) -> bytes:
    """Membuat laporan visual berbeda: Rincian Poin per Misi (Harian) vs Tren Harian (Periode)."""
    is_daily = (start_str == end_str)

    total_xp_periode = df_period["XP Diperoleh"].sum()
    total_target_periode = df_period["bobot_xp"].sum()
    persen = int((total_xp_periode / total_target_periode) * 100) if total_target_periode > 0 else 0

    if is_daily:
        # Jika 1 hari: tampilkan perbandingan XP per masing-masing tugas
        judul_laporan = f"<b>RINGKASAN MISI HARIAN: {nama_karyawan.upper()}</b>"
        sub_judul = f"Tanggal: {start_str} | Skor KPI Harian: {persen}% ({total_xp_periode}/{total_target_periode} XP)"
        judul_grafik = "Perolehan XP per Item Tugas"
        x_data = df_period["deskripsi"]
        y_data = df_period["XP Diperoleh"]
        warna_bar = "#3B82F6" # Biru untuk laporan harian
    else:
        # Jika rentang tanggal: tampilkan tren akumulasi XP per tanggal
        daily_summary = df_period.groupby("tanggal", as_index=False)["XP Diperoleh"].sum().sort_values("tanggal")
        judul_laporan = f"<b>LAPORAN KINERJA PERIODE: {nama_karyawan.upper()}</b>"
        sub_judul = f"Periode: {start_str} s/d {end_str} | Skor KPI: {persen}% ({total_xp_periode}/{total_target_periode} XP)"
        judul_grafik = "Tren Akumulasi XP Harian"
        x_data = daily_summary["tanggal"].astype(str)
        y_data = daily_summary["XP Diperoleh"]
        warna_bar = "#00CC96" # Hijau untuk laporan periode

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.52, 0.48],
        specs=[[{"type": "xy"}], [{"type": "table"}]],
        vertical_spacing=0.16,
        subplot_titles=(judul_grafik, "Rincian Daftar Tugas")
    )

    fig.add_trace(
        go.Bar(
            x=x_data,
            y=y_data,
            text=y_data,
            textposition="auto",
            marker_color=warna_bar
        ),
        row=1, col=1
    )

    df_table = df_period[["tanggal", "deskripsi", "XP Diperoleh", "Status"]].tail(15)
    fig.add_trace(
        go.Table(
            header=dict(
                values=["<b>Tanggal</b>", "<b>Deskripsi Misi</b>", "<b>XP</b>", "<b>Status</b>"],
                fill_color="#1E293B",
                font=dict(color="white", size=12),
                align="left"
            ),
            cells=dict(
                values=[df_table["tanggal"].astype(str), df_table["deskripsi"], df_table["XP Diperoleh"], df_table["Status"]],
                fill_color="#F8FAFC",
                font=dict(color="#0F172A", size=11),
                align="left",
                height=24
            )
        ),
        row=2, col=1
    )

    fig.update_xaxes(type="category", row=1, col=1) # Memastikan sumbu X bersih tanpa tulisan jam 23:59:59
    fig.update_layout(
        title=dict(
            text=f"{judul_laporan}<br><span style='font-size:13px; color:#475569;'>{sub_judul}</span>",
            x=0.03
        ),
        width=1000,
        height=780,
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        showlegend=False,
        margin=dict(t=95, b=30, l=40, r=40)
    )

    png_bytes = fig.to_image(format="png", scale=2)
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    jpg_buffer = io.BytesIO()
    img.save(jpg_buffer, format="JPEG", quality=85, optimize=True)
    return jpg_buffer.getvalue()


def compare_employees_data(karyawan_list: list, tugas_list: list, start_str: str, end_str: str) -> pd.DataFrame:
    rows = []
    for k in karyawan_list:
        t_k = [
            t for t in tugas_list
            if t["karyawan_id"] == k["id"] and start_str <= str(t.get("tanggal")) <= end_str
        ]
        target_xp = sum(t["bobot_xp"] for t in t_k)
        xp_dapat = sum(t["bobot_xp"] for t in t_k if t["selesai"])
        jml_tugas = len(t_k)
        jml_selesai = sum(1 for t in t_k if t["selesai"])
        tingkat_kpi = round((xp_dapat / target_xp) * 100, 1) if target_xp > 0 else 0.0

        rows.append({
            "Karyawan": k["nama"],
            "Divisi": k["divisi"],
            "Total XP": xp_dapat,
            "Target XP": target_xp,
            "Tugas Selesai": f"{jml_selesai}/{jml_tugas}",
            "Skor KPI (%)": tingkat_kpi
        })

    return pd.DataFrame(rows).sort_values(by="Total XP", ascending=False)
