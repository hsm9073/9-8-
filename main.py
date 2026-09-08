import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="칼로리 유난히 많았던 날",
    page_icon="🍱",
    layout="wide"
)

st.title("🍱 칼로리 유난히 많았던 날")
st.caption("급식 식단 데이터를 바탕으로 평소보다 칼로리가 높았던 날을 찾아보는 앱입니다.")

@st.cache_data
def load_data():
    df = pd.read_csv("급식식단정보.csv")
    df["칼로리_kcal"] = (
        df["칼로리정보"].astype(str)
        .str.extract(r"([\d,]+(?:\.\d+)?)")[0]
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    df["급식일자_dt"] = pd.to_datetime(df["급식일자"].astype(str), format="%Y%m%d", errors="coerce")
    return df

df = load_data()

st.sidebar.header("🔎 조건 설정")

schools = sorted(df["학교명"].dropna().unique())
school = st.sidebar.selectbox("학교", schools)

meal_options = ["전체"] + sorted(df["식사명"].dropna().unique().tolist())
meal = st.sidebar.selectbox("식사", meal_options)

top_n = st.sidebar.slider("표시할 고칼로리 급식 수", 5, 30, 10)

filtered = df[df["학교명"] == school].copy()

if meal != "전체":
    filtered = filtered[filtered["식사명"] == meal]

filtered = filtered.dropna(subset=["칼로리_kcal"]).sort_values("칼로리_kcal", ascending=False)

if filtered.empty:
    st.warning("조건에 맞는 급식 데이터가 없습니다.")
    st.stop()

# 평균과 기준값
mean_kcal = filtered["칼로리_kcal"].mean()
std_kcal = filtered["칼로리_kcal"].std()
high_cut = mean_kcal + std_kcal if pd.notna(std_kcal) else mean_kcal

# 가장 칼로리가 높은 날
max_row = filtered.iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("평균 칼로리", f"{mean_kcal:,.1f} kcal")
c2.metric("최고 칼로리", f"{max_row['칼로리_kcal']:,.1f} kcal")
c3.metric("평균보다 높은 급식", f"{(filtered['칼로리_kcal'] > mean_kcal).sum()}개")

st.divider()

st.subheader("🔥 칼로리가 유난히 많았던 날")
st.write(f"평균 **{mean_kcal:,.1f} kcal**보다 높고, 평균 + 표준편차(**{high_cut:,.1f} kcal**)를 넘는 급식을 강조했습니다.")

outliers = filtered[filtered["칼로리_kcal"] >= high_cut].copy()

if outliers.empty:
    st.info("평균 + 표준편차 기준을 넘는 급식이 없습니다. 아래의 전체 순위에서 높은 날을 확인해 보세요.")
else:
    for _, row in outliers.iterrows():
        menu = re.sub(r"<br\\s*/?>", " · ", str(row["요리명"]))
        menu = re.sub(r"<[^>]+>", "", menu)
        st.markdown(
            f"### 📅 {row['급식일자_dt'].strftime('%Y-%m-%d') if pd.notna(row['급식일자_dt']) else row['급식일자']}"
        )
        st.write(f"**{row['칼로리_kcal']:,.1f} kcal**")
        st.write(f"🍽️ {menu}")
        st.divider()

st.subheader("📊 고칼로리 급식 TOP")
top = filtered.head(top_n).copy()
top["날짜"] = top["급식일자_dt"].dt.strftime("%Y-%m-%d")
top["칼로리"] = top["칼로리_kcal"]

st.bar_chart(top.set_index("날짜")["칼로리"])

display_df = top[["날짜", "식사명", "칼로리", "요리명"]].copy()
display_df["요리명"] = (
    display_df["요리명"].astype(str)
    .str.replace(r"<br\s*/?>", " / ", regex=True)
    .str.replace(r"<[^>]+>", "", regex=True)
)
display_df.columns = ["급식일자", "식사", "칼로리(kcal)", "메뉴"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.info("💡 '유난히 많았던 날'은 선택한 조건의 평균 칼로리에 표준편차를 더한 값을 기준으로 판단합니다.")
