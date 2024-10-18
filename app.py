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
        return abs(int(round((current_value - previous_value) / previous_value * 100 + 100, 0)))

# Sidebar for GitHub file URL input and macro analysis options
st.sidebar.title("Acompanhamento de custos")
st.sidebar.write("Análises de despesas pessoais")

# Input the GitHub raw file URL
file_url_fatura = "https://raw.githubusercontent.com/soilmo/Financas/main/historico_fatura_nubank.xlsx"
file_url_extrato = "https://raw.githubusercontent.com/soilmo/Financas/main/historico_extrato_nubank.xlsx"

# Load the Excel data directly from GitHub into memory
try:
    
    # Fatura
    data = load_excel_from_github(file_url_fatura)
    data['Mes'] = data['data_pagamento'].dt.strftime('%Y-%m')
    unique_months = data['Mes'].unique()
    all_categories = data['categoria'].unique()

    # Extrato
    df_extrato = load_excel_from_github(file_url_extrato)
    df_extrato['Mes'] = df_extrato['data_pagamento'].dt.strftime('%Y-%m')

    # Base geral
    data = pd.concat([data, df_extrato])
    

    # Set default month to the most recent one
    default_month = max(unique_months)


    # Sidebar options for different types of analysis
    analysis_type = st.sidebar.selectbox(
        "Escolha a análise",
        ["Resumo", "Visão mensal", "Visão por categoria"]
    )

    # Show basic data Resumo
    if analysis_type == "Resumo":

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
            'redução': abs(reductions.values),
            '%': [
                calculate_percentage_change(current, previous_month_totals.get(cat, 0))
                for cat, current in zip(reductions.index, reductions.values)
            ]
        }).head()

        reduction_df.set_index("categoria", inplace = True)

        # Linha resumo
        # Valor total e variação percentual
        total_0 = round(data[data['Mes'] == latest_month]['valor'].sum(),2)
        total_1 = round(data[data['Mes'] == previous_month]['valor'].sum(),2)
        var_pct = (round(100*(total_0/total_1 - 1),0))

        # Valor total crédito e variação percentual
        total_0_cred = round(data[(data['Mes'] == latest_month)&(data['tipo'] == "Crédito")]['valor'].sum(),2)
        total_1_cred = round(data[(data['Mes'] == previous_month)&(data['tipo'] == "Crédito")]['valor'].sum(),2)
        var_pct_cred = (round(100*(total_0_cred/total_1_cred - 1),0))

        
        # Valor total débito e variação percentual
        total_0_deb = round(data[(data['Mes'] == latest_month)&(data['tipo'] == "Débito")]['valor'].sum(),2)
        total_1_deb = round(data[(data['Mes'] == previous_month)&(data['tipo'] == "Débito")]['valor'].sum(),2)
        var_pct_deb = (round(100*(total_0_deb/total_1_deb - 1),0))

        # Gasto diário
        total_0_dia = round(data[(data['Mes'] == latest_month)]['valor'].sum()/data[(data['Mes'] == latest_month)].shape[0],2)
        total_1_dia = round(data[(data['Mes'] == previous_month)]['valor'].sum()/data[(data['Mes'] == previous_month)].shape[0],2)
        var_pct_dia = (round(100*(total_0_dia/total_1_dia - 1),0))



        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", total_0, f'{var_pct}%')
        col2.metric("Crédito", total_0_cred,  f'{var_pct_cred}%')
        col3.metric("Débito", total_0_deb,  f'{var_pct_deb}%')
        col4.metric("Gasto diário médio", total_0_dia,  f'{var_pct_dia}%')

        # Split layout into two columns for Increases and Reductions
        col1, col2 = st.columns(2)

        # Show largest increases in the left column
        with col1:
            st.subheader(f"Top aumentos de {previous_month} a {latest_month}")
            st.dataframe(increase_df)

        # Show largest reductions in the right column
        with col2:
            st.subheader(f"Top reduções de {previous_month} a {latest_month}")
            st.dataframe(reduction_df)
        
        
    # Visão mensal bar chart
    if analysis_type == "Visão mensal":

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
    if analysis_type == "Visão por categoria":
        st.title("Despesas por categoria")

        # Create a month filter
        selected_month = st.selectbox("Mês escolhido", options=unique_months, index=unique_months.tolist().index(default_month))

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

        text_pie = pie.mark_text(radius=140, size=20).encode(text="valor:Q")

        selection = alt.selection_multi(fields=['categoria'], bind='legend')
        pie = pie.add_selection(
            selection
        ).encode(
            opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
        )

        st.altair_chart((pie + text_pie).interactive(), use_container_width=True)

except Exception as e:
    st.error(f"Error loading the file: {e}")
