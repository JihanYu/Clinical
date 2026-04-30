import streamlit as st

########################################
# 페이지 설정
########################################
st.set_page_config(
    page_title = "고지혈증 약물치료 판정도구",
    layout = "wide",
    initial_sidebar_state="collapsed"
)

########################################
# style
########################################
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
 
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
 
    .stApp { background: #f4f6f9; }
 
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }
 
    /* 섹션 카드 */
    .section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        border: 1px solid #e8ecf0;
    }
    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7a8494;
        margin-bottom: 0.9rem;
    }
 
    /* 위험군 배지 */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .badge-1  { background:#fff0f0; color:#c0392b; border:1px solid #f5c6c6; }
    .badge-2  { background:#fff4ed; color:#d35400; border:1px solid #f5d0b5; }
    .badge-3  { background:#fffbec; color:#b07d00; border:1px solid #f0e0a0; }
    .badge-4  { background:#f0f7ff; color:#1a6fb5; border:1px solid #b8d4ee; }
    .badge-5  { background:#f2f9f2; color:#27ae60; border:1px solid #b5ddb5; }
 
    /* 결과 박스 */
    .result-alert {
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-top: 0.5rem;
    }
    .result-alert.treat {
        background: #fff5f5;
        border: 1.5px solid #e74c3c;
    }
    .result-alert.ok {
        background: #f0faf2;
        border: 1.5px solid #27ae60;
    }
    .result-label { font-size: 1.0rem; font-weight: 700; margin-bottom: 0.4rem; }
    .result-label.treat { color: #c0392b; }
    .result-label.ok    { color: #1e8449; }
    .result-detail { font-size: 0.88rem; color: #555; line-height: 1.7; }
 
    /* 수치 하이라이트 */
    .metric-row { display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.6rem; }
    .metric-box {
        background:#fff;
        border:1px solid #dde3ea;
        border-radius:8px;
        padding:0.5rem 0.9rem;
        text-align:center;
        min-width:90px;
    }
    .metric-box .val { font-size:1.2rem; font-weight:700; color:#1a2a3a; }
    .metric-box .lbl { font-size:0.72rem; color:#8a94a2; margin-top:2px; }
    .metric-box.over .val { color:#e74c3c; }
    .metric-box.target-line { font-size:0.78rem; color:#7a8494; margin-top:0.4rem; }
</style>
""", unsafe_allow_html=True)
 
########################################
#데이터 테이블 (category 별 LDL/non-HDL 기준)
########################################
CATEGORY_INFO = {
    1: {"label": "초고위험군",  "LDL": 55, "non_HDL": 85, "badge":"badge-1"},
    2: {"label": "고위험군",    "LDL": 70, "non_HDL": 100, "badge":"badge-2"},
    3: {"label": "고-중등도위험군", "LDL": 100, "non_HDL": 130, "badge":"badge-3"},
    4: {"label": "중등도위험군",    "LDL": 130, "non_HDL": 160, "badge":"badge-4"},
    5: {"label": "저위험군",    "LDL": 160, "non_HDL": 190, "badge":"badge-5"},
}

########################################
# 위험도 계산 함수
########################################
def compute_risk(inputs: dict) -> dict:
    """
    입력값 딕셔너리를 받아 위험군 category, 위험인자 목록, DM 위험도를 반환
    """
    age, sex        = inputs['age'], inputs['sex']
    HTN, SBP, DBP   = inputs['HTN'], inputs['SBP'], inputs['DBP']
    HDL             = inputs['HDL']
    FHx_CAD         = inputs['FHx_CAD']
    smoking         = inputs['smoking']
    ACS             = inputs['ACS']
    CVA             = inputs['CVA']
    CarotidDis      = inputs['CarotidDis']
    PAD             = inputs['PAD']
    AAA             = inputs['AAA']
    DMover10        = inputs['DMover10']
    DMunder10       = inputs['DMunder10']

    findings = []

    # 심뇌혈관 위험인자
    no_risk = 0

    if (sex == "Male" and age >= 45) or (sex == 'Female' and age >= 55):
        no_risk += 1
        findings.append(f"고령 ({sex}, {age} 세)")
    if HTN or SBP >= 140 or DBP >= 90:
        no_risk += 1
        findings.append("HTN" if HTN else f"고혈압 ({SBP}/{DBP} mmHg)")
    if smoking:
        no_risk += 1
        findings.append("흡연")
    if HDL < 40:
        no_risk += 1
        findings.append(f"낮은 HDL ({HDL} mg/dL)")
    if FHx_CAD:
        no_risk += 1
        findings.append("조기 심혈관질환 가족력")
    if HDL >= 60:
        no_risk -= 1

    # 당뇨 위험도
    # 0: DM 없음 / 1 : 저위험 DM / 2: 고위험 DM
    if DMover10 or (DMunder10 and no_risk >= 1):
        DM_risk = 2
        findings.append("당뇨(> 10 yrs)" if DMover10 else "당뇨(위험인자동반)")
    elif DMunder10:
        DM_risk = 1
        findings.append("당뇨(< 10 yrs)")
    else:
        DM_risk = 0
    
    # category 결정(우선순위 순)
    if ACS:
        findings.append("ACS")
        category = 1
    elif CVA or CarotidDis or PAD or AAA or DM_risk==2:
        for flag, name in [ (CVA, "CVA/TIA"), (CarotidDis, "경동맥질환"),
                            (PAD, "말초동맥질환"), (AAA, "복부대동맥류") ]:
            if flag:
                findings.append(name)
        category = 2
    elif DM_risk == 1:
        category = 3
    elif no_risk >= 2:
        category = 4
    else:
        category = 5
    
    return{"category" : category, "findings": findings, "no_risk": no_risk}

########################################
# intensity 관련 함수 
########################################
def recommend_statin_intensity(category, LDL, target_LDL):
    """
    statin intensity 추천
    """
    if category == 1:
        return "High-intensity statin(예: atorvastatin 40-80mg, rosuvastatin 20-40mg)"
    elif category == 2:
        if LDL > target_LDL + 50:
            return "High-intensity statin 권장"
        else:
            return "Moderate to High-intensity statin 고려"
    elif category == 3:
        return "Moderate-intensity statin 권장"
    elif category == 4:
        if LDL >= target_LDL:
            return "Moderate-intensity statin 고려"
        else:
            return "생활습관 교정 우선"
    else:
        return "생활습관 교정(약물은 선택적)"


########################################
# 헤더
########################################
st.markdown("## 고지혈증 약물치료 판정도구")
st.markdown("<p style='color:#8a94a2;font-size=0.9rem;margin-top:-0.5rem;'>2024 한국지질동맥경화학회 가이드라인 기반</p>", unsafe_allow_html=True)
st.markdown("-----")

########################################
# 입력 레이아웃 (3열)
########################################
col_left, col_mid, col_right = st.columns([1, 1, 1], gap="medium")

# 열 1 : 기본 정보
with col_left:
    st.markdown('<div class = "section-card">'
                '<div class = "section-title">기본 정보</div>', unsafe_allow_html=True)
    age = st.number_input("연령(세)", min_value=0, max_value=120, value=60)
    sex = st.radio("성별", ["Male", "Female"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class = "section-card">'
                '<div class = "section-title">혈압</div>', unsafe_allow_html=True)
    SBP = st.number_input("수축기 혈압(SBP)", min_value=0, value=130)
    DBP = st.number_input("이완기 혈압(DBP)", min_value=0, value=80)
    st.markdown("</div>", unsafe_allow_html=True)

# 열 2 : 동반질환
with col_mid:
    st.markdown('<div class="section-card">'
                '<div class="section-title">심혈관 질환 / 고위험 상태<div>', unsafe_allow_html=True)
    ACS     = st.checkbox("급성 관상동맥 증후군 (ACS)")
    CVA     = st.checkbox("허혈성 뇌졸증/TIA")
    CarotidDis = st.checkbox("경동맥질환")
    PAD     = st.checkbox("말초동맥질환")
    AAA     = st.checkbox("복부대동맥류")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">'
                '<div class="section-title">위험인자<div>', unsafe_allow_html=True)
    HTN     = st.checkbox("고혈압(진단 또는 치료 중)")
    FHx_CAD = st.checkbox("조기 심혈관질환 가족력(M<55, F<65)")
    smoking = st.checkbox("흡연")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">'
                '<div class="section-title">당뇨병<div>', unsafe_allow_html=True)
    DMover10 = st.checkbox("당뇨 >= 10년")
    DMunder10 = st.checkbox("당뇨 < 10년")
    if DMover10 and DMunder10:
        st.warning("당뇨 항목은 하나만 선택하세요")
    st.markdown("</div>", unsafe_allow_html=True)

# 열 3 지질 수치
with col_right:
    st.markdown('<div class="section-card">'
                '<div class="section-title">지질 검사 결과(mg/dL)<div>', unsafe_allow_html=True)
    TC = st.number_input("Total cholesterol", min_value=0, value=200)
    HDL = st.number_input("HDL-cholesterol", min_value=0, value=50)
    TG = st.number_input("Triglyceride", min_value=0, value=150)
    LDL = st.number_input("LDL-cholesterol", min_value=0, value=130)
    non_HDL = TC - HDL
    st.markdown(
        f"<div style='background:#f4f6f9;border-radius:8px;padding:0.6rem 0.9rem;"
        f"margin-top:0.5rem;font-size:0.9rem;'>"
        f"<b>non-HDL Cholesterol</b>: {non_HDL} mg/dL</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


########################################
# 계산 실행
########################################
inputs = dict(
    age = age, sex = sex, HTN = HTN, SBP = SBP, DBP = DBP, HDL = HDL,
    FHx_CAD = FHx_CAD, smoking = smoking,
    ACS = ACS, CVA = CVA, CarotidDis = CarotidDis, PAD = PAD, AAA = AAA,
    DMover10 = DMover10, DMunder10 = DMunder10
)

result = compute_risk(inputs)
category = result["category"]
findings = result["findings"]
info = CATEGORY_INFO[category]

needs_treatment = (LDL >= info["LDL"]) or (non_HDL >= info["non_HDL"])


########################################
# 결과 출력
########################################
st.markdown("-----")
st.markdown("### 판정 결과")

res_col1, res_col2 = st.columns([1, 2], gap = "large")

with res_col1:
    st.markdown(
        f'<span class="badge {info["badge"]}">{info["label"]}</span>', unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='font-size:0.85rem;color:#555;line-height:1.8;'>"
        f"<b>치료 목표</b><br>"
        f"LDL-C &lt; {info['LDL']} mg/dL<br>"
        f"non-HDL &lt; {info['non_HDL']} mg/dL"
        f"</div>",
        unsafe_allow_html=True
    )

    if findings:
        st.markdown(
            "<div style='margin-top:0.8rem;font-size:0.82rem;color:#7a8494;'>"
            "<b>확인된 위험인자</b></div>",
            unsafe_allow_html=True
        )
        for f in findings:
            st.markdown(f"<span style='font-size:0.83rem;color:#444;'> {f} </span>",
                        unsafe_allow_html=True)

with res_col2:
    LDL_over    = LDL >= info["LDL"]
    non_HDL_over = non_HDL >= info["non_HDL"]

    if needs_treatment:
        st.markdown(
            f'<div class="result-alert treat">'
            f'<div class="result-label treat">**약물치료 고려 대상</div>'
            f'<div class="result-detail">'
            f'현재 수치가 {info["label"]} 치료 목표치를 초과합니다.'
            f'</div></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="result-alert ok">'
            f'<div class="result-label ok">**목표치 이내 / 생활습관 교정 대상</div>'
            f'<div class="result-detail">'
            f'현재 수치가 {info["label"]} 치료 목표치 이내입니다.'
            f'</div></div>',
            unsafe_allow_html=True
        ) 

    intensity = recommend_statin_intensity(category, LDL, info["LDL"])

    st.markdown(
        f"<div style='margin-top:0.8rem;font-size:0.9rem;'>"
        f"<b>권장 치료</b><br>{intensity}</div>",
        unsafe_allow_html=True
    )

    # 수치 카드
    st.markdown(
        f"""<div class="metric-row">
          <div class="metric-box {'over' if LDL_over else ''}">
            <div class="val">{LDL}</div>
            <div class="lbl">LDL-C</div>
          </div>
          <div class="metric-box {'over' if non_HDL_over else ''}">
            <div class="val">{non_HDL}</div>
            <div class="lbl">non-HDL</div>
          </div>
          <div class="metric-box">
            <div class="val">{HDL}</div>
            <div class="lbl">HDL-C</div>
          </div>
          <div class="metric-box">
            <div class="val">{TG}</div>
            <div class="lbl">TG</div>
          </div>
        </div>""",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='target-line' style='font-size:0.78rem;color:#9a9ea5;margin-top:0.3rem;'>"
        f"목표: LDL &lt; {info['LDL']} &nbsp;|&nbsp; non-HDL &lt; {info['non_HDL']}"
        f"</div>",
        unsafe_allow_html=True
    )
 
########################################
# TG 경고
########################################
TG_threshold = 200 if result["no_risk"] > 0 else 500
if TG >= TG_threshold:
    st.warning(f"중성지방(TG) 관리 필요: 현재 {TG} mg/dL (기준 {TG_threshold} mg/dL 이상)")