# Arquivo


import streamlit as st
import pandas as pd
#import plotly.express as px
import altair as alt

# Function to load Excel file from GitHub
def load_excel_from_github(url):
    df = pd.read_excel(url, engine='openpyxl')
    return df

# Helper function to calculate monthly changes
def calculate_monthly_change(df):
    monthly_totals = df.groupby(['Mes', 'categoria'])['valor'].sum().unstack().fillna(0)
    previous_month = monthly_totals.shift(1)
    changes = monthly_totals - previous_month
    print(changes)
    return changes

# Function to calculate percentage change from previous month
def calculate_percentage_change(current_value, previous_value):
    if previous_value == 0:
        return float('inf') if current_value > 0 else 0
    else:
        return (current_value - previous_value) / previous_value * 100

# Sidebar for GitHub file URL input and macro analysis options
st.sidebar.title("Expense Tracker")
st.sidebar.write("Analyze your personal expenses")

# Input the GitHub raw file URL
#file_url = st.sidebar.text_input("Enter GitHub raw file URL for the Excel file")
file_url = "https://raw.githubusercontent.com/soilmo/Financas/main/historico_fatura_nubank.xlsx"

if file_url:
    # Load the Excel data directly from GitHub into memory
    try:
        data = load_excel_from_github(file_url)
        data['Mes'] = data['data_pagamento'].dt.strftime('%Y-%m')
        unique_months = data['Mes'].unique()
        all_categories = data['categoria'].unique()

        # Set default month to the most recent one
        default_month = max(unique_months)


        # Sidebar options for different types of analysis
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type",
            ["Overview", "Monthly Breakdown", "Category Breakdown", "Spending Trend"]
        )

        # Show basic data overview
        if analysis_type == "Overview":

            latest_month = unique_months[-1]
            previous_month = unique_months[-2]

            changes = calculate_monthly_change(data)

            # Largest increases and reductions in value
            increases = changes.loc[latest_month].sort_values(ascending=False)
            reductions = changes.loc[latest_month].sort_values()

            # Retrieve previous month's totals for percentage calculation
            previous_month_totals = data[data['Mes'] == previous_month].groupby('categoria')['valor'].sum()

            # Create a DataFrame for Increases with percentage changes
            increase_df = pd.DataFrame({
                'categoria': increases.index,
                'aumentos': increases.values,
                '%': [
                    calculate_percentage_change(current, previous_month_totals.get(cat, 0))
                    for cat, current in zip(increases.index, increases.values)
                ]
            }).head()

            increase_df.set_index("categoria", inplace = True)

            # Create a DataFrame for Reductions with percentage changes
            reduction_df = pd.DataFrame({
                'categoria': reductions.index,
                'redução': reductions.values,
                '%': [
                    calculate_percentage_change(current, previous_month_totals.get(cat, 0))
                    for cat, current in zip(reductions.index, reductions.values)
                ]
            }).head()

            reduction_df.set_index("categoria", inplace = True)

            # Split layout into two columns for Increases and Reductions
            col1, col2 = st.columns(2)

            # Show largest increases in the left column
            with col1:
                st.subheader(f"Largest Increases from {previous_month} to {latest_month}")
                st.table(increase_df)

            # Show largest reductions in the right column
            with col2:
                st.subheader(f"Largest Reductions from {previous_month} to {latest_month}")
                st.table(reduction_df)
            
            
        # Monthly breakdown bar chart
        if analysis_type == "Monthly Breakdown":

            st.title("Monthly Expense Breakdown")
            
            # Create a multiselect widget to filter by category
            selected_categories = st.multiselect(
                "Select categories to include",
                options=all_categories,
                default=all_categories  # Default: show all categories
            )

            if len(selected_categories) == 0:
                selected_categories = all_categories

            # Filter data based on selected categories
            filtered_data = data[data['categoria'].isin(selected_categories)]
            
            monthly_expenses = filtered_data.groupby('Mes')['valor'].sum().reset_index()


            # Grafico de barras
            bars = alt.Chart(monthly_expenses).mark_bar().encode(
                x="Mes",
                y="valor"
            ).properties(
                width=600,
                height=400,
            )

            text = bars.mark_text(
                align='center',
                baseline='top',
                color = 'white'
            ).encode(
                text='valor:Q'
            )

            # Show the chart
            st.altair_chart(bars+text, use_container_width=True)

             # Create a line plot for each category's total per month
            category_monthly_expenses = filtered_data.groupby(['Mes', 'categoria'])['valor'].sum().reset_index()
            
            linha = alt.Chart(category_monthly_expenses).mark_line(point=True).encode(
                x="Mes",
                y="valor",
                color=alt.Color("categoria"),
            )
            
            text_linha = linha.mark_text(
                align='center',
                baseline='top',
                color = 'white'
            ).encode(
                text='valor:Q'
            )

            selection = alt.selection_multi(fields=['categoria'], bind='legend')

            linha = linha.add_selection(
                selection
            ).encode(
                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
            )
            
            st.altair_chart((linha + text_linha).interactive(), use_container_width=True)


        # Category-wise spending breakdown
        if analysis_type == "Category Breakdown":
            st.title("Despesas por categoria")

            # Create a month filter
            selected_month = st.selectbox("Select Month", options=unique_months, index=unique_months.tolist().index(default_month))

            # Filter data based on the selected month
            filtered_data_by_month = data[data['Mes'] == selected_month]

            # Group data by category for the selected month
            category_expenses = filtered_data_by_month.groupby('categoria')['valor'].sum().reset_index()

            # Calculate the total spending for the month
            total_expenses = category_expenses['valor'].sum()

            # Find small categories contributing less than 10% and group them into "Other"
            threshold = 0.01 * total_expenses
            small_categories = category_expenses[category_expenses['valor'] < threshold]
            large_categories = category_expenses[category_expenses['valor'] >= threshold]

            # Group small categories into "Other"
            other_expenses = pd.DataFrame({
                'categoria': ['Outros'],
                'valor': [small_categories['valor'].sum()]
            })

            # Concatenate large categories with the "Other" category
            final_expenses = pd.concat([large_categories, other_expenses])

            pie = alt.Chart(final_expenses).mark_arc(outerRadius=120).encode(
                theta="valor:Q",
                color=alt.Color("categoria:N", legend=None)
            )

            
            selection = alt.selection_multi(fields=['categoria'], bind='legend')
            pie = pie.add_selection(
                selection
            ).encode(
                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
            )

            text_pie = pie.mark_text(radius=140, size=20).encode(text="valor:Q")

            st.altair_chart((pie + text_pie).interactive(), use_container_width=True)

            # # Create pie chart with percentage and total value
            # pie_fig = px.pie(
            #     final_expenses,
            #     names='categoria',
            #     values='valor',
            #     title=f"Category Breakdown for {selected_month}",
            #     hole=0  # Optional: Creates a donut chart
            # )

            # # Show the pie chart
            # st.plotly_chart(pie_fig)

        # Spending trend over time (line chart)
        if analysis_type == "Spending Trend":
            st.title("Spending Trend Over Time")
            fig = px.line(data, x='data', y='valor', title="Spending Trend")
            st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Error loading the file: {e}")
else:
    st.write("Please enter a valid GitHub raw file URL to begin analysis.")
