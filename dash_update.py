import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =============== 🔧 Konfigurasi Halaman (harus di paling atas) ===============
st.set_page_config(page_title="Product Quality Assurance SIG Dashboard", layout="wide")

# =============== 🔗 Logo ======================================================
st.image("SIG_logo.png", width=100)

# =============== 🎨 Tema & Komponen CSS =======================================
st.markdown(
    """
    <style>
    body {
        background-color: #f4f4f4; /* Abu‑abu terang */
    }
    .block-container {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.1);
        border-left: 8px solid #d71920;
    }
    .stButton>button {
        background-color: #d71920;
        color: white;
        font-size: 16px;
        border-radius: 8px;
        padding: 8px 16px;
        border: 2px solid black;
    }
    .stButton>button:hover {
        background-color: #a31518;
    }
    .stSelectbox, .stTextInput, .stNumberInput {
        border-radius: 8px;
        border: 2px solid black;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# ⚙️  Utilitas
# ============================================================================

def _clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Mengganti koma desimal menjadi titik & konversi ke float."""
    obj_cols = df.select_dtypes(include="object").columns
    for col in obj_cols:
        df[col] = (
            df[col]
            .str.replace(".", "", regex=False)  # hapus pemisah ribuan jika ada
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _hitung_prediksi(df: pd.DataFrame) -> pd.DataFrame:
    """Menambah kolom prediksi ke DataFrame (vectorised)."""

    # koefisien model (hasil PCR)
    coef = {
        "intercept": {
            "K1": 203.873,
            "K3": 355.191,
            "K7": 430.582,
            "K28": 538.751,
            "STA": 97.442,
            "STB": 205.375,
        },
        "SiO2": [1.288, -0.275, 1.176, 52.966, 0.997, 0.405],
        "Al2O3": [0.902, 4.510, 1.138, 162.395, -1.093, -0.628],
        "Fe2O3": [-5.521, -3.382, -3.165, -226.411, 0.478, -0.643],
        "CaO": [4.162, 5.175, 4.831, -24.526, 0.760, -1.166],
        "MgO": [-2.728, -1.699, 2.453, 4.539, 1.905, 1.265],
        "SO3": [5.611, -1.236, -0.912, 3.757, -0.514, 1.190],
        "C3S": [0.842, 2.581, 2.422, 32.333, -0.203, -1.068],
        "C2S": [-0.014, -1.634, -0.648, -16.180, 0.548, 0.818],
        "C3A": [3.924, 5.330, 3.126, -210.471, -1.010, -0.114],
        "C4AF": [5.720, -3.265, -2.715, 97.881, 0.517, -0.778],
        "FL": [0.936, 0.508, 3.031, 0.613, -2.730, -1.292],
        "LOI": [-0.304, -1.759, -3.831, -6.829, -0.230, 0.559],
        "Residu": [-6.203, -3.025, -0.306, 0.995, -1.534, -1.034],
        "Blaine": [7.664, 13.976, 10.915, 10.584, -6.875, -5.868],
        "Insoluble": [-0.193, -0.550, -3.064, -0.047, -0.271, 0.278],
        "Na2O": [0.657, 0.119, 2.155, 0.659, 0.596, -1.995],
        "K2O": [1.533, 2.178, -0.962, -3.647, 2.640, 0.109],
    }

    # pastikan kolom tersedia; isi NaN jika tidak ada
    variables = list(coef.keys())[1:]
    for col in variables:
        if col not in df.columns:
            df[col] = np.nan

    # hitung secara vektor
    coefs_arr = np.vstack([coef[var] for var in variables])  # shape (n_vars, 6)
    X = df[variables].values.astype(float)  # (n_samples, n_vars)
    preds = coef["intercept"]["K1"] + X @ coefs_arr[:, 0]
    df["Kuat Tekan 1 Hari"] = preds
    df["Kuat Tekan 3 Hari"] = coef["intercept"]["K3"] + X @ coefs_arr[:, 1]
    df["Kuat Tekan 7 Hari"] = coef["intercept"]["K7"] + X @ coefs_arr[:, 2]
    df["Kuat Tekan 28 Hari"] = coef["intercept"]["K28"] + X @ coefs_arr[:, 3]
    df["Setting Time Awal"] = coef["intercept"]["STA"] + X @ coefs_arr[:, 4]
    df["Setting Time Akhir"] = coef["intercept"]["STB"] + X @ coefs_arr[:, 5]
    return df

# ============================================================================
# 🎯 HEADER
# ============================================================================
st.title("📊 Product Quality Assurance Dashboard")
st.caption("**Author:** Fitri Fatma Dewi (5003221031) | Devi Sagita Rachman (5003221172)")
st.caption("Proyek Kerja Praktek – PT Semen Indonesia (Persero) Tbk | Institut Teknologi Sepuluh Nopember")
st.markdown("---")

# ============================================================================
# 🛠️ Session State
# ============================================================================
if "data_list" not in st.session_state:
    st.session_state.data_list = []

# ============================================================================
# 📥 SIDEBAR – INPUT MANUAL & UPLOAD EXCEL
# ============================================================================
st.sidebar.header("🔢 Masukkan Nilai Variabel (Manual)")
Tanggal = st.sidebar.date_input("📅 Tanggal")
Silo = st.sidebar.text_input("🏗️ Silo")
Peneliti = st.sidebar.text_input("👨‍🔬 Nama Peneliti")

st.sidebar.markdown("---")

cols = st.sidebar.columns(2)
SiO2 = cols[0].number_input("SiO2", value=0.0)
Al2O3 = cols[1].number_input("Al2O3", value=0.0)
Fe2O3 = cols[0].number_input("Fe2O3", value=0.0)
CaO = cols[1].number_input("CaO", value=0.0)
MgO = cols[0].number_input("MgO", value=0.0)
SO3 = cols[1].number_input("SO3", value=0.0)
C3S = cols[0].number_input("C3S", value=0.0)
C2S = cols[1].number_input("C2S", value=0.0)
C3A = cols[0].number_input("C3A", value=0.0)
C4AF = cols[1].number_input("C4AF", value=0.0)
FL = cols[0].number_input("FL", value=0.0)
LOI = cols[1].number_input("LOI", value=0.0)
Residu = cols[0].number_input("Residu", value=0.0)
Blaine = cols[1].number_input("Blaine", value=0.0)
Insoluble = cols[0].number_input("Insoluble", value=0.0)
Na2O = cols[1].number_input("Na2O", value=0.0)
K2O = cols[0].number_input("K2O", value=0.0)

# ==================== Hitung prediksi manual (single row) =====================
kuat_tekan_1d = (
    203.873
    + 0.473 * SiO2
    + 1.507 * Al2O3
    - 5.456 * Fe2O3
    + 4.137 * CaO
    - 0.862 * MgO
    + 1.458 * SO3
    + 1.728 * C3S
    - 1.074 * C2S
    + 4.210 * C3A
    - 5.810 * C4AF
    + 2.923 * FL
    + 0.366 * LOI
    - 5.538 * Residu
    + 7.079 * Blaine
    + 1.027 * Insoluble
    - 1.424 * Na2O
    + 1.923 * K2O
)

kuat_tekan_3d = (
    355.191
    - 0.275 * SiO2
    + 4.510 * Al2O3
    - 3.382 * Fe2O3
    + 5.175 * CaO
    - 1.699 * MgO
    - 1.236 * SO3
    + 2.581 * C3S
    - 1.634 * C2S
    + 5.33 * C3A
    - 3.265 * C4AF
    + 0.508 * FL
    - 1.759 * LOI
    - 3.025 * Residu
    + 13.976 * Blaine
    - 0.550 * Insoluble
    + 0.119 * Na2O
    + 2.178 * K2O
)

kuat_tekan_7d = (
    430.582
    + 0.486 * SiO2
    + 2.930 * Al2O3
    - 3.874 * Fe2O3
    + 2.518 * CaO
    + 0.360 * MgO
    + 1.753 * SO3
    + 0.670 * C3S
    + 0.102 * C2S
    + 4.631 * C3A
    - 3.702 * C4AF
    + 3.677 * FL
    - 2.349 * LOI
    - 2.715 * Residu
    + 5.661 * Blaine
    - 1.830 * Insoluble
    - 2.283 * Na2O
    + 0.702 * K2O
)

kuat_tekan_28d = (
    538.751
    + 0.469 * SiO2
    + 2.809 * Al2O3
    - 1.560 * Fe2O3
    + 1.722 * CaO
    + 0.841 * MgO
    + 1.902 * SO3
    - 0.047 * C3S
    + 0.561 * C2S
    + 3.148 * C3A
    - 1.289 * C4AF
    + 1.791 * FL
    - 2.112 * LOI
    - 0.563 * Residu
    + 3.991 * Blaine
    + 1.328 * Insoluble
    - 1.691 * Na2O
    + 0.476 * K2O
)

setting_time_awal = (
    97.442
    + 0.341 * SiO2
    - 0.956 * Al2O3
    + 0.514 * Fe2O3
    - 1.192 * CaO
    + 0.011 * MgO
    - 2.272 * SO3
    - 0.805 * C3S
    + 0.495 * C2S
    - 1.119 * C3A
    + 0.350 * C4AF
    - 3.100 * FL
    + 1.102 * LOI
    + 0.661 * Residu
    - 2.834 * Blaine
    - 0.494 * Insoluble
    + 1.565 * Na2O
    + 0.297 * K2O
)

setting_time_akhir = (
    205.375
    + 0.379 * SiO2
    - 1.030 * Al2O3
    - 0.264 * Fe2O3
    - 0.674 * CaO
    + 0.020 * MgO
    - 1.000 * SO3
    - 0.324 * C3S
    + 0.352 * C2S
    - 0.570 * C3A
    - 0.296 * C4AF
    - 1.357 * FL
    + 0.047 * LOI
    + 1.457 * Residu
    - 2.225 * Blaine
    - 0.275 * Insoluble
    + 0.703 * Na2O
    - 0.671 * K2O
)

# ======================= Simpan Manual ke session_state =======================
if st.sidebar.button("Simpan Data Manual"):
    st.session_state.data_list.append(
        [
            Tanggal,
            Silo,
            Peneliti,
            SiO2,
            Al2O3,
            Fe2O3,
            CaO,
            MgO,
            SO3,
            C3S,
            C2S,
            C3A,
            C4AF,
            FL,
            LOI,
            Residu,
            Blaine,
            Insoluble,
            Na2O,
            K2O,
            kuat_tekan_1d,
            kuat_tekan_3d,
            kuat_tekan_7d,
            kuat_tekan_28d,
            setting_time_awal,
            setting_time_akhir,
        ]
    )

# ========================== Upload & Proses Excel ============================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Excel (.xlsx)")
uploaded_file = st.sidebar.file_uploader("Pilih file", type=["xlsx"])

if uploaded_file is not None:
    if st.sidebar.button("Proses & Simpan Excel"):
        df_xl = pd.read_excel(uploaded_file)
        df_xl = _clean_numeric(df_xl)
        df_xl = _hitung_prediksi(df_xl)

        # pastikan kolom meta tersedia
        for col in ["Tanggal", "Silo", "Peneliti"]:
            if col not in df_xl.columns:
                df_xl[col] = np.nan
        # urutkan kolom sesuai data_list
        ordered_cols = [
            "Tanggal",
            "Silo",
            "Peneliti",
            "SiO2",
            "Al2O3",
            "Fe2O3",
            "CaO",
            "MgO",
            "SO3",
            "C3S",
            "C2S",
            "C3A",
            "C4AF",
            "FL",
            "LOI",
            "Residu",
            "Blaine",
            "Insoluble",
            "Na2O",
            "K2O",
            "Kuat Tekan 1 Hari",
            "Kuat Tekan 3 Hari",
            "Kuat Tekan 7 Hari",
            "Kuat Tekan 28 Hari",
            "Setting Time Awal",
            "Setting Time Akhir",
        ]
        df_xl = df_xl[ordered_cols]
        st.session_state.data_list.extend(df_xl.values.tolist())
        st.success("✅ Data dari Excel berhasil ditambahkan!")

# ============================================================================
# 📑 Tabs
# ============================================================================
tabs = st.tabs([
    "🔎 Prediksi (Manual)",
    "📋 Data Tersimpan",
    "📈 Analisis Deskriptif",
    "📊 Visualisasi Data",
    "👥 Tentang Kami",
])

# ---------------------------- Tab 0: Prediksi -------------------------------
with tabs[0]:
    st.subheader("📌 Hasil Prediksi (Input Manual Saat Ini)")
    cols_pred = st.columns(2)
    cols_pred[0].metric("🧪 Kuat Tekan 1 Hari", f"{kuat_tekan_1d:.2f} MPa")
    cols_pred[1].metric("🧪 Kuat Tekan 3 Hari", f"{kuat_tekan_3d:.2f} MPa")
    cols_pred[0].metric("🧪 Kuat Tekan 7 Hari", f"{kuat_tekan_7d:.2f} MPa")
    cols_pred[1].metric("🧪 Kuat Tekan 28 Hari", f"{kuat_tekan_28d:.2f} MPa")
    cols_pred[0].metric("⏳ Setting Time Awal", f"{setting_time_awal:.2f} Menit")
    cols_pred[1].metric("⏳ Setting Time Akhir", f"{setting_time_akhir:.2f} Menit")

# --------------------------- Tab 1: DataFrame -------------------------------
with tabs[1]:
    st.subheader("📋 Data Tersimpan (Manual + Excel)")
    df = pd.DataFrame(
        st.session_state.data_list,
        columns=[
            "Tanggal",
            "Silo",
            "Peneliti",
            "SiO2",
            "Al2O3",
            "Fe2O3",
            "CaO",
            "MgO",
            "SO3",
            "C3S",
            "C2S",
            "C3A",
            "C4AF",
            "FL",
            "LOI",
            "Residu",
            "Blaine",
            "Insoluble",
            "Na2O",
            "K2O",
            "Kuat Tekan 1 Hari",
            "Kuat Tekan 3 Hari",
            "Kuat Tekan 7 Hari",
            "Kuat Tekan 28 Hari",
            "Setting Time Awal",
            "Setting Time Akhir",
        ],
    )
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "data_prediksi.csv", "text/csv")

# ---------------------- Tab 2: Analisis Deskriptif ---------------------------
with tabs[2]:
    st.subheader("📈 Analisis Deskriptif")
    st.write(df.describe())

# ----------------------- Tab 3: Visualisasi ----------------------------------
with tabs[3]:
    st.subheader("📊 Visualisasi Data")
    if df.empty:
        st.info("Belum ada data.")
    else:
        main_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
        df["Bulan"] = df["Tanggal"].dt.strftime("%Y-%m")

        var_x = st.selectbox("Pilih Variabel untuk Boxplot", df.columns[3:19])
        fig1 = px.box(
            df,
            x="Bulan",
            y=var_x,
            title=f"Distribusi {var_x} per Bulan",
            color_discrete_sequence=[main_colors[0]],
        )
        st.plotly_chart(fig1)

        var_x_plot = st.selectbox("Pilih Variabel untuk Line Chart", df.columns[3:19])
        df_melted = df.melt(
            id_vars=["Tanggal"],
            value_vars=["Setting Time Awal", "Setting Time Akhir"],
            var_name="Tipe Setting Time",
            value_name="Waktu",
        )
        fig2 = px.bar(
            df_melted,
            x="Tanggal",
            y="Waktu",
            color="Tipe Setting Time",
            barmode="group",
            title="Setting Time + Line {var_x_plot}",
            color_discrete_sequence=[main_colors[1], main_colors[2]],
        )
        fig2.add_scatter(
            x=df["Tanggal"],
            y=df[var_x_plot],
            mode="lines+markers",
            name=var_x_plot,
            line=dict(color=main_colors[3], width=2),
        )
        st.plotly_chart(fig2)

        tekan_vars = [
            "Kuat Tekan 1 Hari",
            "Kuat Tekan 3 Hari",
            "Kuat Tekan 7 Hari",
            "Kuat Tekan 28 Hari",
        ]
        fig3 = go.Figure()
        for i, tekan in enumerate(tekan_vars):
            fig3.add_trace(
                go.Scatter(
                    x=df["Tanggal"],
                    y=df[tekan],
                    mode="lines+markers",
                    name=tekan,
                    line=dict(color=main_colors[i], width=2),
                )
            )
        fig3.update_layout(
            title="Tracking Kuat Tekan 1, 3, 7, 28 Hari",
            xaxis_title="Tanggal",
            yaxis_title="Kuat Tekan",
        )
        st.plotly_chart(fig3)

# --------------------------- Tab 4: Tentang Kami -----------------------------
with tabs[4]:
    st.subheader("👥 Tentang Kami")
    st.markdown(
        """
        **Dashboard Product Quality Assurance** dikembangkan sebagai bagian dari proyek kerja praktik di **PT Semen Indonesia (Persero) Tbk** oleh:

        - **Fitri Fatma Dewi**  
          📧 fitrifatmadewi10@gmail.com  
          📞 +62 857‑3183‑3302  

        - **Devi Sagita Rachman**  
          📧 devisrachmn@gmail.com  
          📞 +62 838‑4432‑2614  

        🏫 **Departemen Statistika | Fakultas Sains dan Analitika Data (FSAD) | Institut Teknologi Sepuluh Nopember | 2025**
        """
    )