import streamlit as st
import pandas as pd
import re

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="요일별 급식 영양 분석",
    page_icon="🍱",
    layout="wide"
)

# =========================================================
# 스타일
# =========================================================
st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        color: #777;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .info-box {
        padding: 18px;
        border-radius: 15px;
        background-color: #f5f7fa;
        margin-bottom: 15px;
    }

    .insight-box {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
        background-color: #ffffff;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 제목
# =========================================================
st.markdown(
    '<div class="main-title">🍱 요일별 급식 영양 분석</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '급식 데이터를 이용해 요일에 따라 칼로리와 영양 균형이 어떻게 달라지는지 분석합니다.'
    '</div>',
    unsafe_allow_html=True
)

# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():
    df = pd.read_csv("급식식단정보.csv", encoding="utf-8-sig")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["급식일자"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    # 칼로리 숫자 추출
    df["칼로리"] = pd.to_numeric(
        df["칼로리정보"].astype(str).str.extract(r"([\d,]+\.?\d*)")[0]
        .str.replace(",", ""),
        errors="coerce"
    )

    # 영양정보에서 각 영양소 추출
    def get_nutrient(text, name):
        pattern = name + r"\s*:\s*([\d.]+)"
        result = re.search(pattern, str(text))
        if result:
            return float(result.group(1))
        return None

    df["탄수화물"] = df["영양정보"].apply(
        lambda x: get_nutrient(x, "탄수화물\\(g\\)")
    )

    df["단백질"] = df["영양정보"].apply(
        lambda x: get_nutrient(x, "단백질\\(g\\)")
    )

    df["지방"] = df["영양정보"].apply(
        lambda x: get_nutrient(x, "지방\\(g\\)")
    )

    # 요일
    weekday_map = {
        0: "월요일",
        1: "화요일",
        2: "수요일",
        3: "목요일",
        4: "금요일",
        5: "토요일",
        6: "일요일"
    }

    df["요일"] = df["날짜"].dt.weekday.map(weekday_map)

    # 평일만 분석
    df = df[df["요일"].isin(
        ["월요일", "화요일", "수요일", "목요일", "금요일"]
    )]

    return df


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.info("main.py와 급식식단정보.csv가 같은 폴더에 있는지 확인해주세요.")
    st.stop()

# =========================================================
# 데이터 정리
# =========================================================
df = df.dropna(subset=["날짜", "칼로리"])

weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일"]

# =========================================================
# 사이드바
# =========================================================
st.sidebar.header("⚙️ 분석 설정")

selected_weekdays = st.sidebar.multiselect(
    "분석할 요일",
    weekday_order,
    default=weekday_order
)

if not selected_weekdays:
    st.warning("분석할 요일을 하나 이상 선택해주세요.")
    st.stop()

filtered = df[df["요일"].isin(selected_weekdays)].copy()

# 날짜 범위
min_date = filtered["날짜"].min().date()
max_date = filtered["날짜"].max().date()

date_range = st.sidebar.date_input(
    "분석 기간",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        (filtered["날짜"].dt.date >= start_date) &
        (filtered["날짜"].dt.date <= end_date)
    ]

# =========================================================
# 핵심 통계
# =========================================================
if len(filtered) == 0:
    st.warning("선택한 조건에 해당하는 급식 데이터가 없습니다.")
    st.stop()

weekday_avg = (
    filtered
    .groupby("요일")
    .agg(
        평균칼로리=("칼로리", "mean"),
        평균탄수화물=("탄수화물", "mean"),
        평균단백질=("단백질", "mean"),
        평균지방=("지방", "mean"),
        급식일수=("칼로리", "count")
    )
    .reindex(weekday_order)
)

weekday_avg = weekday_avg.dropna(how="all")

# =========================================================
# 주요 지표
# =========================================================
st.markdown("### 📊 핵심 분석")

c1, c2, c3, c4 = st.columns(4)

avg_kcal = filtered["칼로리"].mean()
max_kcal = filtered["칼로리"].max()
min_kcal = filtered["칼로리"].min()
kcal_std = filtered["칼로리"].std()

c1.metric(
    "전체 평균 칼로리",
    f"{avg_kcal:,.1f} kcal"
)

c2.metric(
    "최고 칼로리",
    f"{max_kcal:,.1f} kcal"
)

c3.metric(
    "최저 칼로리",
    f"{min_kcal:,.1f} kcal"
)

c4.metric(
    "칼로리 편차",
    f"{kcal_std:,.1f} kcal"
)

# =========================================================
# 요일별 평균 칼로리
# =========================================================
st.markdown("### 🔥 요일별 평균 칼로리")

kcal_chart = weekday_avg[["평균칼로리"]].copy()
kcal_chart.columns = ["평균 칼로리 (kcal)"]

st.bar_chart(kcal_chart)

# =========================================================
# 영양소 비교
# =========================================================
st.markdown("### 🥗 요일별 주요 영양소")

nutrition_chart = weekday_avg[
    ["평균탄수화물", "평균단백질", "평균지방"]
].copy()

nutrition_chart.columns = [
    "탄수화물 (g)",
    "단백질 (g)",
    "지방 (g)"
]

st.line_chart(nutrition_chart)

# =========================================================
# 영양 균형 분석
# =========================================================
st.markdown("### ⚖️ 칼로리 구성 분석")

st.write(
    "탄수화물·단백질·지방이 실제로 제공하는 에너지를 이용해 "
    "요일별 칼로리 구성을 비교합니다."
)

balance = weekday_avg.copy()

# 탄수화물 4 kcal/g
balance["탄수화물 kcal"] = balance["평균탄수화물"] * 4

# 단백질 4 kcal/g
balance["단백질 kcal"] = balance["평균단백질"] * 4

# 지방 9 kcal/g
balance["지방 kcal"] = balance["평균지방"] * 9

balance["탄수화물 비율"] = (
    balance["탄수화물 kcal"] /
    (balance["탄수화물 kcal"] +
     balance["단백질 kcal"] +
     balance["지방 kcal"]) * 100
)

balance["단백질 비율"] = (
    balance["단백질 kcal"] /
    (balance["탄수화물 kcal"] +
     balance["단백질 kcal"] +
     balance["지방 kcal"]) * 100
)

balance["지방 비율"] = (
    balance["지방 kcal"] /
    (balance["탄수화물 kcal"] +
     balance["단백질 kcal"] +
     balance["지방 kcal"]) * 100
)

ratio_chart = balance[
    ["탄수화물 비율", "단백질 비율", "지방 비율"]
].round(1)

st.bar_chart(ratio_chart)

# =========================================================
# 요일별 상세표
# =========================================================
st.markdown("### 📋 요일별 상세 데이터")

display_table = weekday_avg.copy()

display_table.columns = [
    "평균 칼로리",
    "평균 탄수화물(g)",
    "평균 단백질(g)",
    "평균 지방(g)",
    "급식일 수"
]

display_table = display_table.round(1)

st.dataframe(
    display_table,
    use_container_width=True
)

# =========================================================
# 새로운 인사이트 찾기
# =========================================================
st.markdown("### 💡 데이터에서 발견하는 새로운 인사이트")

highest_day = weekday_avg["평균칼로리"].idxmax()
lowest_day = weekday_avg["평균칼로리"].idxmin()

highest_value = weekday_avg.loc[highest_day, "평균칼로리"]
lowest_value = weekday_avg.loc[lowest_day, "평균칼로리"]

difference = highest_value - lowest_value

st.markdown(
    f"""
    <div class="insight-box">
    <h4>🔥 칼로리가 가장 높은 요일</h4>
    <p>
    <b>{highest_day}</b>의 평균 칼로리가
    <b>{highest_value:,.1f} kcal</b>로 가장 높았습니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="insight-box">
    <h4>📉 칼로리가 가장 낮은 요일</h4>
    <p>
    <b>{lowest_day}</b>의 평균 칼로리가
    <b>{lowest_value:,.1f} kcal</b>로 가장 낮았습니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="insight-box">
    <h4>🔎 요일 간 차이</h4>
    <p>
    가장 높은 요일과 가장 낮은 요일의 평균 칼로리 차이는
    <b>{difference:,.1f} kcal</b>입니다.
    </p>
    <p>
    따라서 급식의 영양 균형을 판단할 때
    단순히 평균 칼로리만 보는 것이 아니라
    탄수화물·단백질·지방의 구성까지 함께 살펴볼 필요가 있습니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 최고/최저 급식
# =========================================================
st.markdown("### 🍚 특별히 눈에 띄는 급식")

highest_meal = filtered.loc[filtered["칼로리"].idxmax()]
lowest_meal = filtered.loc[filtered["칼로리"].idxmin()]

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 가장 높은 칼로리")
    st.write(
        f"📅 {highest_meal['날짜'].strftime('%Y-%m-%d')} "
        f"({highest_meal['요일']})"
    )
    st.write(f"**{highest_meal['칼로리']:,.1f} kcal**")
    st.write(f"🍴 {highest_meal['요리명']}")

with col2:
    st.subheader("🌱 가장 낮은 칼로리")
    st.write(
        f"📅 {lowest_meal['날짜'].strftime('%Y-%m-%d')} "
        f"({lowest_meal['요일']})"
    )
    st.write(f"**{lowest_meal['칼로리']:,.1f} kcal**")
    st.write(f"🍴 {lowest_meal['요리명']}")

# =========================================================
# 원본 데이터
# =========================================================
with st.expander("📂 분석에 사용된 데이터 보기"):
    st.dataframe(
        filtered[
            [
                "날짜",
                "요일",
                "식사명",
                "칼로리",
                "탄수화물",
                "단백질",
                "지방",
                "요리명"
            ]
        ],
        use_container_width=True
    )

# =========================================================
# 결론
# =========================================================
st.markdown("### 🎯 탐구 결론")

st.info(
    "이 분석은 요일별 평균 칼로리의 차이를 확인하는 것에서 끝나지 않고, "
    "탄수화물·단백질·지방의 구성 비율을 함께 비교하여 "
    "특정 요일에 급식의 영양 구성이 치우치는지 확인할 수 있도록 설계되었습니다. "
    "이를 통해 '칼로리가 높으면 무조건 영양적으로 좋은 급식일까?'라는 "
    "새로운 질문까지 확장할 수 있습니다."
)
