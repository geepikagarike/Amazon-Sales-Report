from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.sql_analytics import dashboard_summary, initialize_from_project_files


st.set_page_config(page_title="E-Commerce Analytics Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_dashboard_data():
    db_path = initialize_from_project_files()
    summary = dashboard_summary(db_path)
    summary["db_path"] = str(db_path)
    summary["last_refresh"] = datetime.fromtimestamp(db_path.stat().st_mtime)
    return summary


@st.cache_data(show_spinner=False)
def find_market_basket_files() -> list[str]:
    root = Path(__file__).resolve().parents[1]
    patterns = [
        "**/*apriori*",
        "**/*fp*growth*",
        "**/*market*basket*",
        "**/*association*rule*",
    ]
    matches: set[str] = set()
    for pattern in patterns:
        for file_path in root.glob(pattern):
            if file_path.is_file():
                matches.add(str(file_path.relative_to(root)))
    return sorted(matches)


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def show_exec_overview(data: dict) -> None:
    st.title("Executive Overview")
    db_path = Path(data["db_path"]).name
    st.caption(f"Data source: {db_path} | Last refreshed: {data['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")

    total_sales = float(data["total_sales"])
    order_count = int(data["distinct_order_count"])
    aov = float(data["average_order_value"])
    status_df = data["order_status"].copy() if isinstance(data["order_status"], pd.DataFrame) else pd.DataFrame()
    cancelled_amount = 0.0
    if not status_df.empty:
        cancelled_rows = status_df[status_df["status_group"] == "Cancelled"]
        if not cancelled_rows.empty:
            cancelled_amount = float(cancelled_rows["gross_amount"].sum())

    cols = st.columns(4)
    cols[0].metric("Total Sales", format_inr(total_sales))
    cols[1].metric("Distinct Orders", f"{order_count:,}")
    cols[2].metric("Average Order Value", format_inr(aov))
    cols[3].metric("Cancelled GMV", format_inr(cancelled_amount))

    monthly = data["monthly_sales"]
    if monthly.empty:
        st.warning("No monthly sales data available in the current dataset.")
    else:
        fig = px.line(monthly, x="month", y="total_sales", markers=True, title="Monthly Sales Trend")
        fig.update_layout(xaxis_title="Month", yaxis_title="Sales (INR)")
        st.plotly_chart(fig, use_container_width=True)

    category = data["category_performance"]
    if category.empty:
        st.warning("No category data was found for the cleaned dataset.")
    else:
        category_cols = st.columns(2)
        category_fig = px.bar(category, x="Category", y="total_sales", title="Category Performance")
        category_cols[0].plotly_chart(category_fig, use_container_width=True)

        top_products = data["top_products"]
        if top_products.empty:
            st.caption("No product sales analysis available.")
        else:
            top_fig = px.bar(top_products.head(10), x="Product_Name", y="total_sales", title="Top Products by Sales")
            top_fig.update_xaxes(tickangle=45)
            category_cols[1].plotly_chart(top_fig, use_container_width=True)


def show_product_analytics(data: dict) -> None:
    st.title("Product Analytics")
    product_df = data["top_products"]
    quantity_df = data["top_products_quantity"]

    st.subheader("Top product views")
    view = st.radio("Choose metric", ["Sales", "Quantity"], horizontal=True)

    if view == "Sales":
        chart_df = product_df
        y_col = "total_sales"
        title = "Top Products by Sales"
    else:
        chart_df = quantity_df
        y_col = "total_quantity"
        title = "Top Products by Quantity"

    if chart_df.empty:
        st.warning("No product-level data is available.")
        return

    search_term = st.text_input("Filter by product name", "")
    filtered = chart_df if not search_term else chart_df[chart_df["Product_Name"].str.contains(search_term, case=False, na=False)]
    if filtered.empty:
        st.info("No products match the current filter.")
        return

    fig = px.bar(filtered.head(10), x="Product_Name", y=y_col, title=title)
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    category = data["category_performance"]
    if not category.empty:
        st.subheader("Category comparison")
        category_fig = px.bar(category, x="Category", y="total_sales", title="Category Sales Comparison")
        st.plotly_chart(category_fig, use_container_width=True)


def show_order_operations(data: dict) -> None:
    st.title("Order Operations")

    status_df = data["order_status"]
    if status_df.empty:
        st.warning("Order-status data is unavailable in the current dataset.")
    else:
        status_fig = px.pie(status_df, names="status_group", values="order_lines", title="Order Status Distribution")
        st.plotly_chart(status_fig, use_container_width=True)

    cancellation_df = data["cancellation_analysis"]
    if cancellation_df.empty:
        st.info("Cancellation analysis is not available because only completed orders were provided in this dataset.")
    else:
        cancellation_fig = px.bar(cancellation_df, x="status_group", y="gross_market_value", title="Cancellation and Return Exposure")
        st.plotly_chart(cancellation_fig, use_container_width=True)

    geo_df = data["geographic_sales"]
    if geo_df.empty:
        st.warning("Geographic field data is not available in the current fact table.")
    else:
        geo_fig = px.bar(geo_df.head(12), x="state", y="total_sales", title="Geographic Sales by State")
        geo_fig.update_xaxes(tickangle=45)
        st.plotly_chart(geo_fig, use_container_width=True)


def show_market_basket_analysis() -> None:
    st.title("Market Basket Analysis")
    files = find_market_basket_files()
    if not files:
        st.info(
            "No Apriori or FP-Growth output files were found in the current project. "
            "That is expected until association-rule exports are generated."
        )
        st.write("Generate a rule CSV with support, confidence, lift, antecedents, and consequents columns and place it in the project data folder to enable this section.")
        return

    selected = st.selectbox("Available rule outputs", files)
    st.caption(f"Selected source: {selected}")
    file_path = Path(__file__).resolve().parents[1] / selected
    try:
        rule_df = pd.read_csv(file_path)
    except Exception as exc:  # pragma: no cover - UI failure path
        st.error(f"Could not load the selected rule file: {exc}")
        return

    if rule_df.empty:
        st.warning("The selected market basket file is present but empty.")
        return

    allowed = {"support", "confidence", "lift", "antecedents", "consequents"}
    cols = set(rule_df.columns.str.lower())
    if not allowed.intersection(cols):
        st.warning("The file was found, but it does not contain the expected association-rule columns. Expected support/confidence/lift and item columns.")
        return

    best = rule_df.sort_values(by=["confidence", "lift"], ascending=False).head(20)
    st.dataframe(best, use_container_width=True)


def main() -> None:
    data = load_dashboard_data()
    st.sidebar.title("Analytics Menu")
    sections = [
        "Executive Overview",
        "Product Analytics",
        "Order Operations",
        "Market Basket Analysis",
    ]
    section = st.sidebar.radio("Pages", sections)

    if section == "Executive Overview":
        show_exec_overview(data)
    elif section == "Product Analytics":
        show_product_analytics(data)
    elif section == "Order Operations":
        show_order_operations(data)
    else:
        show_market_basket_analysis()


if __name__ == "__main__":
    main()
