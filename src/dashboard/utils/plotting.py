import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_sales_over_time(df, title="Sales Over Time"):
    """
    Interactive line chart of sales.
    """
    daily = df.groupby('date')['sales'].sum().reset_index()
    fig = px.line(daily, x='date', y='sales', title=title)
    fig.update_layout(template="plotly_white")
    return fig

def plot_earthquake_impact(df, region_col='state'):
    """
    Bar chart showing growth/decline by region before/after earthquake.
    Hardcoded dates for the 2016 Ecuador Earthquake.
    """
    # Define periods
    earthquake_date = pd.Timestamp('2016-04-16')
    shock_period_end = pd.Timestamp('2016-04-30')
    
    # Filter for relevant window (March to May 2016)
    mask_crisis = (df['date'] >= earthquake_date) & (df['date'] <= shock_period_end)
    mask_normal = (df['date'] >= '2016-03-01') & (df['date'] < earthquake_date)
    
    # Calculate means
    crisis_sales = df[mask_crisis].groupby(region_col)['sales'].mean()
    normal_sales = df[mask_normal].groupby(region_col)['sales'].mean()
    
    # Calc variation
    impact = ((crisis_sales - normal_sales) / normal_sales * 100).sort_values(ascending=False).reset_index()
    impact.columns = [region_col, 'Variation (%)']
    
    # Plot
    fig = px.bar(
        impact, 
        x=region_col, 
        y='Variation (%)',
        color='Variation (%)',
        color_continuous_scale="RdYlGn",
        title=f"Earthquake Impact by {region_col} (Sales Variation)"
    )
    # Add reference line
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    return fig

def plot_promo_scatter(df, families):
    """
    Scatter plot: Promo Intensity vs Sales Lift for top families
    """
    # Filter for selected families
    subset = df[df['family'].isin(families)]
    
    # Aggregate by family and onpromotion count buckets? 
    # Or just correlation. Let's do daily scatter just for one family or agg
    
    # Better: Scatter of Daily Sales vs Daily OnPromotion
    fig = px.scatter(
        subset, 
        x='onpromotion', 
        y='sales', 
        color='family', 
        trendline="ols", # Add regression line
        title="Impact of Promotions on Sales (Elasticity check)",
        opacity=0.5
    )
    return fig

def plot_oil_vs_sales(df):
    """
    Dual Axis plot for Oil vs Sales
    """
    weekly = df.set_index('date').resample('W').agg({'sales':'sum', 'dcoilwtico':'mean'}).reset_index()
    
    fig = go.Figure()
    
    # Sales Bar
    fig.add_trace(go.Scatter(
        x=weekly['date'], 
        y=weekly['sales'],
        name='Total Sales',
        mode='lines',
        line=dict(color='teal')
    ))
    
    # Oil Line (Secondary Y)
    fig.add_trace(go.Scatter(
        x=weekly['date'],
        y=weekly['dcoilwtico'],
        name='Oil Price',
        mode='lines',
        line=dict(color='orange', dash='dot'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Macro View: Oil Economy vs Retail Sales",
        yaxis=dict(title="Sales Volume"),
        yaxis2=dict(title="Oil Price ($)", overlaying='y', side='right'),
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig
