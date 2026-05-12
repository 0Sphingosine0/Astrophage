import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone

st.set_page_config(
    page_title="Astrophage Detection System",
    page_icon="🔭",
    layout="wide",
)

st.markdown("""
<style>
  .mono { font-family: monospace; }
  .status-ok   { color: #0F6E56; font-weight: 500; }
  .status-warn { color: #854F0B; font-weight: 500; }
  .status-crit { color: #A32D2D; font-weight: 500; }
  .log-box {
    background: #f5f5f2;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: monospace;
    font-size: 12px;
    max-height: 180px;
    overflow-y: auto;
  }
  .banner-warn {
    background: #FAEEDA;
    border: 1px solid #EF9F27;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    color: #854F0B;
    font-size: 13px;
    margin-bottom: 0.5rem;
  }
  .banner-crit {
    background: #FCEBEB;
    border: 1px solid #F09595;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    color: #A32D2D;
    font-size: 13px;
    margin-bottom: 0.5rem;
  }
</style>
""", unsafe_allow_html=True)


def calc_risk(lum, ir, orb, alb):
    l = min(lum / 5, 1)
    i = min(ir / 100, 1)
    o = min(orb / 0.01, 1)
    a = min(alb / 1, 1)
    return min(l * 0.35 + i * 0.35 + o * 0.15 + a * 0.15, 1)


def draw_spectrum(ir_level):
    lam = np.linspace(8, 20, 400)
    base = 0.15 * np.exp(-((lam - 10.5) / 1.8) ** 2)
    peak = (ir_level / 100) * 0.85 * np.exp(-((lam - 14) / 0.6) ** 2)
    total = base + peak

    fill_color = "rgba(162,45,45,0.25)" if ir_level > 20 else "rgba(29,158,117,0.2)"
    line_color = "#A32D2D" if ir_level > 20 else "#0F6E56"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=lam, y=total,
        fill="tozeroy",
        fillcolor=fill_color,
        line=dict(color=line_color, width=2),
        name="Emission",
    ))

    if ir_level > 5:
        fig.add_vline(
            x=14,
            line=dict(color="#BA7517", width=1, dash="dash"),
            annotation_text="14μm",
            annotation_position="top right",
            annotation_font_size=11,
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=30),
        height=140,
        xaxis=dict(title="Wavelength (μm)", showgrid=False, color="#888"),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


if "log" not in st.session_state:
    t = datetime.now(timezone.utc).strftime("%H:%M:%S")
    st.session_state.log = [
        f"[{t}] INIT  — Heliospectrometer array online. Baseline calibrated.",
        f"[{t}] INIT  — 14μm band filter engaged. Petrovian ratio nominal.",
        f"[{t}] SCAN  — No anomalous IR emission detected. All systems nominal.",
    ]


def add_log(tag, msg):
    t = datetime.now(timezone.utc).strftime("%H:%M:%S")
    st.session_state.log.append(f"[{t}] {tag:<5} — {msg}")


utc_now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M:%S UTC")
st.markdown(
    f"<div class='mono' style='display:flex;align-items:center;gap:12px;border-bottom:1px solid #ddd;padding-bottom:0.5rem;margin-bottom:1rem;'>"
    f"<span style='width:10px;height:10px;border-radius:50%;background:#1D9E75;display:inline-block;'></span>"
    f"<span style='font-size:13px;letter-spacing:0.07em;color:#555;'>ASTROPHAGE DETECTION SYSTEM</span>"
    f"<span style='margin-left:auto;font-size:11px;color:#999;'>{utc_now}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

col_sliders, col_main = st.columns([1, 2], gap="large")

with col_sliders:
    st.markdown("**Sensor inputs**")
    lum = st.slider("Luminosity drop (%)", 0.0, 5.0, 0.0, 0.1)
    ir  = st.slider("IR anomaly at 14μm (W/m²)", 0, 100, 0, 1)
    orb = st.slider("Orbit deviation (AU)", 0.0, 0.01, 0.0, 0.0001, format="%.4f")
    alb = st.slider("Venus albedo shift", 0.0, 1.0, 0.0, 0.01)

    st.divider()
    run_scan = st.button("🔭 Run deep scan", use_container_width=True)
    if st.button("↺ Reset sensors", use_container_width=True):
        lum = ir = orb = alb = 0.0
        add_log("INIT", "Sensors reset. Baseline recalibrated.")

risk = calc_risk(lum, ir, orb, alb)
conf = round(risk * 100)
lum_pct = round(100 - lum, 1)
pvr = round(1 - lum * 0.018, 3)
risk_pct = round(risk * 100)

with col_main:
    if risk_pct > 65:
        st.markdown(
            f"<div class='banner-crit'>⚠ ALERT: Confidence {conf}% — 14μm emission spike detected. "
            f"Petrovian ratio degraded. Recommend cross-checking with Venus heliostat array.</div>",
            unsafe_allow_html=True,
        )
    elif risk_pct > 30:
        st.markdown(
            f"<div class='banner-warn'>⚠ WARNING: Marginal anomaly at {conf}% confidence. "
            f"Monitor for sustained luminosity trend.</div>",
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4 = st.columns(4)
    lum_cls = "status-crit" if lum > 2 else "status-warn" if lum > 0.5 else "status-ok"
    ir_cls  = "status-crit" if ir > 50 else "status-warn" if ir > 10 else ""
    pv_cls  = "status-crit" if pvr < 0.97 else "status-warn" if pvr < 0.99 else "status-ok"
    cf_cls  = "status-crit" if conf > 65 else "status-warn" if conf > 30 else ""

    with m1:
        st.metric("Solar luminosity", f"{lum_pct}%", delta=f"-{lum:.1f}%" if lum else None, delta_color="inverse")
    with m2:
        st.metric("IR emission (14μm)", f"{ir:.1f} W/m²")
    with m3:
        st.metric("Petrovian ratio", f"{pvr:.3f}")
    with m4:
        st.metric("Detection conf.", f"{conf}%")

    st.markdown("**Contamination risk index**")
    st.progress(risk_pct / 100)
    risk_color = "#A32D2D" if risk_pct > 65 else "#BA7517" if risk_pct > 30 else "#1D9E75"
    st.markdown(
        f"<span style='font-size:13px;font-family:monospace;color:{risk_color};font-weight:500;'>{risk_pct}%</span>",
        unsafe_allow_html=True,
    )

    st.markdown("**Infrared emission spectrum**")
    st.plotly_chart(draw_spectrum(ir), use_container_width=True, config={"displayModeBar": False})

    if run_scan:
        add_log("SCAN", "Initiating deep spectral scan across heliospectrometer array...")
        if conf > 65:
            add_log("ALERT", f"Astrophage signature confirmed at {conf}% confidence. 14μm band: {ir:.1f} W/m² above baseline.")
            add_log("ALERT", "Initiating emergency protocol. Recommend immediate Hail Mary mission briefing.")
        elif conf > 30:
            add_log("WARN", f"Marginal IR anomaly — {conf}% probability. Insufficient for confirmation. Continue monitoring.")
        else:
            add_log("SCAN", "No astrophage signature detected. Solar parameters within normal bounds.")

    st.markdown("**System log**")
    log_html = "<div class='log-box'>" + "<br>".join(st.session_state.log[-20:]) + "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
