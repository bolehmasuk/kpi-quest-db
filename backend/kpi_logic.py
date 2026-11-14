import pandas as pd

def calculate_user_kpi(tugas_list: list, karyawan_id: int) -> dict:
    tugas_user = [t for t in tugas_list if t["karyawan_id"] == karyawan_id]
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

def prepare_leaderboard_df(karyawan_list: list, tugas_list: list) -> pd.DataFrame:
    data_grafik = []
    for k in karyawan_list:
        t_k = [t for t in tugas_list if t["karyawan_id"] == k["id"]]
        xp_k = sum(t["bobot_xp"] for t in t_k if t["selesai"])
        data_grafik.append({"Nama": k["nama"], "Total XP": xp_k})
    
    return pd.DataFrame(data_grafik).sort_values(by="Total XP", ascending=True)
