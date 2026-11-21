import pandas as pd
import io
from PIL import Image
import matplotlib.pyplot as plt

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
    """Membuat laporan visual tajam & ringan dalam format JPG menggunakan Matplotlib (100% kompatibel Cloud)."""
    is_daily = (start_str == end_str)

    total_xp_periode = df_period["XP Diperoleh"].sum()
    total_target_periode = df_period["bobot_xp"].sum()
    persen = int((total_xp_periode / total_target_periode) * 100) if total_target_periode > 0 else 0

    if is_daily:
        judul_laporan = f"RINGKASAN MISI HARIAN: {nama_karyawan.upper()}"
        sub_judul = f"Tanggal: {start_str}  |  Skor KPI Harian: {persen}% ({total_xp_periode}/{total_target_periode} XP)"
        judul_grafik = "Perolehan XP per Item Tugas"
        x_labels = [d[:22] + "..." if len(d) > 22 else d for d in df_period["deskripsi"]]
        y_values = df_period["XP Diperoleh"].tolist()
        warna_bar = "#3B82F6"
    else:
        daily_summary = df_period.groupby("tanggal", as_index=False)["XP Diperoleh"].sum().sort_values("tanggal")
        judul_laporan = f"LAPORAN KINERJA PERIODE: {nama_karyawan.upper()}"
        sub_judul = f"Periode: {start_str} s/d {end_str}  |  Skor KPI: {persen}% ({total_xp_periode}/{total_target_periode} XP)"
        judul_grafik = "Tren Akumulasi XP Harian"
        x_labels = daily_summary["tanggal"].astype(str).tolist()
        y_values = daily_summary["XP Diperoleh"].tolist()
        warna_bar = "#00CC96"

    # Siapkan kanvas gambar 2 baris (Atas: Grafik Batang, Bawah: Tabel Rincian)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.2), dpi=180, gridspec_kw={"height_ratios": [1.1, 1]})
    fig.patch.set_facecolor("white")

    # Header Utama
    fig.suptitle(judul_laporan, fontsize=15, fontweight="bold", x=0.05, y=0.96, ha="left", color="#0F172A")
    fig.text(0.05, 0.925, sub_judul, fontsize=10.5, color="#475569")

    # Bagian 1: Grafik Batang
    bars = ax1.bar(x_labels, y_values, color=warna_bar, width=0.45)
    ax1.set_title(judul_grafik, fontsize=11.5, fontweight="bold", loc="left", pad=12, color="#1E293B")
    ax1.set_facecolor("#F8FAFC")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.tick_params(axis="x", labelsize=9)
    batas_atas = max(y_values) * 1.25 if y_values and max(y_values) > 0 else 10
    ax1.set_ylim(0, batas_atas)


    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f"{int(height)} XP",
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, fontweight="bold", color="#0F172A")

    # Bagian 2: Tabel Rincian Tugas (Maksimal 12 baris terakhir agar tetap terbaca jelas)
    ax2.axis("off")
    ax2.set_title("Rincian Daftar Tugas", fontsize=11.5, fontweight="bold", loc="left", pad=8, color="#1E293B")

    df_table = df_period[["tanggal", "deskripsi", "XP Diperoleh", "Status"]].tail(12).copy()
    df_table["Status"] = df_table["Status"].str.replace("✅ ", "", regex=False).str.replace("⏳ ", "", regex=False)
    df_table["deskripsi"] = df_table["deskripsi"].apply(lambda x: x[:42] + "..." if len(x) > 42 else x)

    table_data = df_table.astype(str).values.tolist()
    col_labels = ["Tanggal", "Deskripsi Misi", "XP", "Status"]

    table = ax2.table(
        cellText=table_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="left",
        colWidths=[0.16, 0.54, 0.12, 0.18]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#CBD5E1")
        if row == 0:
            cell.set_facecolor("#1E293B")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#F8FAFC" if row % 2 == 1 else "white")

    plt.tight_layout(rect=[0.03, 0.02, 0.97, 0.90])

    # Konversi kanvas ke JPG terkompresi (tajam & ringan)
    png_buffer = io.BytesIO()
    plt.savefig(png_buffer, format="png", dpi=180)
    plt.close(fig)

    png_buffer.seek(0)
    img = Image.open(png_buffer).convert("RGB")
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
