import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, wilcoxon, shapiro, ttest_ind, mannwhitneyu, levene
import matplotlib.pyplot as plt

st.set_page_config(page_title="Statistik Jabodetabek", layout="wide")
st.title("📊 Statistik Jabodetabek (Web Version)")

# Upload file
file = st.file_uploader("Upload Excel / CSV", type=["xlsx", "xls", "csv"])

if file:
    # Load data
    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        xls = pd.ExcelFile(file)
        sheet = st.selectbox("Pilih Sheet", xls.sheet_names)
        df = xls.parse(sheet)

    st.write("Preview Data")
    st.dataframe(df.head())

    # Pilih kolom
    cols = df.columns.tolist()
    col1 = st.selectbox("Kolom 1", cols)
    col2 = st.selectbox("Kolom 2", cols)

    paired = st.selectbox("Pair Checking", ["Tidak", "Ya"])
    method = st.selectbox("Jenis Grafik", ["Boxplot", "Histogram", "Scatterplot"])

    if st.button("Lakukan Analisis"):

        # Ambil data numerik
        try:
            x = df[col1].dropna().astype(float).values
            y = df[col2].dropna().astype(float).values
        except:
            st.error("Kolom harus berisi angka")
            st.stop()

        # Jika data terlalu besar (Shapiro max stabil ~5000)
        if len(x) > 5000:
            x_sample = np.random.choice(x, 5000, replace=False)
        else:
            x_sample = x

        if len(y) > 5000:
            y_sample = np.random.choice(y, 5000, replace=False)
        else:
            y_sample = y

        # =====================
        # Statistik Deskriptif
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

        result = ""
        result += "📊 Statistik Deskriptif:\n"
        result += (
            f"- {col1}: Mean={desc_x['Mean']:.3f}, Median={desc_x['Median']:.3f}, "
            f"Std Dev={desc_x['Std']:.3f}, N={desc_x['N']}, "
            f"Min={desc_x['Min']}, Max={desc_x['Max']}\n"
        )
        result += (
            f"- {col2}: Mean={desc_y['Mean']:.3f}, Median={desc_y['Median']:.3f}, "
            f"Std Dev={desc_y['Std']:.3f}, N={desc_y['N']}, "
            f"Min={desc_y['Min']}, Max={desc_y['Max']}\n\n"
        )

        is_paired = paired == "Ya"

        # =====================
        # ANALISIS PAIRED
        # =====================
        if is_paired:

            if len(x) != len(y):
                st.error("Data harus sama panjang untuk paired test")
                st.stop()

            diff = x - y
            _, p_norm = shapiro(diff if len(diff) <= 5000 else np.random.choice(diff, 5000, replace=False))

            result += f"🧪 Normalitas Selisih (Shapiro-Wilk): p = {p_norm:.12e} → {'Normal' if p_norm > 0.05 else 'Tidak Normal'}\n\n"

            if p_norm > 0.05:
                stat, p = ttest_rel(x, y)
                cohen_d = np.mean(diff) / np.std(diff, ddof=1)

                result += (
                    "🔍 Paired t-test:\n"
                    f"t = {stat:.3f}, p-value = {p:.30e}\n"
                    f"Cohen's d = {cohen_d:.3f}"
                )
            else:
                stat, p = wilcoxon(x, y)
                n = len(x)
                rank_biserial = 1 - (2 * stat) / (n * (n + 1) / 2)

                result += (
                    "🔍 Wilcoxon Test:\n"
                    f"W = {stat:.3f}, p-value = {p:.30e}\n"
                    f"Rank biserial = {rank_biserial:.3f}"
                )

        # =====================
        # ANALISIS INDEPENDENT
        # =====================
        else:

            _, p_x = shapiro(x_sample)
            _, p_y = shapiro(y_sample)

            result += f"🧪 Normalitas Group 1 (Shapiro-Wilk): p = {p_x:.12e} → {'Normal' if p_x > 0.05 else 'Tidak Normal'}\n"
            result += f"🧪 Normalitas Group 2 (Shapiro-Wilk): p = {p_y:.12e} → {'Normal' if p_y > 0.05 else 'Tidak Normal'}\n\n"

            if p_x > 0.05 and p_y > 0.05:
                stat_levene, p_levene = levene(x, y)
                result += f"🧪 Levene Test: p = {p_levene:.6f} → {'Homogen' if p_levene > 0.05 else 'Tidak Homogen'}\n\n"

                if p_levene > 0.05:
                    stat, p = ttest_ind(x, y, equal_var=True)
                else:
                    stat, p = ttest_ind(x, y, equal_var=False)

                effect = abs(np.mean(x) - np.mean(y)) / np.sqrt(
                    (np.var(x, ddof=1) + np.var(y, ddof=1)) / 2
                )

                result += (
                    "🔍 Independent t-test:\n"
                    f"t = {stat:.3f}, p-value = {p:.30e}\n"
                    f"Cohen's d = {effect:.3f}"
                )
            else:
                stat, p = mannwhitneyu(x, y, alternative="two-sided")
                n1, n2 = len(x), len(y)
                rank_biserial = 1 - (2 * stat) / (n1 * n2)

                result += (
                    "🔍 Mann–Whitney U Test:\n"
                    f"U = {stat:.3f}, p-value = {p:.30e}\n"
                    f"Rank biserial = {rank_biserial:.3f}"
                )

        # =====================
        # TAMPILKAN HASIL
        # =====================
        st.subheader("Hasil Analisis")
        st.code(result)

        # =====================
        # Grafik
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
