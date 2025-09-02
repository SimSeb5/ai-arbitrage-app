# app.py — AI Global Arbitrage Finder (deploy-ready, entrypoint at repo root)
import streamlit as st
from arbitrage_core import summarize_products, summarize_services, summarize_realestate, export_html_report

st.set_page_config(page_title="AI Global Arbitrage Finder — MVP", layout="wide")
st.title("🌍 AI Global Arbitrage Finder — MVP")

tab1, tab2, tab3 = st.tabs(["📦 Products", "🧰 Services", "🏠 Real Estate"])

with tab1:
    st.subheader("Product arbitrage")
    q = st.text_input("Search product or brand", value="iPhone 15 Pro 128GB")
    c1, c2, c3 = st.columns(3)
    with c1:
        shipping = st.number_input("Assume shipping/import costs (%)", value=5.0, step=0.5)
    with c2:
        vat = st.number_input("Assume VAT/resale fees on sell-side (%)", value=8.0, step=0.5)
    with c3:
        topn = st.number_input("Show top N countries", value=10, min_value=2, max_value=50, step=1)

    if st.button("Analyze Products", type="primary"):
        res = summarize_products(q, shipping, vat, int(topn))
        st.caption(res['summary'])
        st.dataframe(res['by_country'])
        if not res['pairs'].empty:
            st.markdown("**Suggested Buy/Sell Pair (naive):**")
            st.dataframe(res['pairs'])

        if st.button("Export HTML report"):
            path = export_html_report(
                title=f"Product Arbitrage — {q}",
                sections={"By Country": res['by_country'], "Buy/Sell Pair": res['pairs']},
                out_path="reports/product_report.html",
                extras={"summary": res['summary']}
            )
            st.success(f"Saved to {path}")

with tab2:
    st.subheader("Service rates arbitrage")
    q2 = st.text_input("Search service (e.g., 'Web development')", value="Web development")
    topn2 = st.number_input("Show top N", value=10, min_value=2, max_value=50, step=1, key="topn2")

    if st.button("Analyze Services", type="primary", key="btn2"):
        res2 = summarize_services(q2, int(topn2))
        st.caption(res2['summary'])
        st.dataframe(res2['by_country'])
        if st.button("Export HTML report", key="exp2"):
            path = export_html_report(
                title=f"Service Arbitrage — {q2}",
                sections={"By Country": res2['by_country']},
                out_path="reports/service_report.html",
                extras={"summary": res2['summary']}
            )
            st.success(f"Saved to {path}")

with tab3:
    st.subheader("Real estate yields")
    topn3 = st.number_input("Show top N yields", value=10, min_value=2, max_value=50, step=1, key="topn3")
    if st.button("Analyze Real Estate", type="primary", key="btn3"):
        res3 = summarize_realestate(int(topn3))
        st.caption(res3['summary'])
        st.markdown("**Top yields**")
        st.dataframe(res3['top_yields'])
        st.markdown("**Lowest yields**")
        st.dataframe(res3['worst_yields'])
        if st.button("Export HTML report", key="exp3"):
            path = export_html_report(
                title="Real Estate Yields",
                sections={"Top yields": res3['top_yields'], "Lowest yields": res3['worst_yields']},
                out_path="reports/real_estate_report.html",
                extras={"summary": res3['summary']}
            )
            st.success(f"Saved to {path}")
