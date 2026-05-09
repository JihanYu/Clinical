import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
 
st.set_page_config(page_title="DM Range", layout="wide")
 
st.title("DM Range")
st.markdown("HbA1c와 FBS 수치를 입력하면 정상 / 당뇨 전단계 / 당뇨 범위를 시각화합니다.")
 
# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("HbA1c")
    hba1c_val = st.number_input("HbA1c value (%)", min_value=3.0, max_value=15.0,
                                 value=6.0, step=0.1)
    hba1c_range = st.slider("Range of HbA1c", min_value=4.0, max_value=10.0,
                             value=(5.0, 7.0), step=0.1)
 
    st.header("FBS")
    fbs_val = st.number_input("FBS value (mg/dL)", min_value=30, max_value=500,
                               value=110, step=1)
    fbs_range = st.slider("Range of FBS", min_value=50, max_value=300,
                           value=(70, 150), step=1)
 
# ── Helper ───────────────────────────────────────────────────────────────────
def make_bar_trace(lower, cut1, cut2, upper, patient_val, title, unit):
    """
    Creates a stacked horizontal bar chart showing normal / pre-DM / DM zones
    and a marker line for the patient's value.
 
    Zones:
      [lower, cut1)  → 정상  (normal)
      [cut1,  cut2)  → 전단계 (pre-DM)
      [cut2,  upper] → 당뇨   (DM)
    """
    segments = [
        ("정상",   lower,  cut1,  "rgba(198,232,191,0.85)"),   # soft green
        ("전단계", cut1,   cut2,  "rgba(255,213,128,0.85)"),   # warm amber
        ("당뇨",   cut2,   upper, "rgba(230,100,100,0.85)"),   # muted red
    ]
 
    traces = []
    for label, lo, hi, color in segments:
        traces.append(
            go.Bar(
                x=[hi - lo],
                y=[title],
                base=lo,
                orientation="h",
                name=label,
                marker_color=color,
                marker_line=dict(width=0),
                text=label,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=13, color="#333"),
                hovertemplate=f"<b>{label}</b><br>{lo:.1f} – {hi:.1f} {unit}<extra></extra>",
                showlegend=False,
            )
        )
 
    # Patient value marker (vertical line drawn as a scatter point)
    traces.append(
        go.Scatter(
            x=[patient_val],
            y=[title],
            mode="markers",
            marker=dict(
                symbol="line-ns",
                size=28,
                line=dict(width=4, color="#1a1a2e"),
                color="#1a1a2e",
            ),
            name="측정값",
            hovertemplate=f"<b>측정값</b>: {patient_val} {unit}<extra></extra>",
            showlegend=False,
        )
    )
    return traces
 
 
# ── Build figure ─────────────────────────────────────────────────────────────
hba1c_lo, hba1c_hi = hba1c_range
fbs_lo, fbs_hi = fbs_range
 
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=["HbA1c (%)", "FBS (mg/dL)"],
    vertical_spacing=0.25,
)
 
for trace in make_bar_trace(hba1c_lo, 5.6, 6.5, hba1c_hi,
                             hba1c_val, "HbA1c", "%"):
    fig.add_trace(trace, row=1, col=1)
 
for trace in make_bar_trace(fbs_lo, 100, 126, fbs_hi,
                             fbs_val, "FBS", "mg/dL"):
    fig.add_trace(trace, row=2, col=1)
 
fig.update_layout(
    barmode="stack",
    height=380,
    margin=dict(l=20, r=20, t=60, b=20),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="serif", size=13),
    xaxis=dict(range=[hba1c_lo, hba1c_hi], showgrid=True,
               gridcolor="rgba(180,180,180,0.3)"),
    xaxis2=dict(range=[fbs_lo, fbs_hi], showgrid=True,
                gridcolor="rgba(180,180,180,0.3)"),
    yaxis=dict(showticklabels=False),
    yaxis2=dict(showticklabels=False),
)
 
# Add reference-line annotations (cut-points)
for x_val, row_idx in [(5.6, 1), (6.5, 1), (100, 2), (126, 2)]:
    fig.add_vline(
        x=x_val, line_dash="dot", line_color="rgba(80,80,80,0.5)",
        line_width=1.5, row=row_idx, col=1,
    )
 
st.plotly_chart(fig, use_container_width=True)
 
# ── Result badges ─────────────────────────────────────────────────────────────
def classify_hba1c(v):
    if v < 5.6:   return "정상",    "🟢"
    elif v < 6.5: return "당뇨 전단계", "🟡"
    else:          return "당뇨",    "🔴"
 
def classify_fbs(v):
    if v < 100:   return "정상",    "🟢"
    elif v < 126: return "당뇨 전단계", "🟡"
    else:          return "당뇨",    "🔴"
 
hba1c_cls, hba1c_icon = classify_hba1c(hba1c_val)
fbs_cls,   fbs_icon   = classify_fbs(fbs_val)
 
col1, col2 = st.columns(2)
col1.metric(label=f"HbA1c {hba1c_icon}", value=f"{hba1c_val:.1f} %",
            delta=hba1c_cls, delta_color="off")
col2.metric(label=f"FBS {fbs_icon}", value=f"{fbs_val} mg/dL",
            delta=fbs_cls, delta_color="off")
 
st.caption("기준: HbA1c 정상 < 5.6 / 전단계 5.6–6.4 / 당뇨 ≥ 6.5  |  "
           "FBS 정상 < 100 / 전단계 100–125 / 당뇨 ≥ 126 ")
 