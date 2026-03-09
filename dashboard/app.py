import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Superstore Dashboard",
    page_icon="🛒",
    layout="wide"
)

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "superstore_db")
DB_USER     = os.getenv("DB_USER", "superstore_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "superstore_pass")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ─────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

@st.cache_data(ttl=300)
def load_data():
    engine = get_engine()
    query = """
        SELECT
            oi.item_id,
            o.order_id,
            o.order_date,
            o.ship_date,
            o.ship_mode,
            o.year,
            o.month,
            o.quarter,
            cu.customer_id,
            cu.customer_name,
            cu.segment,
            r.region,
            r.state,
            r.city,
            c.category,
            c.sub_category,
            p.product_name,
            oi.sales,
            oi.delivery_days
        FROM order_items oi
        JOIN orders o     ON oi.order_id    = o.order_id
        JOIN customers cu ON o.customer_id  = cu.customer_id
        JOIN regions r    ON o.region_id    = r.region_id
        JOIN products p   ON oi.product_id  = p.product_id
        JOIN categories c ON p.category_id  = c.category_id
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['month_year'] = df['order_date'].dt.to_period('M').astype(str)
    df['profit_ratio'] = (df['sales'] * 0.2).round(2)
    return df

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
try:
    df = load_data()
except Exception as e:
    st.error(f"Cannot connect to database: {e}")
    st.stop()

# ─────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/emoji/96/shopping-cart-emoji.png", width=80)
st.sidebar.title("🔍 Filters")

years = sorted(df['year'].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("📅 Year", years, default=years)

regions = sorted(df['region'].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("🌍 Region", regions, default=regions)

categories = sorted(df['category'].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("📦 Category", categories, default=categories)

segments = sorted(df['segment'].dropna().unique().tolist())
selected_segments = st.sidebar.multiselect("👤 Segment", segments, default=segments)

# Apply filters
mask = (
    df['year'].isin(selected_years) &
    df['region'].isin(selected_regions) &
    df['category'].isin(selected_categories) &
    df['segment'].isin(selected_segments)
)
filtered = df[mask]

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.title("🛒 Superstore Sales Dashboard")
st.markdown("Interactive dashboard connected to **PostgreSQL**")
st.markdown("---")

if filtered.empty:
    st.warning("⚠️ No data for selected filters.")
    st.stop()


# ─────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────
total_sales    = filtered['sales'].sum()
avg_sales      = filtered['sales'].mean()
median_sales   = filtered['sales'].median()
std_sales      = filtered['sales'].std()
total_orders   = filtered['order_id'].nunique()
total_customers = filtered['customer_id'].nunique()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("💰 Total Sales",      f"${total_sales:,.0f}")
col2.metric("📦 Total Orders",     f"{total_orders:,}")
col3.metric("👥 Customers",        f"{total_customers:,}")
col4.metric("📊 Avg Sale",         f"${avg_sales:,.2f}")
col5.metric("📈 Median Sale",      f"${median_sales:,.2f}")
col6.metric("📉 Std Dev",          f"${std_sales:,.2f}")

st.markdown("---")


# ─────────────────────────────────────────
# ROW 1 — Sales by Category & Region
# ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Sales by Category")
    cat_sales = filtered.groupby('category')['sales'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(cat_sales.index, cat_sales.values, color=['#4C72B0','#DD8452','#55A868'])
    ax.set_ylabel("Total Sales ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f'${bar.get_height():,.0f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("🌍 Sales by Region")
    reg_sales = filtered.groupby('region')['sales'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ['#4C72B0','#DD8452','#55A868','#C44E52']
    wedges, texts, autotexts = ax.pie(
        reg_sales.values,
        labels=reg_sales.index,
        autopct='%1.1f%%',
        colors=colors[:len(reg_sales)],
        startangle=140
    )
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ─────────────────────────────────────────
# ROW 2 — Monthly Sales Trend & Sub-Category
# ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Monthly Sales Trend")
    monthly = filtered.groupby('month_year')['sales'].sum().reset_index()
    monthly = monthly.sort_values('month_year')
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(monthly['month_year'], monthly['sales'], marker='o', color='#4C72B0', linewidth=2)
    ax.fill_between(monthly['month_year'], monthly['sales'], alpha=0.1, color='#4C72B0')
    ax.set_ylabel("Total Sales ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("🗂️ Sales by Sub-Category")
    sub_sales = (
        filtered.groupby('sub_category')['sales']
        .sum()
        .sort_values(ascending=True)
        .tail(10)
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(sub_sales.index, sub_sales.values, color='#4C72B0')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ─────────────────────────────────────────
# ROW 3 — Top 10 Customers & Segment
# ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 Customers by Revenue")
    top_customers = (
        filtered.groupby('customer_name')['sales']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.barh(top_customers.index[::-1], top_customers.values[::-1], color='#55A868')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("👤 Sales by Customer Segment")
    seg_sales = filtered.groupby('segment')['sales'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(seg_sales.index, seg_sales.values, color=['#4C72B0','#DD8452','#55A868'])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'${bar.get_height():,.0f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ─────────────────────────────────────────
# ROW 4 — Heatmap & Delivery Days
# ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Sales Heatmap — Region × Category")
    heatmap_data = filtered.pivot_table(
        values='sales', index='region',
        columns='category', aggfunc='sum'
    ).fillna(0)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='Blues',
                linewidths=0.5, ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("🚚 Avg Delivery Days by Ship Mode")
    delivery = filtered.groupby('ship_mode')['delivery_days'].mean().sort_values()
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(delivery.index, delivery.values, color='#C44E52')
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{bar.get_height():.1f}d', ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Avg Days")
    plt.xticks(rotation=15)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ─────────────────────────────────────────
# ROW 5 — Descriptive Statistics
# ─────────────────────────────────────────
st.markdown("---")
st.subheader("📐 Descriptive Statistics")

stats = filtered['sales'].describe().rename({
    'count': 'Count', 'mean': 'Mean', 'std': 'Std Dev',
    'min': 'Min', '25%': 'Q1', '50%': 'Median',
    '75%': 'Q3', 'max': 'Max'
})

s1, s2, s3, s4, s5, s6, s7, s8 = st.columns(8)
s1.metric("Count",   f"{stats['Count']:,.0f}")
s2.metric("Mean",    f"${stats['Mean']:,.2f}")
s3.metric("Std Dev", f"${stats['Std Dev']:,.2f}")
s4.metric("Min",     f"${stats['Min']:,.2f}")
s5.metric("Q1",      f"${stats['Q1']:,.2f}")
s6.metric("Median",  f"${stats['Median']:,.2f}")
s7.metric("Q3",      f"${stats['Q3']:,.2f}")
s8.metric("Max",     f"${stats['Max']:,.2f}")

# Sales Distribution
st.subheader("📊 Sales Distribution")
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].hist(filtered['sales'], bins=50, color='#4C72B0', edgecolor='white')
axes[0].set_title("Sales Distribution")
axes[0].set_xlabel("Sales ($)")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

sns.boxplot(x='category', y='sales', data=filtered, ax=axes[1], palette='Set2')
axes[1].set_title("Sales Boxplot by Category")
axes[1].set_xlabel("")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

plt.tight_layout()
st.pyplot(fig)
plt.close()

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.markdown("---")  
st.markdown(
    "<div style='text-align:center; color:gray;'>Superstore Dashboard | Connected to PostgreSQL superstore_db</div>",
    unsafe_allow_html=True
)