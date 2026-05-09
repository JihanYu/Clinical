# ============================================================
# Liver Health Predictor  v3
# 지방간 / 간섬유화 예측 계산기
# ============================================================
# 지표 목록:
#   섬유화(Fibrosis) : FIB-4, NFS, APRI, SAFE, FNI
#   지방간(Steatosis): FLI, BARD

import math
import numpy as np
import streamlit as st

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Liver Health Predictor",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# 커스텀 CSS  (카드 스타일 + 신호등 배지)
# ─────────────────────────────────────────
st.markdown("""
<style>
/* 전체 폰트 */
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

/* 카드 */
.score-card {
    background: #f8fafd;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.score-card .label {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.score-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.2;
}
.score-card .sub {
    font-size: 0.82rem;
    color: #475569;
    margin-top: 4px;
}

/* 위험도 배지 */
.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-top: 6px;
}
.badge-low    { background:#dcfce7; color:#166534; }
.badge-mid    { background:#fef9c3; color:#854d0e; }
.badge-high   { background:#fee2e2; color:#991b1b; }
.badge-info   { background:#dbeafe; color:#1e40af; }

/* 종합 요약 카드 */
.summary-card {
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
.summary-card.low  { background:#f0fdf4; border:1.5px solid #86efac; }
.summary-card.mid  { background:#fefce8; border:1.5px solid #fde047; }
.summary-card.high { background:#fff1f2; border:1.5px solid #fca5a5; }

/* 섹션 헤더 */
.section-header {
    font-size: 1.0rem;
    font-weight: 700;
    color: #334155;
    border-left: 4px solid #3b82f6;
    padding-left: 10px;
    margin: 8px 0 16px 0;
}

/* 구분선 */
hr.thin { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 사이드바 – 입력
# ─────────────────────────────────────────
st.sidebar.header("📋 검사 데이터 입력")

with st.sidebar:
    with st.expander("🧍 기본 정보", expanded=True):
        age      = st.number_input("연령 (세)", 1, 120, 60)
        diabetes = st.checkbox("당뇨 / 공복혈당장애 (HbA1c ≥ 6.5%)")
        dm_val   = 1 if diabetes else 0
        weight   = st.number_input("체중 (kg)",  1.0, 300.0, 80.0, step=0.1)
        height   = st.number_input("키 (cm)",    50.0, 250.0, 165.0, step=0.1)
        wc       = st.number_input("허리둘레 (cm)", 30.0, 200.0, 85.0, step=0.1)

    # BMI (0 나누기 방어)
    bmi = weight / (height / 100.0) ** 2 if height > 0 else 0.0

    with st.expander("🩸 혈액 검사 결과", expanded=True):
        ast     = st.number_input("AST (IU/L)",           0, 2000, 25)
        alt     = st.number_input("ALT (IU/L)",           0, 2000, 25)
        ast_uln = st.number_input("AST 정상 상한치 (ULN)", 1,  200, 40)
        ggt     = st.number_input("GGT / r-GTP (U/L)",   0, 5000, 30)
        tg      = st.number_input("중성지방 TG (mg/dL)",  0, 8000, 150)
        hdl     = st.number_input("HDL-콜레스테롤 (mg/dL)", 0, 300, 50)
        plt_val = st.number_input("혈소판 (×10³/μL)",     1, 2000, 200)
        alb     = st.number_input("알부민 (g/dL)",        0.0, 10.0, 4.0, step=0.1)
        hba1c   = st.number_input("HbA1c (%)",           0.0, 20.0, 5.5, step=0.1)

    st.caption(f"📐 자동 계산된 BMI: **{bmi:.1f}** kg/m²")


# ─────────────────────────────────────────
# 계산 함수들 (인자 명시 + 0 나누기 방어)
# ─────────────────────────────────────────
RISK_LOW  = "low"
RISK_MID  = "mid"
RISK_HIGH = "high"
RISK_INFO = "info"

def badge_html(text: str, level: str) -> str:
    return f'<span class="badge badge-{level}">{text}</span>'


def calc_fib4(age, ast, alt, plt_val):
    """FIB-4 index — Angulo et al."""
    if alt <= 0 or plt_val <= 0:
        return None, "입력값 오류 (ALT, PLT > 0 필요)", RISK_INFO
    score = (age * ast) / (plt_val * math.sqrt(alt))
    if age <= 35:
        status, level = "35세 이하 — 해석 주의", RISK_INFO
    elif age < 65:
        if score < 1.3:       status, level = "저위험 (F0-F2)", RISK_LOW
        elif score <= 2.67:   status, level = "중간 위험 — 추가 평가 권장", RISK_MID
        else:                 status, level = "고위험 (F3-F4)", RISK_HIGH
    else:
        if score < 2.0:       status, level = "저위험 (F0-F2)", RISK_LOW
        elif score <= 2.67:   status, level = "중간 위험 — 추가 평가 권장", RISK_MID
        else:                 status, level = "고위험 (F3-F4)", RISK_HIGH
    return score, status, level


def calc_nfs(age, bmi, dm_val, ast, alt, plt_val, alb):
    """NAFLD Fibrosis Score — Angulo et al. 2007"""
    if alt <= 0:
        return None, "입력값 오류 (ALT > 0 필요)", RISK_INFO
    score = (-1.675 + (0.037 * age) + (0.094 * bmi) +
             (1.13 * dm_val) + (0.99 * (ast / alt)) -
             (0.013 * plt_val) - (0.66 * alb))
    if score < -1.455:      status, level = "저위험 (F0-F2)", RISK_LOW
    elif score <= 0.675:    status, level = "중간 위험 — 추가 평가 권장", RISK_MID
    else:                   status, level = "고위험 (F3-F4)", RISK_HIGH
    return score, status, level


def calc_apri(ast, ast_uln, plt_val):
    """APRI — Wai et al. 2003"""
    if plt_val <= 0:
        return None, "입력값 오류 (PLT > 0 필요)", RISK_INFO
    score = ((ast / ast_uln) / plt_val) * 100
    if score < 0.5:         status, level = "저위험", RISK_LOW
    elif score <= 1.0:      status, level = "중간 위험 (F2 경계)", RISK_MID
    else:                   status, level = "F2 이상 의심", RISK_HIGH
    return score, status, level


def calc_safe(age, bmi, dm_val, ast, alt, plt_val):
    """
    SAFE score (Steatosis-Associated Fibrosis Estimator)
    Anstee et al. 2019, Gut — fibrosis sub-model
    ※ 원 논문 계수 기준 (총단백 항목은 steatosis sub-model 전용)
    """
    score = (-5.412 + (0.040 * age) + (0.048 * bmi) +
             (0.595 * dm_val) + (0.010 * ast) -
             (0.013 * alt) - (0.016 * plt_val))
    if score < -1.35:       status, level = "저위험 (F0-F1)", RISK_LOW
    elif score <= 0.45:     status, level = "중간 위험", RISK_MID
    else:                   status, level = "고위험 (F2 이상)", RISK_HIGH
    return score, status, level


def calc_fni(ast, hba1c, hdl):
    """Fibrotic NASH Index — Tönjes et al."""
    lp    = 1.139 + (0.041 * ast) + (0.446 * hba1c) - (1.25 * hdl)
    score = math.exp(lp) / (1 + math.exp(lp))
    if score < 0.10:        status, level = "Fibrotic NASH 가능성 낮음", RISK_LOW
    elif score >= 0.40:     status, level = "Fibrotic NASH 고위험", RISK_HIGH
    else:                   status, level = "관찰 요망", RISK_MID
    return score, status, level


def calc_fli(tg, bmi, ggt, wc):
    """Fatty Liver Index — Bedogni et al. 2006"""
    if tg <= 0 or ggt <= 0:
        return None, "입력값 오류 (TG, GGT > 0 필요)", RISK_INFO
    lp    = 0.953 * math.log(tg) + 0.139 * bmi + 0.718 * math.log(ggt) + 0.053 * wc - 15.745
    score = math.exp(lp) / (1 + math.exp(lp)) * 100
    if score < 30:          status, level = "지방간 가능성 낮음", RISK_LOW
    elif score < 60:        status, level = "지방간 가능성 중간", RISK_MID
    else:                   status, level = "지방간 가능성 높음", RISK_HIGH
    return score, status, level


def calc_bard(bmi, ast, alt, diabetes):
    """BARD score — Harrison et al. 2008"""
    if alt <= 0:
        return None, "입력값 오류 (ALT > 0 필요)", RISK_INFO
    score = (1 if bmi >= 28 else 0) + (2 if (ast / alt) >= 0.8 else 0) + (1 if diabetes else 0)
    if score >= 2:          status, level = "간섬유화 고위험 (F3-F4)", RISK_HIGH
    else:                   status, level = "저위험", RISK_LOW
    return score, status, level


# ─────────────────────────────────────────
# 모든 지표 계산
# ─────────────────────────────────────────
results = {
    "fib4" : calc_fib4(age, ast, alt, plt_val),
    "nfs"  : calc_nfs(age, bmi, dm_val, ast, alt, plt_val, alb),
    "apri" : calc_apri(ast, ast_uln, plt_val),
    "safe" : calc_safe(age, bmi, dm_val, ast, alt, plt_val),
    "fni"  : calc_fni(ast, hba1c, hdl),
    "fli"  : calc_fli(tg, bmi, ggt, wc),
    "bard" : calc_bard(bmi, ast, alt, diabetes),
}


# ─────────────────────────────────────────
# 종합 위험도 계산 (섬유화 지표 기반)
# ─────────────────────────────────────────
def overall_fibrosis_risk(results):
    """필수 지표(FIB-4, NFS) + 보조(APRI, BARD) 기반 종합 위험도"""
    levels = [results[k][2] for k in ("fib4", "nfs", "apri", "bard")
              if results[k][0] is not None]
    high_cnt = levels.count(RISK_HIGH)
    mid_cnt  = levels.count(RISK_MID)
    if high_cnt >= 2:
        return RISK_HIGH, "고위험", "다수 지표에서 고도 간섬유화 가능성이 확인됩니다. 간 전문의 진료 및 조직검사 고려가 필요합니다."
    elif high_cnt == 1 or mid_cnt >= 2:
        return RISK_MID, "중간 위험", "일부 지표에서 섬유화 신호가 있습니다. 추가 영상검사(FibroScan 등) 및 추적 관찰을 권장합니다."
    else:
        return RISK_LOW, "저위험", "현재 지표상 유의한 간섬유화 가능성은 낮습니다. 정기적인 검진을 권장합니다."


overall_level, overall_label, overall_msg = overall_fibrosis_risk(results)


# ─────────────────────────────────────────
# 헬퍼 — 카드 렌더링
# ─────────────────────────────────────────
def render_score_card(label: str, score, status: str, level: str,
                      fmt: str = ".2f", note: str = ""):
    value_str = f"{score:{fmt}}" if score is not None else "—"
    badge     = badge_html(status, level)
    note_html = f'<div class="sub">{note}</div>' if note else ""
    st.markdown(f"""
    <div class="score-card">
        <div class="label">{label}</div>
        <div class="value">{value_str}</div>
        {badge}
        {note_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# 메인 화면
# ─────────────────────────────────────────
st.title("🫀 Liver Health Predictor")
st.caption("혈액검사 및 신체 계측치 기반 지방간·간섬유화 예측 도구  |  결과는 임상적 참고 자료로만 활용하십시오.")

st.markdown("<hr class='thin'>", unsafe_allow_html=True)

# ── 1. 종합 요약 배너 ──────────────────────
st.markdown('<div class="section-header">📊 종합 위험도 요약 (섬유화)</div>', unsafe_allow_html=True)

icon_map  = {RISK_LOW: "🟢", RISK_MID: "🟡", RISK_HIGH: "🔴"}
color_map = {RISK_LOW: "low", RISK_MID: "mid", RISK_HIGH: "high"}

steatosis_level = results["fli"][2]
steatosis_label = {"low": "낮음", "mid": "중간", "high": "높음", "info": "확인 불가"}.get(steatosis_level, "—")

sum_col1, sum_col2 = st.columns([2, 1])
with sum_col1:
    st.markdown(f"""
    <div class="summary-card {color_map[overall_level]}">
        <div style="font-size:1.5rem; font-weight:800; color:#1e293b; margin-bottom:6px;">
            {icon_map[overall_level]}&nbsp; 간섬유화 종합: <span style="color:{'#166534' if overall_level==RISK_LOW else '#854d0e' if overall_level==RISK_MID else '#991b1b'}">{overall_label}</span>
        </div>
        <div style="font-size:0.9rem; color:#334155; line-height:1.6;">{overall_msg}</div>
    </div>
    """, unsafe_allow_html=True)

with sum_col2:
    fli_score = results["fli"][0]
    fli_icon  = icon_map.get(steatosis_level, "⚪")
    st.markdown(f"""
    <div class="summary-card {color_map.get(steatosis_level, 'low')}">
        <div style="font-size:1.1rem; font-weight:800; color:#1e293b; margin-bottom:6px;">
            {fli_icon}&nbsp; 지방간 가능성 (FLI)
        </div>
        <div style="font-size:1.4rem; font-weight:700;">{f"{fli_score:.0f}" if fli_score else "—"}</div>
        <div style="font-size:0.85rem; color:#334155; margin-top:4px;">{steatosis_label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='thin'>", unsafe_allow_html=True)

# ── 2. 섬유화 / 지방간 지표 상세 ─────────────
tab_fib, tab_fat = st.tabs(["🔬 섬유화(Fibrosis) 지표", "🫙 지방간(Steatosis) 지표"])

with tab_fib:
    st.caption("FIB-4, NFS는 필수 지표 / APRI는 보조 지표 / SAFE·FNI는 선택적 추가 지표입니다.")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**필수 지표**")
        render_score_card(
            "FIB-4 Index",
            *results["fib4"],
            note="(Age × AST) / (PLT × √ALT) — 가장 널리 사용되는 비침습 섬유화 지표"
        )
        render_score_card(
            "NFS (NAFLD Fibrosis Score)",
            *results["nfs"],
            note="Angulo et al. 2007 — F3 이상 진단에 NPV 93%"
        )

        st.markdown("**보조 지표**")
        render_score_card(
            "APRI",
            *results["apri"],
            fmt=".3f",
            note=">0.5: F2 이상 경계 / >1.0: 고도 섬유화 가능성"
        )

    with c2:
        st.markdown("**선택적 지표**")
        render_score_card(
            "SAFE Score (Fibrosis Sub-model)",
            *results["safe"],
            fmt=".2f",
            note="Anstee et al. 2019, Gut — fibrosis 예측 모델"
        )
        render_score_card(
            "FNI (Fibrotic NASH Index)",
            *results["fni"],
            fmt=".3f",
            note="<0.10: NASH 배제 / ≥0.40: Fibrotic NASH 고위험"
        )

        # 고위험 지표 요약 테이블
        high_list = [k.upper() for k in ("fib4","nfs","apri","safe","fni")
                     if results[k][0] is not None and results[k][2] == RISK_HIGH]
        mid_list  = [k.upper() for k in ("fib4","nfs","apri","safe","fni")
                     if results[k][0] is not None and results[k][2] == RISK_MID]
        if high_list or mid_list:
            st.markdown("---")
            if high_list:
                st.error(f"🔴 고위험 신호: **{', '.join(high_list)}**")
            if mid_list:
                st.warning(f"🟡 중간 위험 신호: **{', '.join(mid_list)}**")


with tab_fat:
    c3, c4 = st.columns(2)

    with c3:
        render_score_card(
            "FLI (Fatty Liver Index)",
            *results["fli"],
            fmt=".1f",
            note="Bedogni 2006 — <30: 지방간 배제 / ≥60: 지방간 가능성 높음"
        )

    with c4:
        bard_score, bard_status, bard_level = results["bard"]
        bard_val_str = f"{int(bard_score)}점" if bard_score is not None else "—"
        badge_bard   = badge_html(bard_status, bard_level)
        st.markdown(f"""
        <div class="score-card">
            <div class="label">BARD Score</div>
            <div class="value">{bard_val_str}</div>
            {badge_bard}
            <div class="sub">BMI≥28(1pt) + AST/ALT≥0.8(2pt) + DM(1pt) — Harrison 2008</div>
        </div>
        """, unsafe_allow_html=True)

    st.info("ℹ️ FLI는 지방간(steatosis) 유무 스크리닝 도구이며, 섬유화 중증도와는 별개로 해석합니다.")


st.markdown("<hr class='thin'>", unsafe_allow_html=True)

# ── 3. 공식 및 참고문헌 ───────────────────
with st.expander("📖 지표별 산출 공식 및 참고문헌"):
    st.markdown("""
    | 지표 | 공식 요약 | 주요 참고문헌 |
    |------|-----------|---------------|
    | **FIB-4** | (Age × AST) / (PLT × √ALT) | Sterling et al. *Hepatology* 2006 |
    | **NFS** | -1.675 + 0.037×Age + 0.094×BMI + 1.13×DM + 0.99×(AST/ALT) − 0.013×PLT − 0.66×Alb | Angulo et al. *Hepatology* 2007 |
    | **APRI** | (AST / AST_ULN) / PLT × 100 | Wai et al. *Gut* 2003 |
    | **SAFE** | 로지스틱 모델 (Age, BMI, DM, AST, ALT, PLT) | Anstee et al. *Gut* 2019 |
    | **FNI** | 로지스틱 모델 (AST, HbA1c, HDL) | Tönjes et al. *Diabetologia* 2012 |
    | **FLI** | 로지스틱 (TG, BMI, GGT, WC) × 100 | Bedogni et al. *BMC Gastroenterology* 2006 |
    | **BARD** | 점수 합산 (BMI, AST/ALT ratio, DM) | Harrison et al. *Hepatology* 2008 |
    
    """)
