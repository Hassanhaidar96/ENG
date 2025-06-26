# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 22:50:12 2025
@author: DellG15
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

# Language support
language = st.sidebar.selectbox("Language / Sprache / Langue", ["English", "Deutsch", "Français", "Italiano"], index=0)

def tr(en, de, fr, it):
    return {
        "English": en,
        "Deutsch": de,
        "Français": fr,
        "Italiano": it
    }[language]

st.set_page_config(page_title="Interactive Beam Designer", layout="wide")
st.title(tr("🔧 Interactive Beam Designer (Eurocode)",
            "🔧 Interaktiver Balkendesigner (Eurocode)",
            "🔧 Concepteur de poutre interactif (Eurocode)",
            "🔧 Progettista di travi interattivo (Eurocodice)"))

# Sidebar inputs
st.sidebar.header(tr("Beam Inputs", "Balken-Eingaben", "Entrées de poutre", "Input trave"))
L = st.sidebar.number_input(tr("Span Length L [m]", "Stützweite L [m]", "Portée L [m]", "Luce L [m]"), value=5.0, min_value=1.0, step=0.1)
q = st.sidebar.number_input(tr("Load Magnitude q [kN] or [kN/m]", "Last q [kN] oder [kN/m]", "Charge q [kN] ou [kN/m]", "Carico q [kN] o [kN/m]"), value=10.0, min_value=0.0, step=0.5)
load_type = st.sidebar.selectbox(tr("Load Type", "Lastart", "Type de charge", "Tipo di carico"), ["Uniform", "Point at center"])
beam_type = st.sidebar.selectbox(tr("Beam Type", "Balkentyp", "Type de poutre", "Tipo di trave"), ["Simply Supported", "Cantilever"])
b = st.sidebar.number_input(tr("Beam Width b [mm]", "Balkenbreite b [mm]", "Largeur de la poutre b [mm]", "Larghezza trave b [mm]"), value=300, min_value=100, step=10)
h = st.sidebar.number_input(tr("Beam Height h [mm]", "Balkenhöhe h [mm]", "Hauteur de la poutre h [mm]", "Altezza trave h [mm]"), value=500, min_value=100, step=10)
cover = st.sidebar.number_input(tr("Concrete Cover [mm]", "Betondeckung [mm]", "Enrobage béton [mm]", "Copriferro [mm]"), value=25, min_value=10, step=5)
phi = st.sidebar.selectbox(tr("Rebar Diameter [mm]", "Durchmesser Bewehrung [mm]", "Diamètre armature [mm]", "Diametro armatura [mm]"), options=[8, 10, 12, 14, 16, 20, 25, 32], index=4)
f_ck = st.sidebar.selectbox(tr("Concrete Class fck [MPa]", "Betonklasse fck [MPa]", "Classe béton fck [MPa]", "Classe del calcestruzzo fck [MPa]"), options=[20, 25, 30, 35, 40], index=2)
f_yk = st.sidebar.selectbox(tr("Steel Yield Strength fyk [MPa]", "Streckgrenze fyk [MPa]", "Limite élastique fyk [MPa]", "Snervamento acciaio fyk [MPa]"), options=[500, 550], index=0)

# Calculations
x = np.linspace(0, L, 100)
if beam_type == "Simply Supported":
    if load_type == "Uniform":
        M_max = q * L**2 / 8
        V_max = q * L / 2
        M = q * x * (L - x) / 2
    else:
        M_max = q * L / 4
        V_max = q / 2
        M = np.piecewise(x, [x < L/2, x >= L/2], [lambda x: q*x/2, lambda x: q*(L - x)/2])
elif beam_type == "Cantilever":
    if load_type == "Uniform":
        M_max = q * L**2 / 2
        V_max = q * L
        M = -q * x**2 / 2
    else:
        M_max = q * L
        V_max = q
        M = np.piecewise(x, [x < L, x >= L], [0, lambda x: -q * L])

# Convert to consistent units
b_m = b / 1000
h_m = h / 1000
z = 0.9 * h_m
f_cd = f_ck / 1.5 * 1e6
f_yd = f_yk / 1.15 * 1e6

phi_m = phi / 1000
d = h - cover - phi / 2
As_single = np.pi * (phi_m**2) / 4
As_req = (M_max * 1e6) / (z * f_yd)
n_bars = int(np.ceil(As_req / As_single))
As_prov = n_bars * As_single
ld = phi * f_yk / (4 * 1.4)

# Shear design
V_rd_c = 0.12 * 1000 * (100 * As_prov / (b * d))**(1/3) * b * d / 1000
shear_safe = V_max < V_rd_c

# Display results
st.subheader(tr("🧮 Design Results", "🧮 Bemessungsergebnisse", "🧮 Résultats de dimensionnement", "🧮 Risultati del progetto"))
col1, col2 = st.columns(2)

with col1:
    st.metric(tr("Max Bending Moment [kNm]", "Max. Biegemoment [kNm]", "Moment maximum [kNm]", "Momento massimo [kNm]"), f"{M_max:.2f}")
    st.metric(tr("Max Shear Force [kN]", "Max. Querkraft [kN]", "Effort tranchant max [kN]", "Taglio massimo [kN]"), f"{V_max:.2f}")
    st.metric(tr("Required As [cm²]", "Erforderliche As [cm²]", "Acier requis As [cm²]", "Armatura richiesta As [cm²]"), f"{As_req*1e4:.2f}")

with col2:
    st.metric(tr("Bars Ø{} mm Needed", "Benötigte Ø{} mm Stäbe", "Barres Ø{} mm nécessaires", "Barre Ø{} mm richieste").format(phi), f"{n_bars}")
    st.metric(tr("Provided As [cm²]", "Vorhandene As [cm²]", "As fournie [cm²]", "As fornita [cm²]"), f"{As_prov*1e4:.2f}")
    st.metric(tr("Dev. Length [mm]", "Verankerungslänge [mm]", "Longueur d'ancrage [mm]", "Lunghezza di ancoraggio [mm]"), f"{ld:.0f}")
    st.metric(tr("Shear OK?", "Querkraft OK?", "Effort tranchant OK?", "Taglio OK?"), "✅" if shear_safe else "❌")

# Visualization - Moment Diagram
fig, ax = plt.subplots(figsize=(10, 2))
ax.plot(x, M, label=tr("Moment Diagram", "Momentendiagramm", "Diagramme des moments", "Diagramma dei momenti"), linewidth=2)
ax.set_title(tr("Bending Moment Diagram", "Momentenverlauf", "Diagramme du moment fléchissant", "Diagramma del momento flettente"))
ax.set_xlabel(tr("Beam Length [m]", "Balkenlänge [m]", "Longueur de la poutre [m]", "Lunghezza trave [m]"))
ax.set_ylabel(tr("Moment [kNm]", "Moment [kNm]", "Moment [kNm]", "Momento [kNm]"))
ax.grid(True)
ax.axhline(0, color='black', linewidth=0.5)
ax.legend()
st.pyplot(fig)

# Visualization - Beam Cross-Section
fig2, ax2 = plt.subplots(figsize=(6, 4))
ax2.set_xlim(0, b)
ax2.set_ylim(0, h)
ax2.set_aspect('equal')

# Draw beam rectangle
ax2.add_patch(plt.Rectangle((0, 0), b, h, fill=None, edgecolor='black', linewidth=2))

# Draw rebars
bar_spacing = (b - 2 * cover) / (n_bars - 1) if n_bars > 1 else 0
for i in range(n_bars):
    x_pos = cover + i * bar_spacing if n_bars > 1 else b / 2
    ax2.add_patch(plt.Circle((x_pos, cover), phi / 2, color='black'))

ax2.set_title(tr("Beam Cross-Section with Rebars", "Balkenquerschnitt mit Bewehrung", "Coupe transversale avec armatures", "Sezione trasversale con armature"))
ax2.set_xlabel(tr("Width [mm]", "Breite [mm]", "Largeur [mm]", "Larghezza [mm]"))
ax2.set_ylabel(tr("Height [mm]", "Höhe [mm]", "Hauteur [mm]", "Altezza [mm]"))
st.pyplot(fig2)

# PDF Export
st.subheader(tr("📄 Export Report", "📄 Bericht exportieren", "📄 Exporter le rapport", "📄 Esporta rapporto"))

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Beam Design Report", ln=True, align='C')
    pdf.ln(10)
    load_unit = "kN/m" if load_type == "Uniform" else "kN"
    pdf.cell(100, 10, f"Span: {L} m")
    pdf.cell(100, 10, f"Load: {q} {load_unit}", ln=True)
    pdf.cell(100, 10, f"Beam Type: {beam_type}")
    pdf.cell(100, 10, f"Load Type: {load_type}", ln=True)
    pdf.cell(100, 10, f"Moment: {M_max:.2f} kNm")
    pdf.cell(100, 10, f"Shear: {V_max:.2f} kN", ln=True)
    pdf.cell(100, 10, f"Required As: {As_req*1e4:.2f} cm²")
    pdf.cell(100, 10, f"Provided As: {As_prov*1e4:.2f} cm²", ln=True)
    pdf.cell(100, 10, f"Bars Ø{phi} mm: {n_bars}")
    pdf.cell(100, 10, f"Dev. Length: {ld:.0f} mm", ln=True)
    pdf.cell(200, 10, f"Shear Check: {'OK' if shear_safe else 'NOT OK'}", ln=True)
    return pdf

if st.button(tr("Generate PDF Report", "PDF-Bericht erzeugen", "Générer le rapport PDF", "Genera rapporto PDF")):
    pdf = create_pdf()
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button(
        label=tr("📥 Download Beam Report", "📥 Balkenbericht herunterladen", "📥 Télécharger le rapport", "📥 Scarica il rapporto"),
        data=pdf_output.getvalue(),
        file_name="beam_design_report.pdf",
        mime="application/pdf"
    )

st.caption(tr(
    "Designed according to simplified Eurocode 2 assumptions. Always verify final design with a professional engineer.",
    "Entworfen gemäß vereinfachten Annahmen nach Eurocode 2. Endgültige Bemessung von Fachpersonen prüfen lassen.",
    "Conçu selon des hypothèses simplifiées du Eurocode 2. Vérifier avec un ingénieur qualifié.",
    "Progettato secondo assunzioni semplificate dell'Eurocodice 2. Verificare con un ingegnere qualificato."
))
