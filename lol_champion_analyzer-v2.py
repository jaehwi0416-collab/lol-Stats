import pandas as pd
import streamlit as st
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="롤(LoL) 챔피언 스탯 분석 대시보드",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 롤(LoL) 챔피언 스탯 데이터 분석 대시보드")
st.markdown("CSV 또는 Excel 파일을 업로드하면 **데이터 표, 기초 통계, 상위/하위 랭킹 및 다양한 차트**로 자동 분석합니다.")

# 2. 사이드바: 파일 업로드
st.sidebar.header("📁 데이터 파일 업로드")
uploaded_file = st.sidebar.file_uploader(
    "분석할 파일을 업로드하세요 (.csv, .xlsx, .xls)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is None:
    st.info("👈 왼쪽 사이드바에서 분석할 파일(`.csv`, `.xlsx`, `.xls`)을 업로드해주세요.")
    st.stop()

# 3. 데이터 로드 함수
@st.cache_data
def load_data(file) -> pd.DataFrame:
    if file.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, encoding="cp949")
    else:
        return pd.read_excel(file)

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    st.stop()

# 4. 사이드바 필터링 (LoL 데이터 컬럼이 있을 경우 자동 활성화)
st.sidebar.header("🔍 데이터 필터")
filtered_df = df.copy()

if "Range type" in filtered_df.columns:
    range_options = filtered_df["Range type"].dropna().unique().tolist()
    selected_ranges = st.sidebar.multiselect("사거리 유형 (Range type)", range_options, default=range_options)
    if selected_ranges:
        filtered_df = filtered_df[filtered_df["Range type"].isin(selected_ranges)]

if "Role" in filtered_df.columns:
    unique_roles = sorted(list({r.strip() for roles in filtered_df["Role"].dropna() for r in str(roles).split(",")}))
    selected_roles = st.sidebar.multiselect("주 포지션 (Role)", unique_roles, default=unique_roles)
    if selected_roles:
        pattern = "|".join(selected_roles)
        filtered_df = filtered_df[filtered_df["Role"].astype(str).str.contains(pattern, na=False)]

if "Resource type" in filtered_df.columns:
    res_options = filtered_df["Resource type"].fillna("없음(None)").unique().tolist()
    selected_res = st.sidebar.multiselect("자원 유형 (Resource type)", res_options, default=res_options)
    if selected_res:
        filtered_df = filtered_df[filtered_df["Resource type"].fillna("없음(None)").isin(selected_res)]

st.success(f"✅ **{uploaded_file.name}** 업로드 완료! (총 {filtered_df.shape[0]:,}행 × {filtered_df.shape[1]:,}열)")

# 5. 핵심 요약 지표 (KPI)
numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()
if len(numeric_cols) > 0:
    kpi_cols = st.columns(4)
    kpi_cols[0].metric("총 데이터 수 (챔피언 수)", f"{len(filtered_df):,}개")
    if "Base HP" in filtered_df.columns:
        kpi_cols[1].metric("평균 기본 체력 (Base HP)", f"{filtered_df['Base HP'].mean():.1f}")
    if "Base attack damage" in filtered_df.columns:
        kpi_cols[2].metric("평균 기본 공격력", f"{filtered_df['Base attack damage'].mean():.1f}")
    elif "Base armor" in filtered_df.columns:
        kpi_cols[2].metric("평균 기본 방어력", f"{filtered_df['Base armor'].mean():.1f}")
    if "Movement speed" in filtered_df.columns:
        kpi_cols[3].metric("평균 이동 속도", f"{filtered_df['Movement speed'].mean():.1f}")

# 6. 데이터 표 미리보기 및 기초 통계 분석
st.header("1. 데이터 표 및 기초 통계 분석")
tab1, tab2, tab3, tab4 = st.tabs(["📋 데이터 표", "📈 기초 통계량", "🏆 스탯 상위/하위 랭킹", "🔍 결측치 및 컬럼 정보"])

with tab1:
    search_query = st.text_input("이름(Name) 또는 키워드 검색:", "")
    display_df = filtered_df
    if search_query and "Name" in display_df.columns:
        display_df = display_df[display_df["Name"].astype(str).str.contains(search_query, case=False, na=False)]
    st.dataframe(display_df, use_container_width=True, height=400)

with tab2:
    st.subheader("수치형 스탯 기초 통계량")
    if numeric_cols:
        st.dataframe(filtered_df[numeric_cols].describe().T.round(2), use_container_width=True)
    else:
        st.info("수치형 컬럼이 없습니다.")

with tab3:
    if numeric_cols and "Name" in filtered_df.columns:
        target_stat = st.selectbox("랭킹을 확인할 스탯 선택:", numeric_cols, index=0)
        top_n = st.slider("표시할 순위 수 (Top N)", 5, 30, 10)
        col_top, col_bot = st.columns(2)
        with col_top:
            st.subheader(f"🔼 {target_stat} 상위 {top_n}")
            st.dataframe(filtered_df[["Name", target_stat]].sort_values(by=target_stat, ascending=False).head(top_n), use_container_width=True)
        with col_bot:
            st.subheader(f"🔽 {target_stat} 하위 {top_n}")
            st.dataframe(filtered_df[["Name", target_stat]].sort_values(by=target_stat, ascending=True).head(top_n), use_container_width=True)
    else:
        st.info("Name 컬럼 또는 수치형 컬럼이 필요합니다.")

with tab4:
    info_df = pd.DataFrame({
        "컬럼명": filtered_df.columns,
        "데이터 타입": filtered_df.dtypes.astype(str).values,
        "결측치 수": filtered_df.isnull().sum().values,
        "결측치 비율(%)": (filtered_df.isnull().sum().values / max(len(filtered_df), 1) * 100).round(2),
        "고유값 수": filtered_df.nunique().values
    })
    st.dataframe(info_df, use_container_width=True)

# 7. 데이터 시각화 (차트 분석)
st.header("2. 데이터 시각화 (차트 분석)")

all_cols = filtered_df.columns.tolist()
default_x = all_cols.index("Range type") if "Range type" in all_cols else 0
default_y = numeric_cols.index("Base HP") if "Base HP" in numeric_cols else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    chart_type = st.selectbox(
        "차트 유형",
        ["박스 플롯 (분포 비교)", "막대 차트 (평균/합계)", "산점도 (상관관계)", "히스토그램 (분포)", "파이 차트 (비율)"]
    )
with c2:
    x_col = st.selectbox("X축 (기준 컬럼)", all_cols, index=default_x)
with c3:
    y_col = st.selectbox("Y축 (수치 컬럼)", numeric_cols if numeric_cols else all_cols, index=default_y)
with c4:
    color_options = ["없음"] + [c for c in ["Range type", "Resource type", "Role", "Tags"] if c in all_cols] + all_cols
    color_options = list(dict.fromkeys(color_options))
    color_col = st.selectbox("색상 구분", color_options, index=1 if len(color_options) > 1 else 0)

color_arg = None if color_col == "없음" else color_col
hover_arg = ["Name"] if "Name" in all_cols else None

try:
    if chart_type == "박스 플롯 (분포 비교)":
        fig = px.box(filtered_df, x=x_col, y=y_col, color=color_arg, points="all", hover_data=hover_arg,
                     title=f"{x_col}별 {y_col} 분포 비교")
    elif chart_type == "막대 차트 (평균/합계)":
        agg_df = filtered_df.groupby(x_col, as_index=False)[y_col].mean(numeric_only=True)
        fig = px.bar(agg_df, x=x_col, y=y_col, color=x_col, title=f"{x_col}별 평균 {y_col}")
    elif chart_type == "산점도 (상관관계)":
        fig = px.scatter(filtered_df, x=x_col, y=y_col, color=color_arg, hover_data=hover_arg,
                         title=f"{x_col} vs {y_col} 상관관계 산점도")
    elif chart_type == "히스토그램 (분포)":
        fig = px.histogram(filtered_df, x=y_col, color=color_arg, barmode="overlay",
                           title=f"{y_col} 전체 분포 히스토그램")
    elif chart_type == "파이 차트 (비율)":
        fig = px.pie(filtered_df, names=x_col, title=f"{x_col} 구성 비율")

    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"선택한 컬럼 조합으로 차트를 그릴 수 없습니다: {e}")

# 8. 다중 스탯 상관관계 히트맵
if len(numeric_cols) >= 2:
    st.subheader("3. 챔피언 능력치 간 상관관계 히트맵")
    selected_corr_cols = st.multiselect(
        "상관관계를 볼 스탯 선택 (기본 상위 10개):",
        numeric_cols,
        default=numeric_cols[:10]
    )
    if len(selected_corr_cols) >= 2:
        corr_matrix = filtered_df[selected_corr_cols].corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            aspect="auto",
            title="능력치 상관계수 히트맵"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
