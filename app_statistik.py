import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel, wilcoxon, shapiro, ttest_ind, mannwhitneyu, levene
from streamlit_oauth import OAuth2Component

st.set_page_config(page_title="Statistik Jabodetabek", layout="wide")

# ==============================
# CONFIG SECURITY
# ==============================
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

ALLOWED_DOMAIN = "@shopee.com"
SESSION_TIMEOUT = 1800  # 30 menit

ROLE_MAP = {
    "arrahman@shopee.com": "admin",
    "randy.ilhamzah@shopee.com": "admin",
    "wahdiana.fajar@shopee.com": "user",
    "fajri.razak@shopee.com": "user",
    "firas.abdat@shopee.com": "user",
    "ganesha.dwirama@shopee.com": "user",
    "gilang.mardiana@shopee.com": "user",
    "holmes.lumban@shopee.com": "user",
    "haykal.m@shopee.com": "user",
    "nashira.nattaya@shopee.com": "user",
    "febrian.lewis@shopee.com": "user",
    "riki.pakpahan@shopee.com": "user",
    "risal.umar@shopee.com": "user",
    "rengga.kusumah@shopee.com": "user"
}

# ==============================
# AUTO LOGOUT SYSTEM
# ==============================
def check_timeout():
    if "last_activity" in st.session_state:
        elapsed = time.time() - st.session_state["last_activity"]
        if elapsed > SESSION_TIMEOUT:
            st.warning("Session expired (idle > 30 menit).")
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    st.session_state["last_activity"] = time.time()

check_timeout()

# ==============================
# GOOGLE LOGIN
# ==============================
oauth2 = OAuth2Component(
    CLIENT_ID,
    CLIENT_SECRET,
    "https://accounts.google.com/o/oauth2/auth",
    "https://oauth2.googleapis.com/token",
    REDIRECT_URI,
)

result = oauth2.authorize_button("Login with Google")

if result:
    email = result["email"]

    if not email.endswith(ALLOWED_DOMAIN):
        st.error("Akses ditolak. Hanya email @shopee.com")
        st.stop()

    st.session_state["user_email"] = email
    st.session_state["role"] = ROLE_MAP.get(email, "user")

if "user_email" not in st.session_state:
    st.info("Silakan login menggunakan akun Shopee.")
    st.stop()

user_email = st.session_state["user_email"]
role = st.session_state["role"]

# ==============================
# LOG ACCESS
# ==============================
def log_access(email, role):
    log_file = "access_log.csv"
    now = datetime.datetime.now()

    data = pd.DataFrame([{
        "email": email,
        "role": role,
        "access_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    }])

    try:
        existing = pd.read_csv(log_file)
        updated = pd.concat([existing, data], ignore_index=True)
    except:
        updated = data

    updated.to_csv(log_file, index=False)

if "logged" not in st.session_state:
    log_access(user_email, role)
    st.session_state["logged"] = True

# ==============================
# SIDEBAR INFO
# ==============================
st.sidebar.success(f"Login: {user_email}")
st.sidebar.info(f"Role: {role}")

if st.sidebar.button("Logout"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ==============================
# ADMIN DASHBOARD LOGIN STATS
# ==============================
if role == "admin":
    st.sidebar.markdown("---")
    if st.sidebar.checkbox("🔑 Lihat Statistik Login"):
        try:
            log_df = pd.read_csv("access_log.csv")

            st.subheader("📊 Statistik Login")

            total_login = len(log_df)
            st.metric("Total Login", total_login)

            login_per_day = log_df.groupby("date").size()

            fig = plt.figure()
            login_per_day.plot(kind="line")
            plt.xticks(rotation=45)
            plt.ylabel("Jumlah Login")
            st.pyplot(fig)

            st.dataframe(log_df)

        except:
            st.warning("Belum ada data login.")

# =====================
# SIDEBAR MENU UTAMA
# =====================
menu = st.sidebar.radio(
    "Menu Aplikasi",
    ["📈 Analisis Data", "📘 Panduan Penggunaan", "📊 Contoh Persiapan Data"]
)

# =====================
# PANDUAN
# =====================
if menu == "📘 Panduan Penggunaan":
    st.title("📘 Panduan Penggunaan Aplikasi")

    slide_url = "https://docs.google.com/presentation/d/1Peo8PIa6DiU68Ff4mm1BHP6Sx82q5dZxeKMggz96rqo/embed?start=false&loop=false&delayms=3000"
    st.components.v1.iframe(slide_url, height=650)
    st.stop()

# =====================
# CONTOH DATA
# =====================
if menu == "📊 Contoh Persiapan Data":
    st.title("📊 Contoh Dataset Format Excel")

    sheet_url = "https://docs.google.com/spreadsheets/d/18hWnma_Q3hxMZW71elsveLwdt8ETGycZg9uoivKI448/preview"
    st.components.v1.iframe(sheet_url, height=650)
    st.stop()

# =====================
# ANALISIS DATA
# =====================
if menu == "📈 Analisis Data":

    st.title("📊 Statistik Jabodetabek (Web Version)")

    file = st.file_uploader("Upload Excel / CSV", type=["xlsx", "xls", "csv"])

    if file:

        if file.name.endswith("csv"):
            df = pd.read_csv(file)
        else:
            xls = pd.ExcelFile(file)
            sheet = st.selectbox("Pilih Sheet", xls.sheet_names)
            df = xls.parse(sheet)

        st.subheader("Preview Data")
        st.dataframe(df.head())

        cols = df.columns.tolist()
        col1 = st.selectbox("Kolom 1", cols)
        col2 = st.selectbox("Kolom 2", cols)

        paired = st.selectbox("Pair Checking", ["Tidak", "Ya"])
        method = st.selectbox("Jenis Grafik", ["Boxplot", "Histogram", "Scatterplot"])

        if st.button("Lakukan Analisis"):

            try:
                x = df[col1].dropna().astype(float).values
                y = df[col2].dropna().astype(float).values
            except:
                st.error("Kolom harus angka")
                st.stop()

            if paired == "Ya" and len(x) != len(y):
                st.error("Data harus sama panjang untuk paired test")
                st.stop()

            def describe(arr):
                return np.mean(arr), np.std(arr, ddof=1), len(arr)

            mean_x, std_x, n_x = describe(x)
            mean_y, std_y, n_y = describe(y)

            st.write("Mean 1:", mean_x, "| Mean 2:", mean_y)

            # Independent example (ringkas)
            stat, p = ttest_ind(x, y)
            st.write("p-value:", p)

            fig, ax = plt.subplots()
            ax.boxplot([x, y], labels=[col1, col2])
            st.pyplot(fig)
