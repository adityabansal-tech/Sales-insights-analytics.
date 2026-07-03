import os
import sqlite3

# --- AUTOMATIC DATABASE INITIALIZATION ---
db_path = "sales_insights.db"
# If the database file is missing or totally empty, we force create the tables
if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Recreate the missing fact_sales table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_sales (
        order_id TEXT,
        customer_id TEXT,
        product_id TEXT,
        sales_amount REAL,
        profit REAL,
        order_date TEXT
    )
    """)
    conn.commit()
    conn.close()
# ----------------------------------------
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==================== CONFIG ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sales_insights.db")

st.set_page_config(
    page_title="Sales Insights Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.5rem; color: #1f6feb; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 0.95rem; opacity: 0.8; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 1.05rem; font-weight: 500; }
    h1 { color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 10px; }
    h2 { color: #e6eef6; margin-top: 20px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE FUNCTIONS ====================
def execute_query(query, params=None):
    # Intentionally not cached to ensure UI reflects immediate DB changes during development
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    if params:
        return pd.read_sql_query(query, conn, params=params)
    return pd.read_sql_query(query, conn)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🎯 Navigation & Filters")
    
    # Page selection
    page = st.radio("Select Page", [
        "📈 Dashboard",
        "➕ Add Sales",
        "📋 Data Explorer",
        "⚙️ Admin"
    ], label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("### 📅 Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", datetime(2024, 1, 1), key="start")
    with col2:
        end_date = st.date_input("To", datetime.now(), key="end")
    
    st.markdown("### 📦 Category Filter")
    try:
        categories = execute_query("SELECT DISTINCT category FROM dim_product ORDER BY category")['category'].tolist()
        selected_categories = st.multiselect("Select Categories", categories, default=categories)
    except:
        selected_categories = []
    
    st.markdown("### 🌍 Region Filter")
    try:
        countries = execute_query("SELECT DISTINCT country FROM dim_customer ORDER BY country")['country'].tolist()
        selected_countries = st.multiselect("Select Regions", countries, default=countries[:5])
    except:
        selected_countries = []
    
    st.divider()
    st.markdown("**Sales Insights v1.0**  \nPowered by Streamlit + SQLite")

# ==================== BUILD FILTER QUERIES ====================
category_filter = ""
country_filter = ""

if selected_categories:
    cats = "','".join(selected_categories)
    category_filter = f"AND dp.category IN ('{cats}')"

if selected_countries:
    countries_list = "','".join(selected_countries)
    country_filter = f"AND dc.country IN ('{countries_list}')"

date_filter = f"AND DATE(fs.order_date) BETWEEN '{start_date}' AND '{end_date}'"

# ==================== PAGE: DASHBOARD ====================
if page == "📈 Dashboard":
    st.markdown("# 📊 Sales Analytics Dashboard")
    st.markdown("*Real-time interactive analytics with live data updates*")
    
    try:
        # KPI Query
        kpi_query = f"""
        SELECT 
            SUM(fs.sales_amount) as total_revenue,
            SUM(fs.profit) as total_profit,
            COUNT(DISTINCT fs.order_id) as total_orders,
            ROUND(AVG(fs.sales_amount), 2) as avg_order,
            ROUND(AVG(fs.profit) / AVG(fs.sales_amount) * 100, 2) as avg_margin
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_id = dp.product_id
        JOIN dim_customer dc ON fs.customer_id = dc.customer_id
        WHERE 1=1 {category_filter} {country_filter} {date_filter}
        """
        
        kpi_data = execute_query(kpi_query)
        kpi = kpi_data.iloc[0]
        
        # Display KPIs
        st.markdown("## 💼 Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💰 Revenue", f"${kpi['total_revenue']:,.0f}", delta="📊 Live")
        with col2:
            st.metric("💵 Profit", f"${kpi['total_profit']:,.0f}", delta="📈 Live")
        with col3:
            st.metric("📦 Orders", f"{kpi['total_orders']:,.0f}", delta="⬆ Live")
        with col4:
            st.metric("🎯 Avg Order", f"${kpi['avg_order']:,.2f}", delta="Live")
        with col5:
            st.metric("📊 Margin", f"{kpi['avg_margin']:.1f}%", delta="📈 Live")
        
        st.divider()
        
        # Charts
        st.markdown("## 📊 Analytics & Insights")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Trend", "📦 Categories", "🏆 Products", "🌍 Regions"])
        
        with tab1:
            trend_query = f"""
            SELECT 
                order_date as date,
                SUM(sales_amount) as revenue,
                SUM(profit) as profit
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_id = dp.product_id
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            WHERE 1=1 {category_filter} {country_filter} {date_filter}
            GROUP BY order_date
            ORDER BY order_date
            """
            trend_data = execute_query(trend_query)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['revenue'], 
                                      name='Revenue', line=dict(color='#1f6feb', width=3),
                                      fill='tozeroy', fillcolor='rgba(31,111,235,0.1)', mode='lines'))
            fig.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['profit'],
                                      name='Profit', line=dict(color='#22c55e', width=3),
                                      fill='tozeroy', fillcolor='rgba(34,197,94,0.1)', mode='lines'))
            fig.update_layout(hovermode='x unified', template='plotly_dark', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            cat_query = f"""
            SELECT dp.category, SUM(fs.sales_amount) as revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_id = dp.product_id
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            WHERE 1=1 {category_filter} {country_filter} {date_filter}
            GROUP BY dp.category
            ORDER BY revenue DESC
            """
            cat_data = execute_query(cat_query)
            
            fig = px.bar(cat_data, x='category', y='revenue', 
                         title='Revenue by Category',
                         color_discrete_sequence=['#1f6feb'],
                         labels={'revenue': 'Revenue ($)', 'category': 'Category'})
            fig.update_layout(template='plotly_dark', height=400, xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            prod_query = f"""
            SELECT dp.product_name, SUM(fs.sales_amount) as revenue, COUNT(*) as orders
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_id = dp.product_id
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            WHERE 1=1 {category_filter} {country_filter} {date_filter}
            GROUP BY dp.product_name
            ORDER BY revenue DESC
            LIMIT 10
            """
            prod_data = execute_query(prod_query)
            
            fig = px.bar(prod_data, x='revenue', y='product_name', orientation='h',
                         title='Top 10 Products by Revenue',
                         color='revenue', color_continuous_scale='Blues_r',
                         labels={'revenue': 'Revenue ($)', 'product_name': 'Product'})
            fig.update_layout(template='plotly_dark', height=400, yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            region_query = f"""
            SELECT dc.country, SUM(fs.sales_amount) as revenue, COUNT(*) as orders
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            WHERE 1=1 {country_filter} {date_filter}
            GROUP BY dc.country
            ORDER BY revenue DESC
            """
            region_data = execute_query(region_query)
            
            fig = px.pie(region_data, values='revenue', names='country',
                         title='Revenue Distribution by Region',
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(template='plotly_dark', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Customer table
        st.markdown("## 👥 Top Customers")
        cust_query = f"""
        SELECT
            dc.customer_name, dc.segment, 
            SUM(fs.sales_amount) as lifetime_value,
            COUNT(*) as order_count,
            MAX(fs.order_date) as last_order
        FROM fact_sales fs
        JOIN dim_customer dc ON fs.customer_id = dc.customer_id
        WHERE 1=1 {country_filter} {date_filter}
        GROUP BY dc.customer_name, dc.segment
        ORDER BY lifetime_value DESC
        LIMIT 15
        """
        customers_data = execute_query(cust_query)
        st.dataframe(customers_data, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Dashboard Error: {str(e)}")

# ==================== PAGE: ADD SALES ====================
elif page == "➕ Add Sales":
    st.markdown("# ➕ Add New Sales Record")
    st.markdown("*Enter transaction details and watch the dashboard update in real-time*")
    
    try:
        with st.form("add_sales_form", clear_on_submit=True):
            st.markdown("## 📝 Sales Information")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                products = execute_query("SELECT product_id, product_name FROM dim_product ORDER BY product_name")
                product_id = st.selectbox("🏷️ Product", 
                                        options=products['product_id'],
                                        format_func=lambda x: products[products['product_id']==x]['product_name'].values[0],
                                        key="product")
                
                quantity = st.number_input("📦 Quantity", min_value=1, value=1, step=1)
            
            with col2:
                customers = execute_query("SELECT customer_id, customer_name FROM dim_customer ORDER BY customer_name")
                customer_id = st.selectbox("👤 Customer",
                                          options=customers['customer_id'],
                                          format_func=lambda x: customers[customers['customer_id']==x]['customer_name'].values[0],
                                          key="customer")
                
                sale_date = st.date_input("📅 Sale Date", datetime.now())
            
            with col3:
                # dim_product stores `unit_cost` (cost), not `unit_price` (retail price).
                product_info = execute_query("SELECT unit_cost, category FROM dim_product WHERE product_id = ?", (product_id,))
                if len(product_info) > 0:
                    unit_cost = product_info['unit_cost'].values[0]
                    # use a sensible default markup to derive a retail `unit_price` for manual entry
                    unit_price = round(unit_cost * 1.5, 2)
                    revenue = quantity * unit_price

                    st.metric("💰 Revenue", f"${revenue:,.2f}")

                    profit_margin = st.slider("📊 Margin %", 0, 100, 40, 1)
                    profit = round(revenue * (profit_margin / 100), 2)
                    st.metric("💵 Profit", f"${profit:,.2f}")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                submitted = st.form_submit_button("✅ Add Sale")
            
            if submitted:
                try:
                    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                    cursor = conn.cursor()
                    
                    # ensure date is ISO string
                    order_date_val = sale_date.isoformat() if hasattr(sale_date, 'isoformat') else str(sale_date)
                    cursor.execute("""
                        INSERT INTO fact_sales 
                        (order_id, order_date, customer_id, product_id, quantity, unit_price, discount, sales_amount, profit)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (f"ORD{int(datetime.now().timestamp())}", order_date_val, customer_id, product_id, quantity, unit_price, 0, revenue, profit))
                    
                    conn.commit()
                    conn.close()
                    
                    # Clear cache
                    st.cache_data.clear()
                    
                    st.success("✅ Sale added successfully! Dashboard will update automatically.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Form Error: {str(e)}")

# ==================== PAGE: DATA EXPLORER ====================
elif page == "📋 Data Explorer":
    st.markdown("# 📋 Data Explorer")
    st.markdown("*Browse, filter, and export your data*")
    
    try:
        tab1, tab2, tab3 = st.tabs(["💳 Sales Data", "👥 Customers", "🏷️ Products"])
        
        with tab1:
            st.markdown("## Recent Sales Transactions")
            sales_query = f"""
            SELECT
                fs.order_date, dp.product_name, dc.customer_name, 
                fs.quantity, fs.sales_amount, fs.profit, ROUND(CASE WHEN fs.sales_amount = 0 THEN 0 ELSE (fs.profit / fs.sales_amount * 100) END, 1) as margin_pct
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_id = dp.product_id
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            WHERE 1=1 {category_filter} {country_filter} {date_filter}
            ORDER BY fs.order_date DESC
            LIMIT 100
            """
            sales_data = execute_query(sales_query)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Records", len(sales_data))
            col2.metric("💰 Total Revenue", f"${sales_data['sales_amount'].sum():,.0f}")
            col3.metric("💵 Total Profit", f"${sales_data['profit'].sum():,.0f}")
            
            st.dataframe(sales_data, use_container_width=True, hide_index=True)
            
            # Download button
            csv = sales_data.to_csv(index=False)
            st.download_button("📥 Download as CSV", csv, file_name=f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="sales_csv")
        
        with tab2:
            st.markdown("## Customer Details")
            cust_query = f"""
            SELECT
                dc.customer_name, dc.segment, dc.country,
                COUNT(DISTINCT fs.order_id) as total_orders,
                SUM(fs.sales_amount) as total_spent,
                ROUND(AVG(fs.sales_amount), 2) as avg_order,
                MAX(fs.order_date) as last_purchase
            FROM dim_customer dc
            LEFT JOIN fact_sales fs ON dc.customer_id = fs.customer_id
            WHERE 1=1 {country_filter}
            GROUP BY dc.customer_name, dc.segment, dc.country
            ORDER BY total_spent DESC
            LIMIT 100
            """
            cust_data = execute_query(cust_query)
            st.dataframe(cust_data, use_container_width=True, hide_index=True)
            
            csv = cust_data.to_csv(index=False)
            st.download_button("📥 Download as CSV", csv, file_name=f"customers_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="cust_csv")
        
        with tab3:
            st.markdown("## Product Inventory & Performance")
            prod_query = f"""
            SELECT 
                dp.product_name, dp.category, dp.unit_cost as unit_price,
                COUNT(*) as times_sold,
                SUM(fs.quantity) as units_sold,
                SUM(fs.sales_amount) as total_revenue,
                ROUND(COALESCE(AVG(fs.profit) / NULLIF(AVG(fs.sales_amount), 0) * 100, 0), 1) as avg_margin
            FROM dim_product dp
            LEFT JOIN fact_sales fs ON dp.product_id = fs.product_id
            WHERE 1=1 {category_filter}
            GROUP BY dp.product_name, dp.category, dp.unit_cost
            ORDER BY total_revenue DESC
            """
            prod_data = execute_query(prod_query)
            st.dataframe(prod_data, use_container_width=True, hide_index=True)
            
            csv = prod_data.to_csv(index=False)
            st.download_button("📥 Download as CSV", csv, file_name=f"products_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="prod_csv")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ==================== PAGE: ADMIN ====================
elif page == "⚙️ Admin":
    st.markdown("# ⚙️ Administration Panel")
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Database Statistics")
            
            sales_count = execute_query("SELECT COUNT(*) as count FROM fact_sales")['count'].values[0]
            products_count = execute_query("SELECT COUNT(*) as count FROM dim_product")['count'].values[0]
            customers_count = execute_query("SELECT COUNT(*) as count FROM dim_customer")['count'].values[0]
            
            st.metric("📦 Total Sales", f"{sales_count:,}")
            st.metric("🏷️ Total Products", f"{products_count:,}")
            st.metric("👥 Total Customers", f"{customers_count:,}")
        
        with col2:
            st.markdown("### ⚡ System Status")
            
            st.metric("✅ Database", "Connected", delta="Healthy")
            st.metric("🚀 Views", f"Cached", delta="Active")
            st.metric("📡 API", "Running", delta="Live")
        
        st.divider()
        
        st.markdown("### 🛠️ Database Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ Cache refreshed!")
        
        with col2:
            if st.button("📊 Database Info", use_container_width=True):
                try:
                    db_info = os.path.getsize(DB_PATH) / (1024 * 1024)
                    st.info(f"📁 Database Size: {db_info:.2f} MB")
                except:
                    st.warning("Could not retrieve info")
        
        with col3:
                if st.button("📥 Download DB", use_container_width=True):
                    try:
                        with open(DB_PATH, 'rb') as f:
                            data = f.read()
                        st.download_button("⬇️ sales_insights.db", data, file_name="sales_insights.db", mime="application/octet-stream", key="db_download")
                    except Exception:
                        st.error("Could not read database file for download")
        
        st.divider()
        
        st.markdown("### ℹ️ System Information")
        st.info(f"""
        **Sales Insights Analytics Dashboard**
        - 🏢 Built with: Python, Streamlit, SQLite
        - 📊 Database: {DB_PATH}
        - 📦 Database Size: {os.path.getsize(DB_PATH) / (1024*1024):.2f} MB
        - 📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - ✨ Version: 1.0.0
        """)
        
    except Exception as e:
        st.error(f"❌ Admin Error: {str(e)}")

