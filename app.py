import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set up page configuration
st.set_page_config(page_title="Electronics Store Sales Dashboard (2019)", layout="wide")

cleaning_steps = {}

@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("Sales Data.csv")
    cleaning_steps['Original Dataset'] = len(df)
    
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
        
    df = df.dropna()
    cleaning_steps['After Dropping Missing Values'] = len(df)
    
    df = df[df['Quantity Ordered'] != 'Quantity Ordered']
    cleaning_steps['After Removing Text Header Rows'] = len(df)
    
    df['Quantity Ordered'] = pd.to_numeric(df['Quantity Ordered'])
    df['Price Each'] = pd.to_numeric(df['Price Each'])
    
    df = df.drop_duplicates()
    cleaning_steps['After Removing Duplicates'] = len(df)
    
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Sales'] = df['Quantity Ordered'] * df['Price Each']
    df['Month'] = df['Order Date'].dt.strftime('%B')
    df['Hour'] = df['Order Date'].dt.hour
    df['Day of Week'] = df['Order Date'].dt.strftime('%A')
    
    def get_city_state(address):
        try:
            parts = address.split(',')
            city = parts[1].strip()
            state = parts[2].strip().split(' ')[0]
            return f"{city} ({state})"
        except:
            return "Unknown"
            
    df['City'] = df['Purchase Address'].apply(get_city_state)
    df['State'] = df['Purchase Address'].apply(lambda x: x.split(',')[2].strip().split(' ')[0] if len(str(x).split(',')) > 2 else "Unknown")
    
    df = df[df['Order Date'].dt.year == 2019]
    cleaning_steps['Final Cleaned Data (Strictly 2019)'] = len(df)
    
    return df

try:
    df_raw = load_and_clean_data()
except Exception as e:
    st.error(f"Error loading 'Sales Data.csv'. Details: {e}")
    st.stop()

st.title("🔌 Electronics Store Sales Performance Dashboard (2019)")
st.sidebar.header("🎛️ Dashboard Filters")

available_months = sorted(df_raw['Month'].unique(), key=lambda m: pd.to_datetime(m, format='%B').month)
available_cities = sorted(df_raw['City'].unique())
available_products = sorted(df_raw['Product'].unique())

selected_months = st.sidebar.multiselect("Select Months", available_months, default=available_months)
selected_cities = st.sidebar.multiselect("Select Cities", available_cities, default=available_cities)
selected_products = st.sidebar.multiselect("Select Products", available_products, default=available_products)

filtered_df = df_raw[
    (df_raw['Month'].isin(selected_months)) & 
    (df_raw['City'].isin(selected_cities)) & 
    (df_raw['Product'].isin(selected_products))
]

tab1, tab2 = st.tabs(["📊 Dashboard Analysis", "🧹 Data Cleaning & Outliers"])

if filtered_df.empty:
    with tab1:
        st.warning("⚠️ No data matches your filter criteria.")
    with tab2:
        st.info("Adjust sidebars or see data cleaning transformations below.")
else:
    with tab1:
        total_sales = filtered_df['Sales'].sum()
        num_orders = filtered_df['Order ID'].nunique()
        items_sold = filtered_df['Quantity Ordered'].sum()
        avg_order_val = total_sales / num_orders if num_orders > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Total Sales", f"${total_sales:,.2f}")
        col2.metric("📦 Number of Orders", f"{num_orders:,}")
        col3.metric("🛒 Items Sold", f"{items_sold:,}")
        col4.metric("📈 Avg Order Value", f"${avg_order_val:,.2f}")

        st.markdown("---")
        st.header("🔍 Univariate Analysis")
        u_col1, u_col2 = st.columns(2)
        
        with u_col1:
            fig_qty = px.histogram(filtered_df, x="Quantity Ordered", title="Distribution of Quantity Ordered", nbins=10, text_auto=True)
            st.plotly_chart(fig_qty, use_container_width=True)
            fig_sales = px.histogram(filtered_df, x="Sales", title="Distribution of Sales Value per Row", nbins=30)
            st.plotly_chart(fig_sales, use_container_width=True)
            fig_city = px.bar(filtered_df['City'].value_counts().reset_index(), x='City', y='count', title="Order Distribution across Cities")
            st.plotly_chart(fig_city, use_container_width=True)
            fig_hour = px.histogram(filtered_df, x="Hour", title="Order Frequency by Hour of Day", nbins=24)
            st.plotly_chart(fig_hour, use_container_width=True)

        with u_col2:
            fig_price = px.histogram(filtered_df, x="Price Each", title="Distribution of Unit Price Each", nbins=30)
            st.plotly_chart(fig_price, use_container_width=True)
            fig_product = px.bar(filtered_df['Product'].value_counts().reset_index(), x='count', y='Product', orientation='h', title="Order Counts per Product Type")
            st.plotly_chart(fig_product, use_container_width=True)
            month_counts = filtered_df['Month'].value_counts().reindex(available_months).dropna().reset_index()
            fig_month = px.bar(month_counts, x='Month', y='count', title="Order Frequency across Months")
            st.plotly_chart(fig_month, use_container_width=True)

        st.markdown("---")
        st.header("🔗 Bivariate Analysis")
        b_col1, b_col2 = st.columns(2)
        
        with b_col1:
            city_avg_sales = filtered_df.groupby('City')['Sales'].mean().reset_index().sort_values(by='Sales', ascending=False)
            fig_b1 = px.bar(city_avg_sales, x='City', y='Sales', title="Average Sales Value per Order Across Cities")
            st.plotly_chart(fig_b1, use_container_width=True)
            month_sales = filtered_df.groupby('Month')['Sales'].sum().reindex(available_months).dropna().reset_index()
            fig_b3 = px.line(month_sales, x='Month', y='Sales', title="Total Sales Trend Across Months", markers=True)
            st.plotly_chart(fig_b3, use_container_width=True)

        with b_col2:
            prod_qty = filtered_df.groupby('Product')['Quantity Ordered'].sum().reset_index().sort_values(by='Quantity Ordered', ascending=False)
            fig_b2 = px.bar(prod_qty, x='Quantity Ordered', y='Product', orientation='h', title="Total Quantity Demanded per Product")
            st.plotly_chart(fig_b2, use_container_width=True)
            hour_sales = filtered_df.groupby('Hour')['Sales'].sum().reset_index()
            fig_b4 = px.line(hour_sales, x='Hour', y='Sales', title="Total Revenue Collected by Hour of Day", markers=True)
            st.plotly_chart(fig_b4, use_container_width=True)

        st.markdown("---")
        st.header("🧠 Research Questions")
        st.subheader("Research Question 1: Which day of the week generates the highest sales revenue?")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_sales = filtered_df.groupby('Day of Week')['Sales'].sum().reindex(day_order).reset_index()
        fig_q1 = px.bar(day_sales, x='Day of Week', y='Sales', color='Sales', title="Weekly Revenue Distribution Pattern")
        st.plotly_chart(fig_q1, use_container_width=True)

        st.subheader("Research Question 2: Which State brings in the highest aggregate volume of sales?")
        state_sales = filtered_df.groupby('State')['Sales'].sum().reset_index().sort_values(by='Sales', ascending=False)
        fig_q2 = px.pie(state_sales, values='Sales', names='State', title="Percentage Contribution of Total Sales Revenue by State", hole=0.4)
        st.plotly_chart(fig_q2, use_container_width=True)

        st.markdown("---")
        st.header("🎯 Conclusion")
        st.write("• **Peak Operational Hours:** Busiest hours are 11 AM - 1 PM and 6 PM - 8 PM.")
        st.write("• **Geographic Superpowers:** California locations lead market expansion.")

with tab2:
    st.header("🧹 Data Preprocessing & Cleaning Ledger")
    steps_df = pd.DataFrame(cleaning_steps.items(), columns=["Data Pipeline Step", "Remaining Row Count"])
    st.table(steps_df)
    
    st.markdown("---")
    st.header("📈 Outlier Evaluation Plots")
    o_col1, o_col2 = st.columns(2)
    with o_col1:
        fig_box_qty = px.box(df_raw, y="Quantity Ordered", title="Quantity Ordered Outlier Detection Boxplot")
        st.plotly_chart(fig_box_qty, use_container_width=True)
    with o_col2:
        fig_box_sales = px.box(df_raw, y="Sales", title="Sales Per Row Outlier Detection Boxplot")
        st.plotly_chart(fig_box_sales, use_container_width=True)