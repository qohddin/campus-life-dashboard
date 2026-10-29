import streamlit as st
import pandas as pd
import re
from collections import Counter

# --- 웹페이지 기본 설정 ---
st.set_page_config(page_title="캠퍼스 라이프 분석", layout="wide")
st.title("📊 캠퍼스 라이프 데이터 분석 대시보드")

# --- 1. 파일 업로드 및 데이터 미리보기 ---
st.sidebar.header("📁 데이터 업로드")
# 사이드바에 CSV 파일을 업로드할 수 있는 버튼을 만듭니다.
uploaded_file = st.sidebar.file_uploader("campus_life.csv 파일을 업로드해주세요", type=['csv'])

# 파일이 업로드된 경우에만 아래 코드들이 실행됩니다.
if uploaded_file is not None:
    # 업로드된 파일을 판다스(pandas) 데이터프레임으로 읽어옵니다.
    df = pd.read_csv(uploaded_file)

    st.subheader("👀 원본 데이터 미리보기")
    # 원본 데이터의 첫 5줄을 화면에 표 형태로 보여줍니다.
    st.dataframe(df.head())

    # --- 2. 잘못된 데이터 처리 및 제외 건수 표시 ---
    # 전처리 전 원본 데이터의 총 개수를 저장합니다.
    original_count = len(df)

    # [전처리 1] '만족도' 열에서 '모름' 데이터를 제외합니다.
    df_clean = df[df['만족도'] != '모름'].copy()

    # [전처리 2] 빈칸(결측치)이 있는 데이터 줄을 삭제합니다.
    df_clean = df_clean.dropna()

    # [전처리 3] '만족도' 글자를 계산 가능한 진짜 숫자(정수)로 바꿉니다.
    df_clean['만족도'] = df_clean['만족도'].astype(int)

    # 전처리가 끝난 후 살아남은 데이터의 개수입니다.
    cleaned_count = len(df_clean)

    # 제외된 데이터 건수를 화면에 안내합니다.
    excluded_count = original_count - cleaned_count
    st.info(f"🧹 데이터 정제 완료: '모름' 응답 및 결측치 등 총 {excluded_count}건의 데이터를 제외했습니다.")

    st.divider()

    # --- 3. 학과 필터 및 평균 만족도 연동 ---
    st.sidebar.header("🔍 분석 조건 선택")
    major_list = df_clean['학과'].unique()

    # 학과를 선택할 수 있는 드롭다운을 만들고, 선택된 학과를 저장합니다.
    selected_major = st.sidebar.selectbox("결과를 확인할 학과를 선택하세요:", major_list)

    # 선택된 학과의 데이터만 추려냅니다. (이후 모든 그래프는 이 데이터를 씁니다)
    major_df = df_clean[df_clean['학과'] == selected_major]

    avg_satisfaction = major_df['만족도'].mean()

    st.subheader(f"🎓 {selected_major} 분석 결과")
    st.metric(label=f"{selected_major} 평균 학교생활 만족도", value=f"{avg_satisfaction:.2f} 점")

    # --- 4. 학과별 생활 습관 차이 (막대 그래프) ---
    st.write("#### 📊 생활 습관 비교 (전체 학생 vs 선택 학과)")
    mean_all = df_clean[['통학시간', '공부시간', '스마트폰', '수면시간']].mean()
    mean_major = major_df[['통학시간', '공부시간', '스마트폰', '수면시간']].mean()

    compare_df = pd.DataFrame({
        '전체 평균': mean_all,
        f'{selected_major} 평균': mean_major
    })
    st.bar_chart(compare_df)

    # --- 5. 생활 습관과 만족도의 관계 (산점도) ---
    st.write(f"#### 📈 {selected_major} 학생들의 생활 습관과 만족도의 관계")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("📖 공부시간 vs 만족도")
        st.scatter_chart(major_df, x='공부시간', y='만족도')
    with col2:
        st.write("💤 수면시간 vs 만족도")
        st.scatter_chart(major_df, x='수면시간', y='만족도')
    with col3:
        st.write("📱 스마트폰 vs 만족도")
        st.scatter_chart(major_df, x='스마트폰', y='만족도')

    # --- 6. 한 줄 의견 키워드 분석 및 긍정/부정 표시 ---
    st.write(f"#### 💬 {selected_major} 한 줄 의견 분석")

    # 선택한 학과 학생들이 쓴 모든 한 줄 의견을 띄어쓰기로 연결해 하나의 긴 글로 만듭니다.
    all_text = " ".join(major_df['한줄의견'].tolist())

    # [추가 기능 1] 긍정 단어와 부정 단어 리스트를 미리 만들어 둡니다.
    positive_words = ['좋아요', '재미있어요', '맛있어요', '도움이']
    negative_words = ['부족해요', '피곤해요', '불편해요', '어려워요']

    # 등장 횟수를 저장할 변수를 0으로 시작합니다.
    pos_count = 0
    neg_count = 0

    # 전체 텍스트에서 긍정 단어가 몇 번 쓰였는지 반복문으로 셉니다.
    for word in positive_words:
        pos_count += all_text.count(word)

    # 전체 텍스트에서 부정 단어가 몇 번 쓰였는지 반복문으로 셉니다.
    for word in negative_words:
        neg_count += all_text.count(word)

    # 계산된 긍정/부정 횟수를 나란히 보여줍니다.
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric(label="😊 긍정 단어 등장 횟수", value=f"{pos_count} 회")
    with metric_col2:
        st.metric(label="😥 부정 단어 등장 횟수", value=f"{neg_count} 회")

    # [추가 기능 2] 가장 많이 등장한 단어 상위 10개 막대그래프
    # re 모듈로 한글 단어들만 추출합니다.
    words = re.findall(r'[가-힣]+', all_text)

    # 2글자 이상인 단어만 걸러냅니다. (1글자는 의미가 없는 경우가 많음)
    words_filtered = [word for word in words if len(word) >= 2]

    # 추출된 단어들의 개수를 셉니다.
    word_counts = Counter(words_filtered)

    if word_counts:
        # 가장 많이 등장한 10개 단어를 뽑아 표로 만듭니다.
        top_10_words = pd.DataFrame(word_counts.most_common(10), columns=['단어', '등장 횟수']).set_index('단어')

        st.write("##### 📌 가장 많이 등장한 단어 상위 10개")
        # 막대그래프를 그립니다.
        st.bar_chart(top_10_words)
    else:
        st.info("분석할 수 있는 2글자 이상의 한글 단어가 없습니다.")

else:
    st.info("👈 왼쪽 사이드바에서 'campus_life.csv' 파일을 업로드해주세요.")