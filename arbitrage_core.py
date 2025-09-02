import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.replace({'NULL': np.nan, 'null': np.nan, 'NaN': np.nan})
    return df

def load_data():
    products = _load_csv(os.path.join(DATA_DIR, "products_prices_sample.csv"))
    services = _load_csv(os.path.join(DATA_DIR, "services_rates_sample.csv"))
    realestate = _load_csv(os.path.join(DATA_DIR, "real_estate_sample.csv"))
    fx = _load_csv(os.path.join(DATA_DIR, "fx_rates_sample.csv"))
    return {'products': products, 'services': services, 'realestate': realestate, 'fx': fx}

def fx_to_usd(amount: float, currency: str, fx: pd.DataFrame) -> float:
    row = fx.loc[fx['currency'].str.upper() == currency.upper()]
    if row.empty:
        raise ValueError(f"Missing FX rate for {currency}")
    rate = float(row.iloc[0]['usd_per_unit'])
    return float(amount) * rate

def summarize_products(query: str, shipping_pct: float, vat_pct: float, top_n: int = 10):
    data = load_data()
    df = data['products'].copy()
    fx = data['fx']

    mask = df['item_name'].str.contains(query, case=False, regex=False) | df['brand'].str.contains(query, case=False, regex=False)
    df = df.loc[mask].copy()
    if df.empty:
        return {'by_country': pd.DataFrame(), 'pairs': pd.DataFrame(), 'summary': f'No product rows matching "{query}".'}

    df['price_usd'] = df.apply(lambda r: fx_to_usd(r['price_local'], r['currency'], fx), axis=1)

    grp = df.groupby(['country', 'currency'], as_index=False).agg(
        median_price_usd=('price_usd', 'median'),
        n_listings=('price_usd', 'size')
    ).sort_values('median_price_usd')

    if len(grp) < 2:
        pairs = pd.DataFrame()
    else:
        cheapest = grp.iloc[0]
        richest = grp.iloc[-1]

        def apply_costs(price_usd: float, ship_pct: float, vat_pct: float, direction: str) -> float:
            if direction == 'buy':
                return price_usd * (1 + ship_pct/100.0)
            else:
                return price_usd * (1 - vat_pct/100.0)

        buy_cost = apply_costs(float(cheapest['median_price_usd']), shipping_pct, vat_pct, 'buy')
        sell_net = apply_costs(float(richest['median_price_usd']), shipping_pct, vat_pct, 'sell')
        gross_delta_pct = (richest['median_price_usd'] / cheapest['median_price_usd'] - 1) * 100.0
        est_net_margin_pct = (sell_net / buy_cost - 1) * 100.0

        pairs = pd.DataFrame([{
            'buy_in': cheapest['country'],
            'buy_median_price_usd': round(cheapest['median_price_usd'], 2),
            'sell_in': richest['country'],
            'sell_median_price_usd': round(richest['median_price_usd'], 2),
            'gross_gap_%': round(gross_delta_pct, 2),
            'assumed_shipping_%': shipping_pct,
            'assumed_vat_%': vat_pct,
            'est_net_margin_%': round(est_net_margin_pct, 2),
        }])

    if not grp.empty:
        best = grp.iloc[0]
        worst = grp.iloc[-1]
        summary = (f"Cheapest median in {best['country']} ~ ${best['median_price_usd']:.0f} vs "
                   f"highest in {worst['country']} ~ ${worst['median_price_usd']:.0f}. "
                   f"Gross gap ≈ {(worst['median_price_usd']/best['median_price_usd'] - 1)*100:.1f}%.")
    else:
        summary = "No matching countries."

    return {'by_country': grp.head(top_n), 'pairs': pairs, 'summary': summary}

def summarize_services(query: str, top_n: int = 10):
    data = load_data()
    df = data['services'].copy()
    fx = data['fx']

    mask = df['service_name'].str.contains(query, case=False, regex=False)
    df = df.loc[mask].copy()
    if df.empty:
        return {'by_country': pd.DataFrame(), 'summary': f'No service rows matching "{query}".'}

    df['rate_usd_per_hour'] = df.apply(lambda r: fx_to_usd(r['rate_local_per_hour'], r['currency'], fx), axis=1)
    grp = df.groupby(['country', 'seniority'], as_index=False).agg(
        median_rate_usd=('rate_usd_per_hour', 'median'),
        n_quotes=('rate_usd_per_hour', 'size')
    ).sort_values('median_rate_usd')

    best = grp.iloc[0]
    worst = grp.iloc[-1]
    summary = (f"Lowest median in {best['country']} ({best['seniority']}) ~ ${best['median_rate_usd']:.0f}/h vs "
               f"highest in {worst['country']} ({worst['seniority']}) ~ ${worst['median_rate_usd']:.0f}/h. "
               f"Gap ≈ {(worst['median_rate_usd']/best['median_rate_usd'] - 1)*100:.1f}%.")

    return {'by_country': grp.head(top_n), 'summary': summary}

def summarize_realestate(top_n: int = 10):
    data = load_data()
    df = data['realestate'].copy()
    fx = data['fx']

    df['price_usd_sqm'] = df.apply(lambda r: fx_to_usd(r['price_per_sqm_local'], r['currency'], fx), axis=1)
    df['rent_usd_sqm_m'] = df.apply(lambda r: fx_to_usd(r['rent_per_sqm_local_per_month'], r['currency'], fx), axis=1)
    df['gross_yield_%'] = (df['rent_usd_sqm_m'] * 12) / df['price_usd_sqm'] * 100.0

    top = df.sort_values('gross_yield_%', ascending=False).head(top_n)
    worst = df.sort_values('gross_yield_%', ascending=True).head(top_n)

    if not df.empty:
        s1 = top.iloc[0]
        s2 = worst.iloc[0]
        summary = (f"Best gross yield: {s1['city']} ({s1['country']}) ~ {s1['gross_yield_%']:.1f}% "
                   f"vs lowest: {s2['city']} ({s2['country']}) ~ {s2['gross_yield_%']:.1f}%.")
    else:
        summary = "No real estate rows."

    return {'top_yields': top, 'worst_yields': worst, 'summary': summary}

def export_html_report(title, sections, out_path, extras=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    html_parts = [f"<h1>{title}</h1>"]
    if extras and 'summary' in extras:
        html_parts.append(f"<p><b>Summary:</b> {extras['summary']}</p>")
    for name, df in sections.items():
        html_parts.append(f"<h2>{name}</h2>")
        html_parts.append(df.to_html(index=False))
    html = "\n".join(html_parts)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
