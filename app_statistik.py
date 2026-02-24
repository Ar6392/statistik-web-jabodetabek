import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, wilcoxon, shapiro, ttest_ind, mannwhitneyu, levene
import matplotlib.pyplot as plt

st.set_page_config(page_title="Statistik Web", layout="wide")
st.title("📊 Statistik Otomatis (Web Version)")

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

        try:
            x = df[col1].dropna().astype(float).values
            y = df[col2].dropna().astype(float).values
        except:
            st.error("Kolom harus numerik")
            st.stop()

        def describe(arr):
            return {
                'Mean': np.mean(arr),
                'Std': np.std(arr, ddof=1),
                'N': len(arr)
            }

        desc_x = describe(x)
        desc_y = describe(y)

        st.subheader("Statistik Deskriptif")
        st.write(desc_x)
        st.write(desc_y)

        result = ""

        is_paired = paired == "Ya"

        if is_paired:
            if len(x) != len(y):
                st.error("Data harus sama panjang untuk paired test")
                st.stop()

            diff = x - y
            _, p_norm = shapiro(diff)
            result += f"Shapiro diff p = {p_norm}\n"

            if p_norm > 0.05:
                stat, p = ttest_rel(x, y)
                result += f"Paired t-test p = {p}\n"
            else:
                stat, p = wilcoxon(x, y)
                result += f"Wilcoxon p = {p}\n"

        else:
            _, p_x = shapiro(x)
            _, p_y = shapiro(y)
            result += f"Shapiro X p={p_x}\n"
            result += f"Shapiro Y p={p_y}\n"

            if p_x > 0.05 and p_y > 0.05:
                _, p_levene = levene(x, y)

                if p_levene > 0.05:
                    stat, p = ttest_ind(x, y, equal_var=True)
                else:
                    stat, p = ttest_ind(x, y, equal_var=False)

                result += f"Independent t-test p = {p}\n"
            else:
                stat, p = mannwhitneyu(x, y)
                result += f"Mann Whitney p = {p}\n"

        st.subheader("Hasil Uji")
        st.text(result)

        # Grafik
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
