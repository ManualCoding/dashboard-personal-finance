
# app.py
# Dashboard Interactivo de Finanzas Personales
# Requisitos:
#   pip install streamlit pandas plotly numpy
# Ejecutar:
#   streamlit run app.py

import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "Dashboard de Finanzas Personales"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
INVESTMENTS_FILE = DATA_DIR / "investments.csv"
BUDGET_FILE = DATA_DIR / "budget_config.json"

NEEDS_CATEGORIES = [
    "Renta/Hipoteca", "Servicios", "Supermercado", "Transporte", "Salud", "Seguros", "Deuda mínima"
]
WANTS_CATEGORIES = [
    "Restaurantes", "Entretenimiento", "Compras", "Viajes", "Suscripciones", "Hobbies", "Otros gustos"
]
SAVINGS_CATEGORIES = [
    "Ahorro", "Inversión", "Pago extra deuda", "Fondo emergencia"
]
INCOME_CATEGORIES = ["Salario", "Freelance", "Negocio", "Dividendos", "Intereses", "Otros ingresos"]
ALL_EXPENSE_CATEGORIES = NEEDS_CATEGORIES + WANTS_CATEGORIES + SAVINGS_CATEGORIES + ["Otros gastos"]
ALL_CATEGORIES = INCOME_CATEGORIES + ALL_EXPENSE_CATEGORIES

DEFAULT_BUDGET = {
    "currency": "$",
    "monthly_income_target": 3500.0,
    "emergency_fund_target_months": 6,
    "rule_needs": 50,
    "rule_wants": 30,
    "rule_savings": 20,
}

st.set_page_config(page_title=APP_TITLE, page_icon="💸", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 18px;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    }
    .section-card {
        padding: 1rem 1.2rem;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    }
    .small-muted {color: #64748b; font-size: 0.92rem;}
    .good {color:#16a34a; font-weight:700;}
    .warn {color:#ea580c; font-weight:700;}
    .bad {color:#dc2626; font-weight:700;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def load_budget() -> dict:
    if BUDGET_FILE.exists():
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_BUDGET, **data}
    return DEFAULT_BUDGET.copy()


def save_budget(config: dict) -> None:
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def seed_transactions() -> pd.DataFrame:
    today = pd.Timestamp.today().normalize()
    dates = pd.date_range(today - pd.DateOffset(months=5), today, freq="7D")
    rows = []
    rng = np.random.default_rng(42)
    for d in dates:
        # income monthly-ish
        if d.day <= 7:
            rows.append([d.date(), "Income", "Salario", "Ingreso principal", 3500.0, False, "Banco"])
        # fixed expenses
        if d.day <= 14:
            rows.extend([
                [d.date(), "Expense", "Renta/Hipoteca", "Vivienda", 1200.0, True, "Banco"],
                [d.date(), "Expense", "Servicios", "Luz/agua/internet", 220.0, True, "Tarjeta"],
                [d.date(), "Expense", "Seguros", "Seguro auto/salud", 180.0, True, "Banco"],
            ])
        # variable expenses
        rows.extend([
            [d.date(), "Expense", "Supermercado", "Compra semanal", float(rng.integers(80, 180)), False, "Tarjeta"],
            [d.date(), "Expense", "Restaurantes", "Comidas fuera", float(rng.integers(25, 110)), False, "Tarjeta"],
            [d.date(), "Expense", "Transporte", "Gasolina/Uber", float(rng.integers(30, 95)), False, "Tarjeta"],
            [d.date(), "Expense", "Entretenimiento", "Ocio", float(rng.integers(15, 100)), False, "Tarjeta"],
            [d.date(), "Expense", "Inversión", "Aporte broker", float(rng.integers(150, 350)), False, "Broker"],
        ])
    df = pd.DataFrame(rows, columns=["date", "type", "category", "description", "amount", "is_fixed", "account"])
    return df


def load_transactions() -> pd.DataFrame:
    if TRANSACTIONS_FILE.exists():
        df = pd.read_csv(TRANSACTIONS_FILE)
    else:
        df = seed_transactions()
        df.to_csv(TRANSACTIONS_FILE, index=False)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["is_fixed"] = df["is_fixed"].astype(bool)
    return df


def save_transactions(df: pd.DataFrame) -> None:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out.to_csv(TRANSACTIONS_FILE, index=False)


def seed_investments() -> pd.DataFrame:
    return pd.DataFrame([
        [date.today().replace(day=1), "ETF Total Market", "ETF", 7500, 6800, 0.07],
        [date.today().replace(day=1), "Bonos", "Bond", 2600, 2500, 0.035],
        [date.today().replace(day=1), "Fondo Emergencia", "Cash", 9000, 9000, 0.015],
        [date.today().replace(day=1), "Cripto", "Crypto", 900, 1200, 0.0],
    ], columns=["date", "asset", "asset_class", "current_value", "cost_basis", "expected_return"])


def load_investments() -> pd.DataFrame:
    if INVESTMENTS_FILE.exists():
        df = pd.read_csv(INVESTMENTS_FILE)
    else:
        df = seed_investments()
        df.to_csv(INVESTMENTS_FILE, index=False)
    df["date"] = pd.to_datetime(df["date"])
    for col in ["current_value", "cost_basis", "expected_return"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def save_investments(df: pd.DataFrame) -> None:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out.to_csv(INVESTMENTS_FILE, index=False)


def money(value: float, currency: str = "$") -> str:
    return f"{currency}{value:,.2f}"


def classify_rule(category: str) -> str:
    if category in NEEDS_CATEGORIES:
        return "Necesidades 50%"
    if category in WANTS_CATEGORIES:
        return "Deseos 30%"
    if category in SAVINGS_CATEGORIES:
        return "Ahorro/Inversión 20%"
    return "Sin clasificar"


def month_start_end(df: pd.DataFrame):
    if df.empty:
        current = pd.Timestamp.today()
        return current - pd.DateOffset(months=5), current
    return df["date"].min(), df["date"].max()


def apply_filters(df: pd.DataFrame, start_date, end_date, accounts, categories):
    mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    if accounts:
        mask &= df["account"].isin(accounts)
    if categories:
        mask &= df["category"].isin(categories)
    return df.loc[mask].copy()


def calculate_metrics(df: pd.DataFrame, investments: pd.DataFrame, config: dict):
    income = df.loc[df["type"] == "Income", "amount"].sum()
    expenses = df.loc[df["type"] == "Expense", "amount"].sum()
    fixed = df.loc[(df["type"] == "Expense") & (df["is_fixed"]), "amount"].sum()
    variable = expenses - fixed
    net_cashflow = income - expenses
    savings_amount = df.loc[(df["type"] == "Expense") & (df["category"].isin(SAVINGS_CATEGORIES)), "amount"].sum()
    savings_rate = (savings_amount / income * 100) if income else 0
    expense_ratio = (expenses / income * 100) if income else 0
    invested_value = investments["current_value"].sum() if not investments.empty else 0
    gain_loss = (investments["current_value"] - investments["cost_basis"]).sum() if not investments.empty else 0
    return {
        "income": income,
        "expenses": expenses,
        "fixed": fixed,
        "variable": variable,
        "net_cashflow": net_cashflow,
        "savings_amount": savings_amount,
        "savings_rate": savings_rate,
        "expense_ratio": expense_ratio,
        "invested_value": invested_value,
        "gain_loss": gain_loss,
    }


def render_header():
    st.title("💸 Dashboard Interactivo de Finanzas Personales")
    st.caption("Controla ingresos, gastos, gastos fijos, regla 50-30-20, inversiones y salud financiera en un solo lugar.")


def render_sidebar(config, df):
    st.sidebar.header("⚙️ Configuración")
    currency = st.sidebar.text_input("Símbolo de moneda", value=config["currency"], max_chars=5)
    monthly_income_target = st.sidebar.number_input("Ingreso mensual objetivo", min_value=0.0, value=float(config["monthly_income_target"]), step=100.0)
    emergency_months = st.sidebar.slider("Meta fondo de emergencia: meses", 1, 24, int(config["emergency_fund_target_months"]))

    st.sidebar.subheader("Regla 50-30-20")
    needs = st.sidebar.slider("Necesidades %", 0, 100, int(config["rule_needs"]))
    wants = st.sidebar.slider("Deseos %", 0, 100, int(config["rule_wants"]))
    savings = st.sidebar.slider("Ahorro/Inversión %", 0, 100, int(config["rule_savings"]))
    if needs + wants + savings != 100:
        st.sidebar.warning(f"La suma actual es {needs + wants + savings}%. Recomendado: 100%.")

    new_config = {
        "currency": currency,
        "monthly_income_target": monthly_income_target,
        "emergency_fund_target_months": emergency_months,
        "rule_needs": needs,
        "rule_wants": wants,
        "rule_savings": savings,
    }
    if st.sidebar.button("Guardar configuración"):
        save_budget(new_config)
        st.sidebar.success("Configuración guardada.")

    st.sidebar.divider()
    st.sidebar.header("🔎 Filtros")
    min_d, max_d = month_start_end(df)
    start_date = st.sidebar.date_input("Desde", value=min_d.date())
    end_date = st.sidebar.date_input("Hasta", value=max_d.date())
    accounts = st.sidebar.multiselect("Cuentas", sorted(df["account"].dropna().unique().tolist()))
    categories = st.sidebar.multiselect("Categorías", sorted(df["category"].dropna().unique().tolist()))
    return new_config, start_date, end_date, accounts, categories


def render_data_entry(df: pd.DataFrame, investments: pd.DataFrame):
    with st.expander("➕ Añadir transacción o inversión", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Transacción", "Inversión", "Importar CSV"])
        with tab1:
            with st.form("transaction_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                t_date = c1.date_input("Fecha", value=date.today())
                t_type = c2.selectbox("Tipo", ["Expense", "Income"])
                categories = ALL_EXPENSE_CATEGORIES if t_type == "Expense" else INCOME_CATEGORIES
                t_category = c3.selectbox("Categoría", categories)
                c4, c5, c6 = st.columns(3)
                t_amount = c4.number_input("Monto", min_value=0.0, step=10.0)
                t_fixed = c5.checkbox("Gasto fijo", value=t_category in ["Renta/Hipoteca", "Servicios", "Seguros"])
                t_account = c6.text_input("Cuenta", value="Banco")
                t_description = st.text_input("Descripción", value="")
                submitted = st.form_submit_button("Guardar transacción")
                if submitted and t_amount > 0:
                    new_row = pd.DataFrame([[pd.to_datetime(t_date), t_type, t_category, t_description, t_amount, t_fixed, t_account]], columns=df.columns)
                    df_new = pd.concat([df, new_row], ignore_index=True)
                    save_transactions(df_new)
                    st.success("Transacción guardada. Recarga automática en curso...")
                    st.rerun()
        with tab2:
            with st.form("investment_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                i_date = c1.date_input("Fecha valuación", value=date.today())
                i_asset = c2.text_input("Activo", value="ETF")
                i_class = c3.selectbox("Clase", ["ETF", "Stock", "Bond", "Cash", "Crypto", "Real Estate", "Other"])
                c4, c5, c6 = st.columns(3)
                i_value = c4.number_input("Valor actual", min_value=0.0, step=100.0)
                i_cost = c5.number_input("Costo base", min_value=0.0, step=100.0)
                i_return = c6.number_input("Retorno esperado anual", min_value=-1.0, max_value=1.0, value=0.05, step=0.005, format="%.3f")
                submitted_i = st.form_submit_button("Guardar inversión")
                if submitted_i and i_value >= 0:
                    new_inv = pd.DataFrame([[pd.to_datetime(i_date), i_asset, i_class, i_value, i_cost, i_return]], columns=investments.columns)
                    inv_new = pd.concat([investments, new_inv], ignore_index=True)
                    save_investments(inv_new)
                    st.success("Inversión guardada.")
                    st.rerun()
        with tab3:
            st.markdown("CSV de transacciones con columnas: `date,type,category,description,amount,is_fixed,account`.")
            uploaded = st.file_uploader("Importar transacciones CSV", type=["csv"])
            if uploaded is not None:
                imported = pd.read_csv(uploaded)
                expected = set(df.columns)
                if expected.issubset(imported.columns):
                    imported = imported[list(df.columns)]
                    imported["date"] = pd.to_datetime(imported["date"])
                    combined = pd.concat([df, imported], ignore_index=True)
                    save_transactions(combined)
                    st.success("CSV importado correctamente.")
                    st.rerun()
                else:
                    st.error(f"Columnas faltantes. Se esperan: {', '.join(df.columns)}")


def render_kpis(metrics, config):
    currency = config["currency"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", money(metrics["income"], currency))
    c2.metric("Gastos", money(metrics["expenses"], currency), delta=f"{metrics['expense_ratio']:.1f}% de ingresos", delta_color="inverse")
    c3.metric("Flujo neto", money(metrics["net_cashflow"], currency))
    c4.metric("Tasa ahorro/inversión", f"{metrics['savings_rate']:.1f}%", delta=money(metrics["savings_amount"], currency))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Gastos fijos", money(metrics["fixed"], currency))
    c6.metric("Gastos variables", money(metrics["variable"], currency))
    c7.metric("Portafolio", money(metrics["invested_value"], currency))
    c8.metric("Ganancia/Pérdida inversión", money(metrics["gain_loss"], currency))


def render_cashflow_charts(df, config):
    currency = config["currency"]
    if df.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return
    monthly = df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").dt.to_timestamp()
    monthly_sum = monthly.groupby(["month", "type"], as_index=False)["amount"].sum()
    pivot = monthly_sum.pivot(index="month", columns="type", values="amount").fillna(0).reset_index()
    if "Income" not in pivot: pivot["Income"] = 0
    if "Expense" not in pivot: pivot["Expense"] = 0
    pivot["Net"] = pivot["Income"] - pivot["Expense"]

    col1, col2 = st.columns([1.3, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pivot["month"], y=pivot["Income"], name="Ingresos"))
        fig.add_trace(go.Bar(x=pivot["month"], y=pivot["Expense"], name="Gastos"))
        fig.add_trace(go.Scatter(x=pivot["month"], y=pivot["Net"], name="Flujo neto", mode="lines+markers", yaxis="y2"))
        fig.update_layout(title="Ingresos vs Gastos por Mes", barmode="group", yaxis_title=f"Monto ({currency})", yaxis2=dict(overlaying="y", side="right", title="Flujo neto"), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        exp = df[df["type"] == "Expense"].groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        fig2 = px.pie(exp, names="category", values="amount", title="Distribución de gastos")
        st.plotly_chart(fig2, use_container_width=True)


def render_503020(df, metrics, config):
    currency = config["currency"]
    st.subheader("📐 Análisis Regla 50-30-20")
    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty or metrics["income"] <= 0:
        st.info("Añade ingresos y gastos para evaluar la regla 50-30-20.")
        return
    expenses["bucket"] = expenses["category"].apply(classify_rule)
    actual = expenses.groupby("bucket", as_index=False)["amount"].sum()
    targets = pd.DataFrame({
        "bucket": ["Necesidades 50%", "Deseos 30%", "Ahorro/Inversión 20%"],
        "target": [metrics["income"] * config["rule_needs"] / 100, metrics["income"] * config["rule_wants"] / 100, metrics["income"] * config["rule_savings"] / 100],
    })
    comp = targets.merge(actual, on="bucket", how="left").fillna(0)
    comp["difference"] = comp["target"] - comp["amount"]
    comp["actual_pct_income"] = comp["amount"] / metrics["income"] * 100

    col1, col2 = st.columns([1.2, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=comp["bucket"], y=comp["target"], name="Objetivo"))
        fig.add_trace(go.Bar(x=comp["bucket"], y=comp["amount"], name="Actual"))
        fig.update_layout(title="Objetivo vs Actual", barmode="group", yaxis_title=f"Monto ({currency})", legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        display = comp.copy()
        display["Objetivo"] = display["target"].apply(lambda x: money(x, currency))
        display["Actual"] = display["amount"].apply(lambda x: money(x, currency))
        display["Diferencia"] = display["difference"].apply(lambda x: money(x, currency))
        display["% ingreso"] = display["actual_pct_income"].map(lambda x: f"{x:.1f}%")
        st.dataframe(display[["bucket", "Objetivo", "Actual", "Diferencia", "% ingreso"]], hide_index=True, use_container_width=True)


def render_investments(investments, config):
    currency = config["currency"]
    st.subheader("📈 Inversiones")
    if investments.empty:
        st.info("Añade inversiones para visualizar tu portafolio.")
        return
    inv = investments.copy()
    inv["gain_loss"] = inv["current_value"] - inv["cost_basis"]
    inv["return_pct"] = np.where(inv["cost_basis"] > 0, inv["gain_loss"] / inv["cost_basis"] * 100, 0)
    inv["projected_10y"] = inv["current_value"] * ((1 + inv["expected_return"]) ** 10)

    col1, col2 = st.columns([1, 1])
    with col1:
        alloc = inv.groupby("asset_class", as_index=False)["current_value"].sum()
        fig = px.treemap(alloc, path=["asset_class"], values="current_value", title="Asignación por clase de activo")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        proj = inv.groupby("asset", as_index=False)["projected_10y"].sum().sort_values("projected_10y", ascending=False)
        fig2 = px.bar(proj, x="asset", y="projected_10y", title="Proyección simple a 10 años", labels={"projected_10y": f"Valor proyectado ({currency})", "asset": "Activo"})
        st.plotly_chart(fig2, use_container_width=True)

    show = inv[["asset", "asset_class", "current_value", "cost_basis", "gain_loss", "return_pct", "expected_return"]].copy()
    show.columns = ["Activo", "Clase", "Valor actual", "Costo base", "Gan/Pérd", "Retorno %", "Retorno esperado"]
    st.dataframe(show, hide_index=True, use_container_width=True)


def render_financial_health(df, metrics, config):
    st.subheader("🩺 Salud financiera")
    currency = config["currency"]
    monthly_expense = df[df["type"] == "Expense"].copy()
    if monthly_expense.empty:
        st.info("Necesitas gastos para calcular salud financiera.")
        return
    # Monthly average over filtered months
    months = max(1, monthly_expense["date"].dt.to_period("M").nunique())
    avg_monthly_expense = monthly_expense["amount"].sum() / months
    emergency_target = avg_monthly_expense * config["emergency_fund_target_months"]
    emergency_assets = 0.0
    # infer emergency savings from transactions only
    emergency_assets += df[(df["type"] == "Expense") & (df["category"] == "Fondo emergencia")]["amount"].sum()
    fixed_ratio = metrics["fixed"] / metrics["income"] * 100 if metrics["income"] else 0

    score = 0
    score += 25 if metrics["net_cashflow"] > 0 else 0
    score += 25 if metrics["savings_rate"] >= config["rule_savings"] else max(0, metrics["savings_rate"] / max(config["rule_savings"], 1) * 25)
    score += 25 if fixed_ratio <= 50 else max(0, 25 - (fixed_ratio - 50))
    score += 25 if emergency_assets >= emergency_target else (emergency_assets / emergency_target * 25 if emergency_target else 0)
    score = min(100, score)

    c1, c2, c3 = st.columns(3)
    c1.metric("Score salud financiera", f"{score:.0f}/100")
    c2.metric("Gasto mensual promedio", money(avg_monthly_expense, currency))
    c3.metric("Meta fondo emergencia", money(emergency_target, currency))

    recommendations = []
    if metrics["net_cashflow"] < 0:
        recommendations.append("Reduce gastos variables o aumenta ingresos: tu flujo neto está negativo.")
    if metrics["savings_rate"] < config["rule_savings"]:
        recommendations.append("Automatiza aportes a ahorro/inversión hasta acercarte al objetivo 20%.")
    if fixed_ratio > 50:
        recommendations.append("Tus gastos fijos están altos vs ingresos; renegocia renta, seguros o servicios.")
    if emergency_assets < emergency_target:
        recommendations.append("Prioriza el fondo de emergencia antes de asumir más riesgo de inversión.")
    if not recommendations:
        recommendations.append("Excelente: mantén la disciplina y revisa tu asignación de inversiones trimestralmente.")
    st.markdown("**Recomendaciones:**")
    for rec in recommendations:
        st.write(f"- {rec}")


def render_transactions_table(df):
    st.subheader("🧾 Transacciones")
    view = df.sort_values("date", ascending=False).copy()
    view["date"] = view["date"].dt.date
    st.dataframe(view, hide_index=True, use_container_width=True)
    csv = view.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar transacciones filtradas", data=csv, file_name="transacciones_filtradas.csv", mime="text/csv")


def main():
    render_header()
    config = load_budget()
    df = load_transactions()
    investments = load_investments()
    config, start_date, end_date, accounts, categories = render_sidebar(config, df)
    filtered = apply_filters(df, start_date, end_date, accounts, categories)

    render_data_entry(df, investments)
    metrics = calculate_metrics(filtered, investments, config)
    render_kpis(metrics, config)
    st.divider()

    tab_overview, tab_rule, tab_inv, tab_health, tab_data = st.tabs([
        "Resumen", "50-30-20", "Inversiones", "Salud financiera", "Datos"
    ])
    with tab_overview:
        render_cashflow_charts(filtered, config)
    with tab_rule:
        render_503020(filtered, metrics, config)
    with tab_inv:
        render_investments(investments, config)
    with tab_health:
        render_financial_health(filtered, metrics, config)
    with tab_data:
        render_transactions_table(filtered)

    st.caption("Nota: Este dashboard es educativo y no constituye asesoría financiera personalizada.")


if __name__ == "__main__":
    main()
