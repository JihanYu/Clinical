import streamlit as st

st.set_page_config(page_title='Pre-OP Risk Calculator', layout='centered')
st.title('수술 전 위험도 계산기(RCRI/ARISCAT)')
st.markdown('---')

##### --- 1. 환자 기본 정보 --- #####
with st.expander('환자 기본 정보', expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input('환자 이름')
        surgery = st.text_input('수술명')
    with col2:
        dob = st.text_input('생년월일(YYYY-MM-DD)')
        surgery_emergent = st.selectbox('수술긴급성', ['Elective', 'Urgent', 'Emergent'])

##### --- 2. 병력 및 검사 소견 --- #####
st.header('임상소견 및 검사 결과')
col3, col4 = st.columns(2)
with col3:
    st.subheader('Sx & P/Hx')
    sx = st.text_area('주요증상', 'None', height=100)
    phx = st.text_area('과거력(P/Hx)', 'None', height=100)
with col4:
    st.subheader('검사소견')
    ecg = st.text_input('ECG', 'RSR')
    ech = st.text_area('Echocardiography', 'no RWMA, LVEF=60%', height=100)
    lab = st.text_area('Featured lab', height=100)

st.subheader('Phyxical Examination')
pe = st.text_area('Chest/Abdomen/Etc', 'Clear breathing sound without crackle, Regular heart beat without murmur, Abd NS', height=100)

st.markdown('---')

##### --- 3. RCRI (Revised cardiac risk index) --- #####
st.header('RCRI(Revised Cardiac Risk index) - 심장 위험')
rcri_items = {}
rcri_items['high_risk_surgery'] = st.checkbox('1. 고위험수술(Intraperitoneal, Intrathoracic, Suprainguinal vascular)')
rcri_items['ischemic_heart_disease'] = st.checkbox('2. 허혈성 심질환 병력(MI, 협심증, Q파 등)')
rcri_items['congestive_heart_failure'] = st.checkbox('3. 심부전 병력(pul edema, S3 gallop, PND 등)')
rcri_items['cerebrovascluar_disease'] = st.checkbox('4. 뇌혈관질환 병력(CVA/TIA)')
rcri_items['insulin_dependent_diabetes'] = st.checkbox('5. 인슐린 사용 당뇨')
rcri_items['renal_impairment'] = st.checkbox('6. 신기능저하(Cr > 2.0mg/dL)')

rcri_score = sum(rcri_items.values())
st.info(f'**RCRI 점수: {rcri_score}**')

# RCRI risk interpretation
rcri_risk_text = {
    0: '0.5%',
    1: '1.1%',
    2: '5.0%',
    3: '> 10.0%'
}
rcri_risk_level = '저위험' if rcri_score == 0 else ('중등도 위험' if rcri_score <= 2 else '고위험')

st.markdown(f"""
- *** 위험 분류 *** : {rcri_risk_level}
- *** major cardiac event (approx) *** : **{rcri_risk_text.get(rcri_score, '>10.0%')}**
""")

st.markdown('---')

##### --- 4. ARISCAT (폐 합병증 위험) --- #####
st.header('ARISCAT(폐 합병증 위험)')
ariscat_cols = st.columns(3)
with ariscat_cols[0]:
    age = st.number_input('나이(years)', min_value=12, max_value=120, value=65)
    preop_spO2 = st.number_input('기저 SpO2(%)', min_value=50, max_value=100, value=97)
with ariscat_cols[1]:
    recent_resp = st.checkbox('최근 30일 이내 호흡기 감염 증상')
    hemoglobin = st.number_input('Hb(g/dL)', min_value=5.0, max_value=20.0, value=12.0)
with ariscat_cols[2]:
    surgery_site = st.selectbox('수술부위', ['Etc(기타)', 'Upper abdomen(상복부)', 'Intrathoraci(흉강내)'])
    surgery_duration_hours = st.number_input('예상 수술 시간(hr)', min_value=0.5, max_value=12.0, value=1.0)

# ARISCAT scoring logic
ariscat_score = 0
# 1. Age
if 51 <= age <= 80 :    ariscat_score += 3
elif age > 80 :         ariscat_score += 16

# 2. PreOP SpO2
if 91 <= preop_spO2 <= 95:  ariscat_score += 8
elif preop_spO2 <= 90:      ariscat_score += 24

# 3. Receent resp infection
if recent_resp:             ariscat_score += 17

# 4. Hb < 10 g/dL
if hemoglobin < 10:     ariscat_score += 11

# 5. Surgery site
if surgery_site == 'Intrathorasic(흉강내)':     ariscat_score += 24
elif surgery_site == 'Upper abdomen(상복부)':   ariscat_score += 15

# 6. Duration
if 2 <= surgery_duration_hours < 3:     ariscat_score += 16
elif surgery_duration_hours >= 3 :      ariscat_score += 23

# 7. Emergency
emergency = (surgery_emergent != 'Elective')
if emergency:       ariscat_score += 8

st.info(f'*** ARISCAT score (approx): {ariscat_score} ***')

if ariscat_score < 26:
    ariscat_level = '저위험(Low risk)'
    ariscat_cx_risk = '1.6%'
elif ariscat_score < 45:
    ariscat_level = '중등도위험(Intermediate Risk)'
    ariscat_cx_risk = '13.3%'
else:
    ariscat_level = '고위험(High risk)'
    ariscat_cx_risk = '42.1%'

st.markdown(f"""
- *** 위험 분류 *** : {ariscat_level}
- *** 수술 후 폐 합병증(post OP Pul Cx) 위험 *** : **{ariscat_cx_risk}**
""")

st.markdown('---')

##### --- 5. ASA & METs(기능적 능력) --- #####
st.header('ASA 분류 및 기능적 상태')
# ASA classification
asa_class_options = {
    'ASA I' : '완전히 건강한 환자',
    'ASA II' : '경미한 전신 질환이 잇는 환자',
    'ASA III' : '중등도 이상의 전신 질환을 가진 환자',
    'ASA IV' : '지속적으로 생명을 위협하는 중증 전신 질환을 가진 환자',
    'ASA V' : '수술을 하지 않으면 생명을 유지하기 어려운 환자',
    'ASA VI' : '장기 공여를 위한 뇌사 상태의 환자'
}

asa_selected = st.radio(
    '**ASA (American Society of Anesthesiologists) classification',
    options=list(asa_class_options.keys()),
    index=1,
    format_func=lambda x: f'{x}: {asa_class_options[x]}'
)
asa_class = asa_selected.split(' ')[1]

# Simplified METs/Functional Capacity based on 4METs cut-off
st.subheader('기능적 상태(functional capacity)')
functional_capacity = st.selectbox(
    '4METs 이상 활동 가능 여부 (계단 2층 오르기 또는 평지 빠른 걷기)',
    options=['가능(4 METs 이상)', '불가능(4 METs 미만)', '평가 불가'],
    index=0
)

##### --- 6. 통합 권고 --- #####
st.header('통합 협진 회신 및 권고')
recommendations = []

# RCRI-based recommendation
if rcri_score >= 3:
    recommendations.append(f'**[심장]** 고위험 심혈관 상태 (주요심혈관위험 > 10.0%)')
    recommendations.append(f'  --권고 : 비침습적 또는 침습적 추가 심장 검사 고려')
elif rcri_score == 2:
    recommendations.append(f'**[심장]** 중등도 심혈관 상태 (주요심혈관위험 5.0%)')
    recommendations.append(f'  --권고 : 기능 상태(METs)가 4 미만이거나 수술 위험도가 높을 경우 비침습적 심장 검사 검토')
elif rcri_score == 1:
    recommendations.append(f'**[심장]** 중등도 심혈관 상태 (주요심혈관위험 1.1%)')
    recommendations.append(f'  --권고 : 비침습적 또는 침습적 추가 심장 검사 고려')
else:
    recommendations.append(f'**[심장]** 저위험 심혈관 상태 (주요심혈관위험 0.5%)')

# ARISCAT-based recommendation
if ariscat_score >= 45:
    recommendations.append(f'**[호흡기]** 고위험 폐합병증 위험 ({ariscat_cx_risk})')
    recommendations.append(f'  --권고: 수술 전 폐 재활, 금연 등 최적화, 수술 후 집중적인 폐 관리 및 감시 필요')
elif ariscat_score >= 26:
    recommendations.append(f'**[호흡기]** 중등도 폐합병증 위험 ({ariscat_cx_risk})')
    recommendations.append(f'  --권고: 수술 전후 호흡기 관리 및 위험 요인(예: 흡연) 교정 권고')
else:
    recommendations.append(f'**[호흡기]** 저위험 폐합병증 위험 ({ariscat_cx_risk})')
    recommendations.append(f'  --권고: 일반적인 수술 후 호흡기 관리 지침 준수')

# Functional status(METs) based recommendation
if functional_capacity == '불가능(4 METs 미만)':
    recommendations.append(f'**[기능]** 기능적 능력 4 METs 미만으로 추정')
    recommendations.append(f'  --권고: 심폐기능 저하 가능성 높아 추가적인 심장/폐기능 평가 고려')

# Additional comments input
st.subheader('추가 의견')
add_comm = st.text_area('추가적으로 기재할 사항', '전반적인 상태는 비교적 안정적이나 만성 질환에 대한 철저한 관리와 수술 후 감시가 필요합니다.', height=150)

##### --- 7. 보고서 생성 및 출력 --- #####
st.markdown ('---')
final_recommendation_text = '\n'.join([f'- {r}' for r in recommendations])
final_comments = f"""
수술 후 chest pain, palpitation, dyspnea, abd discomfort 등 증상 시 재의뢰 바랍니다.
의뢰하여 주셔서 감사합니다.

내과 유지한 배상
"""

report = f"""
### 1. 주요 소견 및 검사 결과 ###
Sx : {sx}
P/Hx : {phx}

ECG : {ecg}
Echocardiography : {ech}
Featured lab : {lab}

P/Ex : 
{pe}

### 2. 위험도 평가 요약 ###
- ASA Class: {asa_selected}
- 기능 상태(4 METs 기준) : {functional_capacity}
- RCRI score : {rcri_score}점 (major cardiac event risk : {rcri_risk_text.get(rcri_score, '>10.0%')} ({rcri_risk_level})
- ARISCAT Score : {ariscat_score} (폐합병증 위험: {ariscat_cx_risk} ({ariscat_level}) )

### **3. 통합 협진 권고** ###

{final_recommendation_text}

### **4. 추가 의견** ###

{add_comm}

{final_comments}
"""

if st.button('Generate Final Report Text'):
    st.text_area('최종 협진 보고서 (복사하여 사용하세요)', report, height=800)
