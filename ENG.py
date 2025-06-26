# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 22:50:12 2025
@author: DellG15
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import pandas as pd
import base64

# Page config
st.set_page_config(page_title="Beam Designer Pro", layout="centered")

# 🌙 Dark mode
dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=False)
if dark_mode:
    st.markdown(
        """
        <style>
            body { background-color: #0E1117; color: white; }
            .stButton>button { background-color: #1E90FF; color: white; border-radius: 10px; font-weight: bold; }
            .stMetric label, .stMetric div { font-size: 18px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# 🌍 Language Support
language = st.sidebar.selectbox("Language / Sprache / Langue", ["English", "Deutsch", "Français", "Italiano"])

def tr(en, de, fr, it):
    return {"English": en, "Deutsch": de, "Français": fr, "Italiano": it}[language]

# App title
st.title(tr("🔧 Beam Designer Pro (Eurocode)",
            "🔧 Balkendesigner Pro (Eurocode)",
            "🔧 Concepteur de poutre Pro (Eurocode)",
            "🔧 Progettista di travi Pro (Eurocodice)"))

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header(tr("Beam Inputs", "Balken-Eingaben", "Entrées de poutre", "Input trave"))

L = st.sidebar.number_input(tr("Span Length L [m]", "Stützweite L [m]", "Portée L [m]", "Luce L [m]"), 1.0, 20.0, 5.0)
q_uni = st.sidebar.number_input(tr("Uniform Load [kN/m]", "Gleichlast [kN/m]", "Charge uniforme [kN/m]", "Carico uniforme [kN/m]"), 0.0, 100.0, 10.0)
q_point = st.sidebar.number_input(tr("Point Load at Center [kN]", "Einzellast Mitte [kN]", "Charge ponctuelle au centre [kN]", "Carico puntuale al centro [kN]"), 0.0, 100.0, 0.0)
beam_type = st.sidebar.selectbox(tr("Beam Type", "Balkentyp", "Type de poutre", "Tipo di trave"), ["Simply Supported", "Cantilever"])
b = st.sidebar.number_input("Beam Width b [mm]", 100, 1000, 300)
h = st.sidebar.number_input("Beam Height h [mm]", 100, 1500, 500)
cover = st.sidebar.number_input("Concrete Cover [mm]", 10, 100, 25)
phi = st.sidebar.selectbox("Rebar Diameter [mm]", [8, 10, 12, 14, 16, 20, 25], 4)
f_ck = st.sidebar.selectbox("Concrete fck [MPa]", [20, 25, 30, 35, 40], 2)
f_yk = st.sidebar.selectbox("Steel fyk [MPa]", [500, 550], 0)

# -----------------------------
# Structural Calculations
# -----------------------------
x = np.linspace(0, L, 100)
M = np.zeros_like(x)
V_max = 0

if beam_type == "Simply Supported":
    if q_uni > 0:
        M += q_uni * x * (L - x) / 2
        V_max += q_uni * L / 2
    if q_point > 0:
        M += np.piecewise(x, [x < L/2, x >= L/2], [lambda x: q_point * x / 2, lambda x: q_point * (L - x) / 2])
        V_max += q_point / 2
elif beam_type == "Cantilever":
    if q_uni > 0:
        M -= q_uni * x**2 / 2
        V_max += q_uni * L
    if q_point > 0:
        M += np.piecewise(x, [x < L, x >= L], [0, lambda x: -q_point * L])
        V_max += q_point

M_max = abs(M).max()

# Design parameters
b_m = b / 1000
h_m = h / 1000
z = 0.9 * h_m
phi_m = phi / 1000
d = h - cover - phi / 2
f_cd = f_ck / 1.5 * 1e6
f_yd = f_yk / 1.15 * 1e6

As_single = np.pi * (phi_m ** 2) / 4
As_req = (M_max * 1e6) / (z * f_yd)
n_bars = int(np.ceil(As_req / As_single))
As_prov = n_bars * As_single
ld = phi * f_yk / (4 * 1.4)

# Shear design
V_rd_c = 0.12 * 1000 * (100 * As_prov / (b * d))**(1/3) * b * d / 1000
shear_safe = V_max < V_rd_c

# Deflection check
deflection_ratio = L / h
deflection_ok = deflection_ratio <= (20 if beam_type == "Simply Supported" else 7)

# -----------------------------
# Results Summary
# -----------------------------
st.markdown("### 📊 " + tr("Design Summary", "Bemessungsübersicht", "Résumé du dimensionnement", "Riepilogo progettazione"))
st.success(f"""
- **M<sub>max</sub>** = {M_max:.2f} kNm  
- **V<sub>max</sub>** = {V_max:.2f} kN  
- **As<sub>req</sub>** = {As_req * 1e4:.2f} cm² → Ø{phi} × {n_bars}  
- **Development Length** = {ld:.0f} mm  
- **Shear Check**: {"✅ OK" if shear_safe else "❌ Not OK"}  
- **Deflection Check**: {"✅ OK" if deflection_ok else "❌ Not OK"}  
""", unsafe_allow_html=True)

# -----------------------------
# Moment Diagram
# -----------------------------
fig, ax = plt.subplots(figsize=(8, 2.5))
ax.plot(x, M, label="Moment [kNm]", linewidth=2)
ax.set_xlabel("Length [m]")
ax.set_ylabel("Moment [kNm]")
ax.set_title("Bending Moment Diagram")
ax.grid(True)
ax.axhline(0, color='gray')
ax.legend()
st.pyplot(fig)

# -----------------------------
# Beam Cross Section
# -----------------------------
fig2, ax2 = plt.subplots(figsize=(4.5, 3))
ax2.set_xlim(0, b)
ax2.set_ylim(0, h)
ax2.set_aspect('equal')
ax2.add_patch(plt.Rectangle((0, 0), b, h, fill=False, edgecolor='black', linewidth=2))
spacing = (b - 2 * cover) / (n_bars - 1) if n_bars > 1 else 0
for i in range(n_bars):
    x_pos = cover + i * spacing if n_bars > 1 else b / 2
    ax2.add_patch(plt.Circle((x_pos, cover), phi / 2, color='black'))
ax2.set_title("Beam Cross-Section")
ax2.invert_yaxis()
ax2.grid(True)
st.pyplot(fig2)

# -----------------------------
# PDF Export
# -----------------------------
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Beam Design Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, f"Span: {L} m | Type: {beam_type}", ln=True)
    pdf.cell(200, 10, f"Uniform Load: {q_uni} kN/m | Point Load: {q_point} kN", ln=True)
    pdf.cell(200, 10, f"M_max: {M_max:.2f} kNm | V_max: {V_max:.2f} kN", ln=True)
    pdf.cell(200, 10, f"As required: {As_req * 1e4:.2f} cm² → Ø{phi} × {n_bars}", ln=True)
    pdf.cell(200, 10, f"Development Length: {ld:.0f} mm", ln=True)
    pdf.cell(200, 10, f"Shear: {'OK' if shear_safe else 'NOT OK'}", ln=True)
    pdf.cell(200, 10, f"Deflection: {'OK' if deflection_ok else 'NOT OK'}", ln=True)
    return pdf

if st.button("📄 Generate PDF Report"):
    pdf = create_pdf()
    output = BytesIO()
    output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📥 Download PDF", data=output.getvalue(), file_name="beam_report.pdf", mime="application/pdf")

# -----------------------------
# Excel Export
# -----------------------------
data = {
    "Span (m)": [L],
    "M_max (kNm)": [M_max],
    "V_max (kN)": [V_max],
    "As_required (cm²)": [As_req * 1e4],
    "Bars Ø (mm)": [phi],
    "No. Bars": [n_bars],
    "Development Length (mm)": [ld],
    "Shear OK": ["Yes" if shear_safe else "No"],
    "Deflection OK": ["Yes" if deflection_ok else "No"]
}
df = pd.DataFrame(data)
excel_bytes = BytesIO()
df.to_excel(excel_bytes, index=False, engine='openpyxl')
excel_bytes.seek(0)
st.download_button("📊 Download Excel Summary", data=excel_bytes, file_name="beam_summary.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Footer
st.caption(tr(
    "Designed according to Eurocode 2. Always confirm with a qualified structural engineer.",
    "Entworfen nach Eurocode 2. Immer mit Statiker überprüfen.",
    "Conçu selon l'Eurocode 2. À vérifier avec un ingénieur.",
    "Progettato secondo l'Eurocodice 2. Verificare con un ingegnere strutturista."
))
