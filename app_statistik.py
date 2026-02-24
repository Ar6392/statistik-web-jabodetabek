import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, wilcoxon, shapiro, ttest_ind, mannwhitneyu, levene
import matplotlib.pyplot as plt

st.set_page_config(page_title="Statistik Jabodetabek", layout="wide")

# =====================
# SIDEBAR MENU
# =====================
menu = st.sidebar.radio(
    "Menu Aplikasi",
    ["📈 Analisis Data", "📘 Panduan Penggunaan", "📊 Contoh Data"]
)

# =====================
# PANDUAN (GOOGLE SLIDES)
# =====================
if menu == "📘 Panduan Penggunaan":
    st.title("📘 Panduan Penggunaan Aplikasi")

    slide_url = "https://docs.google.com/presentation/d/1Peo8PIa6DiU68Ff4mm1BHP6Sx82q5dZxeKMggz96rqo/embed?start=false&loop=false&delayms=3000"
    st.components.v1.iframe(slide_url, height=650)

    st.info("Pastikan Google Slides di-set: Anyone with link → Viewer")
    st.stop()

# =====================
# CONTOH DATA (GOOGLE SHEETS)
# =====================
if menu == "📊 Contoh Persiapan Data":
    st.title("📊 Contoh Dataset Format Excel")

    sheet_url = "https://docs.google.com/spreadsheets/d/18hWnma_Q3hxMZW71elsveLwdt8ETGycZg9uoivKI448/preview"
    st.components.v1.iframe(sheet_url, height=650)

    st.info("Gunakan format ini sebagai acuan sebelum upload data.")
    st.stop()

# =====================
# ANALISIS DATA
# =====================
if menu == "📈 Analisis Data":

    st.title("📊 Statistik Jabodetabek (Web Version)")

    file = st.file_uploader("Upload Excel / CSV", type=["xlsx", "xls", "csv"])

    if file:

        # =====================
        # LOAD DATA
        # =====================
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
                st.error("Kolom harus berisi angka")
                st.stop()

            if paired == "Ya" and len(x) != len(y):
                st.error("Data harus sama panjang untuk paired test")
                st.stop()

            # Sampling jika >5000 untuk Shapiro
            x_sample = np.random.choice(x, 5000, replace=False) if len(x) > 5000 else x
            y_sample = np.random.choice(y, 5000, replace=False) if len(y) > 5000 else y

            # =====================
            # DESKRIPTIF
            # =====================
            def describe(arr):
                return {
                    'Mean': np.mean(arr),
                    'Median': np.median(arr),
                    'Std': np.std(arr, ddof=1),
                    'N': len(arr),
                    'Min': np.min(arr),
                    'Max': np.max(arr)
                }

            desc_x = describe(x)
            desc_y = describe(y)

            result = "📊 Statistik Deskriptif:\n"
            result += f"- {col1}: Mean={desc_x['Mean']:.3f}, Median={desc_x['Median']:.3f}, Std={desc_x['Std']:.3f}, N={desc_x['N']}, Min={desc_x['Min']}, Max={desc_x['Max']}\n"
            result += f"- {col2}: Mean={desc_y['Mean']:.3f}, Median={desc_y['Median']:.3f}, Std={desc_y['Std']:.3f}, N={desc_y['N']}, Min={desc_y['Min']}, Max={desc_y['Max']}\n\n"

            is_paired = paired == "Ya"

            # =====================
            # PAIRED TEST
            # =====================
            if is_paired:

                diff = x - y
                _, p_norm = shapiro(diff if len(diff) <= 5000 else np.random.choice(diff, 5000, replace=False))

                result += f"🧪 Normalitas Selisih: p = {p_norm:.12e}\n\n"

                if p_norm > 0.05:
                    stat, p = ttest_rel(x, y)
                    effect = np.mean(diff) / np.std(diff, ddof=1)
                    result += f"🔍 Paired t-test:\nt = {stat:.3f}\np-value = {p:.30e}\nCohen's d = {effect:.3f}"
                else:
                    stat, p = wilcoxon(x, y)
                    n = len(x)
                    effect = 1 - (2 * stat) / (n * (n + 1) / 2)
                    result += f"🔍 Wilcoxon Test:\nW = {stat:.3f}\np-value = {p:.30e}\nRank biserial = {effect:.3f}"

            # =====================
            # INDEPENDENT TEST
            # =====================
            else:

                _, p_x = shapiro(x_sample)
                _, p_y = shapiro(y_sample)

                result += f"🧪 Normalitas Group 1: p = {p_x:.12e}\n"
                result += f"🧪 Normalitas Group 2: p = {p_y:.12e}\n\n"

                if p_x > 0.05 and p_y > 0.05:

                    stat_levene, p_levene = levene(x, y)
                    result += f"🧪 Levene Test: p = {p_levene:.6f}\n\n"

                    stat, p = ttest_ind(x, y, equal_var=p_levene > 0.05)
                    effect = abs(np.mean(x) - np.mean(y)) / np.sqrt(
                        (np.var(x, ddof=1) + np.var(y, ddof=1)) / 2
                    )

                    result += f"🔍 Independent t-test:\nt = {stat:.3f}\np-value = {p:.30e}\nCohen's d = {effect:.3f}"

                else:

                    stat, p = mannwhitneyu(x, y, alternative="two-sided")
                    n1, n2 = len(x), len(y)
                    effect = 1 - (2 * stat) / (n1 * n2)

                    result += f"🔍 Mann–Whitney U Test:\nU = {stat:.3f}\np-value = {p:.30e}\nRank biserial = {effect:.3f}"

            # =====================
            # RANGKUMAN
            # =====================
            alpha = 0.05
            signif = "Signifikan" if p < alpha else "Tidak Signifikan"

            mean_x = np.mean(x)
            mean_y = np.mean(y)

            if mean_x > mean_y:
                direction = f"{col1} lebih tinggi dari {col2}"
            elif mean_y > mean_x:
                direction = f"{col2} lebih tinggi dari {col1}"
            else:
                direction = "Rata-rata sama"

            result += "\n\n📌 Rangkuman:\n"
            result += f"- Hasil: {signif} (p-value={p:.5f})\n"
            result += f"- Arah: {direction}\n"

            st.subheader("Hasil Analisis")
            st.code(result)

            # =====================
            # GRAFIK
            # =====================
            fig, ax = plt.subplots()

            if method == "Boxplot":
                ax.boxplot([x, y], labels=[col1, col2])
            elif method == "Histogram":
                ax.hist(x, alpha=0.5, label=col1)
                ax.hist(y, alpha=0.5, label=col2)
                ax.legend()
            else:
                ax.scatter(x, y)
                ax.set_xlabel(col1)
                ax.set_ylabel(col2)

            st.pyplot(fig)

