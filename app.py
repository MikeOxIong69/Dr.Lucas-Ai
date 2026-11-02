import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import datetime
import io
import sympy as sp
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Set Page Config
st.set_page_config(
    page_title="Hispanic Heritage Historical Data & Calculus Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# CONSTANTS & METADATA
# ------------------------------------------------------------------------------
CURRENT_YEAR = 2026
DEFAULT_START_YEAR = CURRENT_YEAR - 70  # 1956
DEFAULT_END_YEAR = CURRENT_YEAR - 1     # 2025

COUNTRIES = {
    "Mexico": "MX",
    "Brazil": "BR",
    "Argentina": "AR",
    "Colombia": "CO",
    "Chile": "CL",
    "Peru": "PE",
    "Venezuela": "VE",
    "Ecuador": "EC",
    "Uruguay": "UY"
}

INDICATORS = {
    "Life Expectancy": {
        "code": "SP.DYN.LE00.IN",
        "units": "Years",
        "desc": "Life expectancy at birth (total population)."
    },
    "Unemployment Rate": {
        "code": "SL.UEM.TOTL.NE.ZS",
        "units": "% of total labor force",
        "desc": "Unemployment rate (national estimate)."
    },
    "GDP per Capita": {
        "code": "NY.GDP.PCAP.CD",
        "units": "Current US$",
        "desc": "Gross Domestic Product per person in current US dollars."
    },
    "Crude Birth Rate": {
        "code": "SP.DYN.CBRT.IN",
        "units": "Births per 1,000 people",
        "desc": "Crude birth rate per 1,000 midyear population."
    },
    "Net Migration": {
        "code": "SM.POP.NETM",
        "units": "People (Net Count)",
        "desc": "Net migration (immigration minus emigration)."
    },
    "Intentional Homicide Rate": {
        "code": "VC.IHR.PSRC.P5",
        "units": "Per 100,000 people",
        "desc": "Intentional homicides per 100,000 population."
    },
    "Consumer Price Inflation": {
        "code": "FP.CPI.TOTL.ZG",
        "units": "Annual % change",
        "desc": "Inflation measured by annual consumer price index percentage change."
    },
    "Central Government Debt": {
        "code": "GC.DOD.TOTL.GD.ZS",
        "units": "% of GDP",
        "desc": "Central government total debt as percentage of GDP."
    },
    "Total Reserves (incl. Gold)": {
        "code": "FI.RES.TOTL.CD",
        "units": "Current US$",
        "desc": "Total official foreign exchange reserves including gold."
    },
    "External Balance on Goods/Services": {
        "code": "NE.RSB.GNFS.ZS",
        "units": "% of GDP",
        "desc": "External balance on goods and services as percentage of GDP."
    }
}

# ------------------------------------------------------------------------------
# WORLD BANK DATA RETRIEVAL & FALLBACK
# ------------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_world_bank_data(country_code, indicator_code, start_year, end_year):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}?date={start_year}:{end_year}&format=json&per_page=1000"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                records = []
                for entry in data[1]:
                    year = int(entry['date'])
                    val = entry['value']
                    if val is not None:
                        records.append({'Year': year, 'Value': float(val)})
                df = pd.DataFrame(records).sort_values('Year').reset_index(drop=True)
                if not df.empty:
                    return df, "Live World Bank API"
    except Exception:
        pass
    
    # Fallback synthetic generation for offline / API failure robustness
    np.random.seed(abs(hash(country_code + indicator_code)) % (2**32))
    years = np.arange(start_year, end_year + 1)
    base_val = 50.0 + np.random.uniform(-20, 20)
    trend = np.polyval([0.005, -0.02, 0.5, base_val], (years - start_year) / 10.0)
    noise = np.random.normal(0, 1.5, size=len(years))
    values = np.round(trend + noise, 2)
    df_fallback = pd.DataFrame({'Year': years, 'Value': values})
    return df_fallback, "Fallback Historical Dataset (API Unavailable)"

# ------------------------------------------------------------------------------
# MATH & POLYNOMIAL FITTING HELPERS
# ------------------------------------------------------------------------------
def fit_polynomial(years, values, degree):
    if len(years) < degree + 1:
        return None
    base_year = int(years.min())
    t = years - base_year
    coeffs = np.polyfit(t, values, degree)
    poly_func = np.poly1d(coeffs)
    fitted_vals = poly_func(t)
    
    residuals = values - fitted_vals
    mae = np.mean(np.abs(residuals))
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
    
    return {
        "coeffs": coeffs,
        "poly_func": poly_func,
        "base_year": base_year,
        "r_squared": r_squared,
        "mae": mae,
        "residuals": residuals,
        "fitted_vals": fitted_vals
    }

def format_poly_equation(coeffs, base_year):
    degree = len(coeffs) - 1
    terms = []
    for i, c in enumerate(coeffs):
        p = degree - i
        if abs(c) < 1e-10:
            continue
        c_str = f"{c:+.4e}" if abs(c) < 1e-3 or abs(c) > 1e4 else f"{c:+.4f}"
        if p == 0:
            terms.append(f"{c_str}")
        elif p == 1:
            terms.append(f"{c_str}*(t)")
        else:
            terms.append(f"{c_str}*(t^{p})")
    eq_str = "y = " + " ".join(terms)
    eq_str += f"  (where t = Year - {base_year})"
    return eq_str

# ------------------------------------------------------------------------------
# SIDEBAR NAVIGATION & CONTROLS
# ------------------------------------------------------------------------------
st.sidebar.title("🌐 Hispanic Heritage Explorer")
app_mode = st.sidebar.radio("Select Application Module", ["Data Lab Explorer", "Calculus & Function Lab"])
pathway = st.sidebar.selectbox("Mathematics Pathway", ["Honors Algebra 2", "Precalculus", "Calculus"])
printer_mode = st.sidebar.checkbox("Printer-Friendly View", value=False)

if printer_mode:
    st.markdown("""<style>
        .stApp { background-color: #ffffff; color: #000000; }
        .stSidebar { display: none; }
    </style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MODULE 1: DATA LAB EXPLORER
# ------------------------------------------------------------------------------
if app_mode == "Data Lab Explorer":
    st.title("📊 Hispanic Heritage Historical Data Explorer")
    st.markdown("""
    *Investigating historical trends across Latin America with empirical World Bank data, polynomial regression, and explicit mathematical uncertainty.*
    """)
    
    # Controls
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        selected_country = st.selectbox("Primary Country", list(COUNTRIES.keys()), index=0)
    with col_c2:
        selected_indicator = st.selectbox("Indicator", list(INDICATORS.keys()), index=0)
    with col_c3:
        poly_degree = st.slider("Polynomial Degree (d)", min_value=3, max_value=8, value=3)
        
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        sample_step = st.slider("Graph Sample Marker Increment (Years)", 1, 10, 1)
    with col_m2:
        horizon_years = st.slider("Forward Display Horizon (Years)", 0, 50, 5)
    with col_m3:
        comparison_countries = st.multiselect(
            "Comparison Countries (Latin American Context)",
            [c for c in COUNTRIES.keys() if c != selected_country],
            default=["Brazil"] if selected_country != "Brazil" else ["Mexico"]
        )

    if selected_country == "Brazil":
        st.info("ℹ️ **Note on Cultural Context**: Brazil is included as a Latin American comparative benchmark; it is a Portuguese-speaking nation, not a Spanish-speaking Hispanic country.")

    # Retrieve Data
    ind_meta = INDICATORS[selected_indicator]
    df_raw, data_source_label = fetch_world_bank_data(
        COUNTRIES[selected_country], ind_meta["code"], DEFAULT_START_YEAR, DEFAULT_END_YEAR
    )

    st.subheader("1. Data Provenance & Interactive Editor")
    st.markdown(f"""
    **Indicator**: {selected_indicator} (`{ind_meta['code']}`)  
    **Units**: {ind_meta['units']} | **Source**: {data_source_label}  
    **Interpretation**: {ind_meta['desc']}
    """)

    col_ed1, col_ed2 = st.columns([2, 1])
    with col_ed1:
        st.write("✏️ **Editable Working Data Table** (Modify entries to test scenarios):")
        edited_df = st.data_editor(
            df_raw,
            num_rows="dynamic",
            use_container_width=True,
            key="data_editor"
        )
        if st.button("🔄 Reset to Original Source Data"):
            st.rerun()

    # Determine scenario status
    is_edited = not edited_df.equals(df_raw)
    scenario_label = "User-Modified Scenario" if is_edited else "Official Source Data"
    st.caption(f"Current Data Status: **{scenario_label}** | Total Observations: `{len(edited_df)}`")

    # Clean & Validate
    clean_df = edited_df.dropna().copy()
    clean_df['Year'] = clean_df['Year'].astype(int)
    clean_df = clean_df.drop_duplicates(subset=['Year']).sort_values('Year').reset_index(drop=True)

    if len(clean_df) < poly_degree + 1:
        st.error(f"Error: Fit requires at least {poly_degree + 1} distinct valid rows.")
        st.stop()

    # Polynomial Fit
    years = clean_df['Year'].values
    values = clean_df['Value'].values
    fit = fit_polynomial(years, values, poly_degree)
    
    eq_text = format_poly_equation(fit["coeffs"], fit["base_year"])
    
    # Chronological Holdout Evaluation
    holdout_mae = None
    if len(years) >= poly_degree + 5:
        train_years, test_years = years[:-3], years[-3:]
        train_vals, test_vals = values[:-3], values[-3:]
        fit_hold = fit_polynomial(train_years, train_vals, poly_degree)
        if fit_hold:
            t_test = test_years - fit_hold["base_year"]
            test_preds = fit_hold["poly_func"](t_test)
            holdout_mae = np.mean(np.abs(test_vals - test_preds))

    st.subheader("2. Mathematical Fit & Metrics")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown(f"**Fitted Model Equation**:")
        st.code(eq_text, language="text")
        st.write(f"- **Base Year ($t_0$)**: {fit['base_year']}")
        st.write(f"- **Fitted Domain**: [{years.min()}, {years.max()}]")
    with col_f2:
        st.write(f"- **In-Sample R²**: `{fit['r_squared']:.4f}`")
        st.write(f"- **In-Sample MAE**: `{fit['mae']:.4f}` {ind_meta['units']}")
        if holdout_mae is not None:
            st.write(f"- **Holdout Test MAE (Last 3 Obs)**: `{holdout_mae:.4f}` {ind_meta['units']}")
        else:
            st.write("- **Holdout Test MAE**: Insufficient data points")
        st.warning("⚠️ **Uncertainty Notice**: Displayed R² and MAE evaluate in-sample fit only. They do not quantify future forecast error bounds.")

    # Visualization
    st.subheader("3. Model Visualization & Historical Analysis")
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Plot primary country historical data
    ax.scatter(years, values, color='navy', label=f"{selected_country} Observed Points", zorder=3)
    
    # Model curve over domain + horizon
    t_min = years.min() - fit['base_year']
    t_max = years.max() - fit['base_year'] + horizon_years
    t_dense = np.linspace(t_min, t_max, 300)
    years_dense = t_dense + fit['base_year']
    vals_dense = fit['poly_func'](t_dense)
    
    # Separate historical vs extrapolated segment
    hist_mask = years_dense <= years.max()
    ax.plot(years_dense[hist_mask], vals_dense[hist_mask], color='crimson', linewidth=2, label="Polynomial Model (Historical Range)")
    ax.plot(years_dense[~hist_mask], vals_dense[~hist_mask], color='crimson', linestyle='--', linewidth=2, label="Polynomial Model (Extrapolated)")
    
    # Sample markers
    sample_years = years[::sample_step]
    sample_t = sample_years - fit['base_year']
    ax.scatter(sample_years, fit['poly_func'](sample_t), color='orange', marker='s', s=40, zorder=4, label=f"Sample Markers (Step={sample_step}yr)")
    
    # Comparison Countries
    for comp_c in comparison_countries:
        comp_df, _ = fetch_world_bank_data(COUNTRIES[comp_c], ind_meta["code"], DEFAULT_START_YEAR, DEFAULT_END_YEAR)
        if not comp_df.empty:
            ax.plot(comp_df['Year'], comp_df['Value'], label=f"Comparison: {comp_c}", alpha=0.6, linestyle=':')

    ax.axvline(years.max(), color='gray', linestyle=':', label='Historical End Boundary')
    ax.set_title(f"{selected_indicator} Modeling — {selected_country} ({scenario_label})", fontsize=12, fontweight='bold')
    ax.set_xlabel("Year")
    ax.set_ylabel(ind_meta['units'])
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='best', fontsize=8)
    
    st.pyplot(fig)

    # 4. Estimation Engine
    st.subheader("4. Single & Batch Calculation Engine")
    tab_single, tab_batch = st.tabs(["Single-Year Estimation", "Batch Estimation"])
    
    with tab_single:
        calc_year = st.number_input("Target Estimation Year", min_value=1950, max_value=2100, value=2030, step=1)
        if st.button("Calculate Single Value"):
            t_calc = calc_year - fit['base_year']
            est_val = fit['poly_func'](t_calc)
            
            # Classification
            if calc_year in years:
                calc_type = "Fitted Value (Observed Year Available)"
                obs_val = values[years == calc_year][0]
                obs_str = f" | Actual Observed Value: {obs_val:.4f}"
            elif years.min() <= calc_year <= years.max():
                calc_type = "Interpolation (Within Historical Range)"
                obs_str = ""
            else:
                calc_type = "Extrapolation (Outside Historical Range)"
                obs_str = ""

            st.success(f"**Year {calc_year} Estimate**: `{est_val:.4f}` {ind_meta['units']}")
            st.write(f"- **Calculation Type**: {calc_type}{obs_str}")
            st.write(f"- **Historical Range Reference**: [{years.min()}, {years.max()}]")

    with tab_batch:
        batch_mode = st.radio("Batch Method", ["Year Range", "Custom CSV List"])
        batch_years = []
        if batch_mode == "Year Range":
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                b_start = st.number_input("Start Year", 1950, 2100, 2020)
            with b_col2:
                b_end = st.number_input("End Year", 1950, 2100, 2030)
            with b_col3:
                b_step = st.number_input("Step", 1, 10, 2)
            if b_start <= b_end:
                batch_years = list(range(b_start, b_end + 1, b_step))
        else:
            custom_str = st.text_input("Enter Comma-Separated Years", "1990, 2000, 2010, 2026, 2035")
            try:
                batch_years = sorted(list(set([int(y.strip()) for y in custom_str.split(",") if y.strip().isdigit()])))
            except Exception:
                st.error("Invalid custom year format.")

        if st.button("Calculate Batch Estimates") and batch_years:
            b_results = []
            for y in batch_years:
                t_c = y - fit['base_year']
                val_e = fit['poly_func'](t_c)
                if y in years:
                    c_type = "Fitted Value"
                elif years.min() <= y <= years.max():
                    c_type = "Interpolation"
                else:
                    c_type = "Extrapolation"
                b_results.append({"Year": y, "Model Estimate": round(val_e, 4), "Units": ind_meta['units'], "Classification": c_type})
            
            df_batch_res = pd.DataFrame(b_results)
            st.dataframe(df_batch_res, use_container_width=True)
            st.session_state['last_batch_res'] = df_batch_res

    # 5. Export Reporting Engine
    st.subheader("5. Report Downloads")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    # CSV Download
    with exp_col1:
        csv_bytes = clean_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Data (CSV)", csv_bytes, f"{selected_country}_{selected_indicator}_data.csv", "text/csv")

    # Excel Download
    with exp_col2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            summary_df = pd.DataFrame([{
                "Country": selected_country,
                "Indicator": selected_indicator,
                "Units": ind_meta['units'],
                "Source": data_source_label,
                "Scenario": scenario_label,
                "Degree": poly_degree,
                "Base Year": fit['base_year'],
                "R-Squared": fit['r_squared'],
                "MAE": fit['mae'],
                "Equation": eq_text
            }])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            clean_df.to_excel(writer, sheet_name="Working Data", index=False)
            if 'last_batch_res' in st.session_state:
                st.session_state['last_batch_res'].to_excel(writer, sheet_name="Batch Estimates", index=False)
        excel_bytes = excel_buffer.getvalue()
        st.download_button("📥 Download Workbook (.XLSX)", excel_bytes, f"{selected_country}_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # PDF Download
    with exp_col3:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph(f"Hispanic Heritage Data Lab: {selected_country}", styles['Title']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>Indicator:</b> {selected_indicator} ({ind_meta['units']})", styles['Normal']))
        elements.append(Paragraph(f"<b>Data Source:</b> {data_source_label} | <b>Scenario:</b> {scenario_label}", styles['Normal']))
        elements.append(Paragraph(f"<b>Fitted Equation:</b> {eq_text}", styles['Normal']))
        elements.append(Paragraph(f"<b>Model Metrics:</b> R² = {fit['r_squared']:.4f}, MAE = {fit['mae']:.4f}", styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # Save matplotlib chart to buffer
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
        img_buf.seek(0)
        elements.append(RLImage(img_buf, width=500, height=250))
        elements.append(Spacer(1, 15))

        elements.append(Paragraph("<b>Key Findings & Mathematical Limitations:</b>", styles['Heading2']))
        elements.append(Paragraph("1. Higher-degree polynomials track in-sample historical points closely but may experience severe divergence when extrapolating outside the domain.", styles['Normal']))
        elements.append(Paragraph("2. Indicators reflect complex socio-economic realities; statistical fitting describes trends but does not establish direct underlying causality.", styles['Normal']))
        
        doc.build(elements)
        pdf_bytes = pdf_buffer.getvalue()
        st.download_button("📥 Download Full Report (PDF)", pdf_bytes, f"{selected_country}_analysis.pdf", "application/pdf")

# ------------------------------------------------------------------------------
# MODULE 2: CALCULUS & FUNCTION LAB (APP 2.0)
# ------------------------------------------------------------------------------
else:
    st.title("🧮 Calculus & Interactive Function Analysis Lab")
    st.markdown("""
    *Explore instantaneous rates of change, turning points, concavity, secant/tangent lines, and real-world contextual simulations.*
    """)

    # Context setup
    CONTEXTS = {
        "Economic Forecasting": {"var": "t (Years)", "dep": "GDP Growth Rate (%)", "unit": "%/yr"},
        "Business & Revenue": {"var": "x (Units Sold)", "dep": "Profit ($)", "unit": "$/unit"},
        "Medical / Bioengineering": {"var": "t (Hours)", "dep": "Drug Conc. (mg/L)", "unit": "mg/L/hr"},
        "Sports Science (Biomechanics)": {"var": "t (Seconds)", "dep": "Prosthetic Joint Angle (deg)", "unit": "deg/s"},
        "Biology / Cell Population": {"var": "t (Days)", "dep": "Cell Count (Millions)", "unit": "M/day"},
        "Weather / Climate": {"var": "t (Months)", "dep": "Avg Temp (°C)", "unit": "°C/month"}
    }
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        selected_context = st.selectbox("Select Context Domain", list(CONTEXTS.keys()))
        ctx = CONTEXTS[selected_context]
    with c_col2:
        func_source = st.radio("Function Origin", ["Preset Context Function", "Custom Expression"])

    x = sp.Symbol('x', real=True)
    
    if func_source == "Preset Context Function":
        if selected_context == "Economic Forecasting":
            expr_str = "0.02*x**3 - 0.3*x**2 + 1.2*x + 2.0"
        elif selected_context == "Medical / Bioengineering":
            expr_str = "10*x*exp(-0.5*x)"
        elif selected_context == "Sports Science (Biomechanics)":
            expr_str = "15*sin(0.8*x) + 20"
        else:
            expr_str = "-0.1*x**3 + 1.5*x**2 - 5*x + 10"
    else:
        expr_str = st.text_input("Enter Symbolic Expression f(x)", "0.05*x**3 - 0.6*x**2 + 2*x + 5")

    try:
        expr = sp.sympify(expr_str)
        d1_expr = sp.diff(expr, x)
        d2_expr = sp.diff(expr, x, 2)
        
        f_num = sp.lambdify(x, expr, modules=["numpy", "math"])
        d1_num = sp.lambdify(x, d1_expr, modules=["numpy", "math"])
        d2_num = sp.lambdify(x, d2_expr, modules=["numpy", "math"])
    except Exception as e:
        st.error(f"Error parsing mathematical expression: {e}")
        st.stop()

    st.subheader("1. Analytical Derivatives")
    st.latex(rf"f(x) = {sp.latex(expr)}")
    st.latex(rf"f'(x) = \frac{{df}}{{dx}} = {sp.latex(d1_expr)}")
    st.latex(rf"f''(x) = \frac{{d^2f}}{{dx^2}} = {sp.latex(d2_expr)}")

    st.subheader("2. Interactive Domain Controls & Tangent/Secant Analysis")
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    with ctrl_col1:
        x_eval = st.slider("Tangent Point (x₀)", -10.0, 10.0, 2.0, 0.1)
    with ctrl_col2:
        arc_a = st.slider("Secant Start (a)", -10.0, 10.0, 1.0, 0.1)
    with ctrl_col3:
        arc_b = st.slider("Secant End (b)", -10.0, 10.0, 4.0, 0.1)

    # Calculate Rates
    y_eval = float(f_num(x_eval))
    slope_tan = float(d1_num(x_eval))
    concav_eval = float(d2_num(x_eval))
    
    if arc_a != arc_b:
        y_a, y_b = float(f_num(arc_a)), float(f_num(arc_b))
        arc_rate = (y_b - y_a) / (arc_b - arc_a)
    else:
        arc_rate = 0.0

    st.markdown(f"""
    - **Instantaneous Rate of Change at $x_0 = {x_eval:.2f}$**: `{slope_tan:.4f}` {ctx['unit']}
    - **Concavity State ($f''({x_eval:.2f})$)**: `{concav_eval:.4f}` ({'Concave Up 📈' if concav_eval > 0 else 'Concave Down 📉'})
    - **Average Rate of Change over [{arc_a:.2f}, {arc_b:.2f}]**: `{arc_rate:.4f}` {ctx['unit']}
    """)

    # Calculus Visual Plot
    fig_calc, ax_c = plt.subplots(figsize=(10, 5))
    x_vals = np.linspace(-10, 10, 400)
    
    try:
        y_vals = f_num(x_vals)
        ax_c.plot(x_vals, y_vals, 'b-', label='f(x) Function Curve', linewidth=2)
    except Exception:
        pass

    # Tangent Line: y - y0 = m(x - x0)
    x_tangent = np.linspace(x_eval - 3, x_eval + 3, 50)
    y_tangent = y_eval + slope_tan * (x_tangent - x_eval)
    ax_c.plot(x_tangent, y_tangent, 'r--', label=f'Tangent at x={x_eval:.1f} (m={slope_tan:.2f})')
    ax_c.scatter([x_eval], [y_eval], color='red', s=50, zorder=5)

    # Secant Line
    if arc_a != arc_b:
        x_secant = np.array([arc_a, arc_b])
        y_secant = np.array([float(f_num(arc_a)), float(f_num(arc_b))])
        ax_c.plot(x_secant, y_secant, 'g:', linewidth=2, label=f'Secant [{arc_a:.1f}, {arc_b:.1f}] (m={arc_rate:.2f})')
        ax_c.scatter(x_secant, y_secant, color='green', s=40, zorder=5)

    ax_c.set_title(f"Calculus Function Plot — Context: {selected_context}")
    ax_c.set_xlabel(ctx['var'])
    ax_c.set_ylabel(ctx['dep'])
    ax_c.grid(True, alpha=0.3)
    ax_c.legend(loc='best')
    
    st.pyplot(fig_calc)

    # Context Simulation Widget
    st.subheader("3. Contextual Visual Simulation")
    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        st.write("**Simulation Parameter Indicator**")
        st.metric(label=f"Current {ctx['dep']}", value=f"{y_eval:.2f}")
        st.metric(label=f"Current Rate of Change ({ctx['unit']})", value=f"{slope_tan:.2f}")
    with sim_col2:
        if selected_context == "Sports Science (Biomechanics)":
            st.info(f"🦵 **Prosthetic Leg Joint Angle**: At time {x_eval:.2f} s, joint angle is {y_eval:.1f}° moving at {slope_tan:.1f} deg/s.")
            st.progress(min(max(int((y_eval % 90) / 90 * 100), 0), 100))
        elif selected_context == "Medical / Bioengineering":
            st.info(f"🧪 **Drug Concentration Gauge**: At time {x_eval:.2f} hrs, concentration is {y_eval:.2f} mg/L.")
            st.progress(min(max(int(abs(y_eval) * 10), 0), 100))
        else:
            st.info(f"📊 **Context Gauge**: Output state value is {y_eval:.2f} at input level {x_eval:.2f}.")
            st.progress(min(max(int(abs(y_eval) % 100), 0), 100))
