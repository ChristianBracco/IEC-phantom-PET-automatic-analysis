import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# PATH
# ============================================================

HOT_FILE = Path(r"D:\IECAnalysisPyhton\FolderPrefix\outputMetaTargets.xlsx")
BG_FILE  = Path(r"D:\IECAnalysisPyhton\PET_OF_A10_T5\outputMetaTargets.xlsx")

OUTPUT_FILE = Path(r"D:\IECAnalysisPyhton\IEC_NEMA_Report.xlsx")

SHEET = "Meta data per sphere"
TRUE_ACTIVITY_RATIO = 3

PHILIPS_VARIABILITY_REF = {
    "10": 7.9,
    "13": 6.4,
    "17": 5.1,
    "22": 4.0,
    "28": 3.3,
    "37": 2.9,  # cold
}
SPHERE_DIAMETER_MAP = {
    "B1": 10,
    "B2": 13,
    "B3": 17,
    "B4": 22,
    "B5": 28,
    "B6": 37,  # cold
}

# ============================================================
# LOAD
# ============================================================

def load_hot():
    return pd.read_excel(HOT_FILE, sheet_name=SHEET)


def load_bg():
    return pd.read_excel(BG_FILE, sheet_name=SHEET)

# ============================================================
# BACKGROUND (NEMA)
# ============================================================

def compute_background_nema(bg_df):
    B = bg_df["Mean"].mean()
    sigma_B = np.sqrt(bg_df["Variance"].mean())
    variability = sigma_B / B * 100
    return B, sigma_B, variability

# ============================================================
# CONTRAST NEMA
# ============================================================

def compute_contrast_nema(hot_df, B, true_ratio):
    out = hot_df.copy()
    out["Contrast_Raw"] = (out["Mean"] - B) / B
    out["Contrast_Recovery_%"] = (out["Contrast_Raw"] / (true_ratio - 1)) * 100
    return out[["Sphere", "Mean", "Contrast_Recovery_%"]]

# ============================================================
# VARIABILITY NEMA
# ============================================================

def compute_variability_nema(bg_df):
    mean_bg = bg_df["Mean"].mean()
    sigma_bg = np.sqrt(bg_df["Variance"].mean())
    return sigma_bg / mean_bg * 100


def compute_variability_table(hot_df, bg_df):
    rows = []
    variability_meas = compute_variability_nema(bg_df)

    for _, r in hot_df.iterrows():
        sphere = r["Sphere"]
        diameter = SPHERE_DIAMETER_MAP.get(sphere)

        ref = PHILIPS_VARIABILITY_REF.get(str(diameter))

        if ref is not None:
            var_pct = (variability_meas - ref) / ref * 100
            giudizio = "ok" if abs(var_pct) <= 10 else "fail"
        else:
            var_pct = None
            giudizio = ""

        rows.append({
            "Sfera": f"Sfera Ø {diameter} mm {'hot' if diameter != 37 else 'cold'}",
            "Misura Philips Prova di Accettazione": ref,
            "Misura": round(variability_meas, 2),
            "Var %": round(var_pct) if var_pct is not None else None,
            "Giudizio [10 % PVS]": giudizio
        })

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def run_iec_analysis():

    hot_df = load_hot()
    bg_df  = load_bg()

    # --- BACKGROUND ---
    B, sigma_B, variability_global = compute_background_nema(bg_df)

    # --- CONTRAST ---
    contrast_df = compute_contrast_nema(
        hot_df, B, TRUE_ACTIVITY_RATIO
    )

    # --- VARIABILITY GLOBALE ---
    variability_global_df = pd.DataFrame([{
        "Background mean": B,
        "Background sigma": sigma_B,
        "Variability_NEMA_%": round(variability_global, 2),
        "Giudizio (≤10%)": "ok" if variability_global <= 10 else "fail"
    }])

    # --- VARIABILITY PER SFERA ---
    variability_table_df = compute_variability_table(
        hot_df, bg_df
    )

    # --- WRITE EXCEL ---
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        contrast_df.to_excel(
            writer, sheet_name="CONTRAST_NEMA", index=False
        )
        variability_global_df.to_excel(
            writer, sheet_name="VARIABILITY_GLOBALE", index=False
        )
        variability_table_df.to_excel(
            writer, sheet_name="VARIABILITY_PER_SFERA", index=False
        )

    print("\n✅ Analisi IEC / NEMA completata")
    print(f"📄 Output: {OUTPUT_FILE}")

# ============================================================
# EXEC
# ============================================================

if __name__ == "__main__":
    run_iec_analysis()
