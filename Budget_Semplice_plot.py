import pandas as pd
import datetime as dt
import os
import math
import glob
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import plotly.subplots as sp


# Ottieni i nomi dei file CSV nella tua directory
path = 'C:\\Users\\Davidde\\Downloads\\Telegram Desktop\\Budget semplice'

def collect_file(path,name):
    filenames = glob.glob(path + f"/*202*-{name}.csv", recursive=True)
    # Ordina i file dal più recente al più vecchio
    filenames.sort(key=os.path.getmtime)
    # Inverti l'ordine della lista per avere i file dal più vecchio al più nuovo
    filenames = filenames[::-1]
    number_sample = len(filenames)
    return filenames, number_sample

def month_year():
    now = dt.datetime.now()
    return now.month, now.year

def collect_data_from_list_csv(path,file_name,wanted_regexp,scaling_factor):
    filenames,number_sample = collect_file(path,file_name)
    # Crea una lista vuota per i valori
    values_collected = []

    # Leggi ogni file e aggiungi il valore alla lista
    for filename in filenames:
        df = pd.read_csv(filename, sep=';', header=None, names=['Descrizione', 'Valore'])
        collected_data = df[df['Descrizione'] == f'{wanted_regexp}']['Valore'].values[0]
        collected_data = (collected_data.replace('€', '').replace('.', '').replace(',', '.').strip())
        try:
            if collected_data.startswith('-'):
                collected_data = float(collected_data[1:]) * -1
            else:
                collected_data = float(collected_data)
            values_collected = np.append(values_collected,collected_data*scaling_factor)
        except ValueError:
            print(f"Impossibile convertire {collected_data} in float.")
    return values_collected,number_sample

def simple_mean(previous_avg, new_value, n):
    # You need to define this function for computing the new average.
    # Assuming `previous_avg` is the average of the first `n-1` items,
    # `new_value` is the nth item, and `n` is the total count,
    # the new average will be computed as follows:
    return ((previous_avg * (n - 1)) + new_value) / n

def dynamic_avg(values):
    # This function calculates the dynamic average of a list of values.
    avg_values = []
    avg_intermediate = []

    for i, value in enumerate(values):
        if i == 0:
            # The average of the first element is the element itself.
            new_avg = value
        else:
            # Compute the new average based on the previous one.
            new_avg = simple_mean(avg_intermediate[i-1], value, i+1)
        
        # Append the new average to the intermediate list.
        avg_intermediate.append(new_avg)

        # Append the new average to the final list of averages.
        avg_values.append(new_avg)

    # Convert the list of averages to a numpy array.
    return np.array(avg_values)

def sum(values):
    sum_value = 0
    sum_value_list = []
    for i, value in enumerate(values):
        sum_value += value
        sum_value_list.append(sum_value)
    return sum_value_list,sum_value

def create_plot(x,y,name_trace,name_graph,overlap,y1,name_trace_1):
    fig  = go.Figure()
    # Aggiungi i valori al grafico
    if (overlap):
     fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=f'{name_trace}'))
     fig.add_trace(go.Scatter(x=x, y=y1, mode='lines+markers', name=f'{name_trace_1}'))
    else :
     fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=f'{name_trace}'))   
    # Imposta le etichette degli assi e il titolo
    fig.update_layout(
    title=f'{name_graph}',
    xaxis_title=f'09.2021 - {month}.{year}',
    yaxis_title='',
    legend_title='Legenda',
    hovermode="x"
    )
    fig.show()
    return fig

def create_subplot(x, y, y1, name_trace, name_trace_1, name_graph, overlap):
    # Creazione di un oggetto subplots
    subplots = sp.make_subplots(rows=1, cols=2, specs=[[{'type': 'scatter'}, {'type': 'scatter'}]])

    # Aggiungi i valori al grafico
    if overlap:
        subplots.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=f'{name_trace}'), row=1, col=1)
        subplots.add_trace(go.Scatter(x=x, y=y1, mode='lines+markers', name=f'{name_trace_1}'), row=1, col=2)
    else:
        subplots.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=f'{name_trace}'), row=1, col=1)

    # Imposta le etichette degli assi e il titolo
    subplots.update_layout(
        title=f'{name_graph}',
        xaxis_title=f'09.2021 - {month}.{year}',
        yaxis_title='',
        legend_title='Legenda',
        hovermode="x"
    )

    # Mostra il grafico
    subplots.show()

    return subplots

def reddito_annuo(reference_year,reference_month,path,scaling_factor):
    date_list_annuo              = pd.date_range(start=f'{reference_year-1}-{reference_month}',end =f'{reference_year}-{reference_month}',freq='MS')
    reddito_values,number_months = collect_data_from_list_csv(path,file_name='Reddito',wanted_regexp='Stipendio',scaling_factor=scaling_factor)
    initial_date_record          = pd.to_datetime('2021-09-01')
    start_date                   = pd.to_datetime(f'{reference_year}-{reference_month}')
    reddito_annuo_result         = 0.0
    try:
            if initial_date_record <= start_date:
                delta = (start_date - initial_date_record)
                delta_in_months = delta.days / (30 if reference_year % 4 == 0 and (reference_year % 100 != 0 or reference_year % 400 == 0) else 31)
                delta_in_months_rounded = math.floor(delta_in_months + 0.5) if delta_in_months % 1 >= 0.5 else math.ceil(delta_in_months - 0.5) if delta_in_months % 1 < 0.5 else delta_in_months
    except ValueError:
            print(f"Impossibile accedere a {reddito_values} in float.")
    if delta_in_months_rounded <= 12 :
        for i in range(delta_in_months_rounded):
            reddito_annuo_result += reddito_values[i]
    else :
        for i in range(delta_in_months_rounded-12,delta_in_months_rounded):
            reddito_annuo_result += reddito_values[i]
    return reddito_annuo_result

def numero_anni(number_samples):
    numero_anni = number_samples // 12
    return numero_anni

def reddito_annuo_totale(number_samples,scaling_factor):
    numero_anni_osservati = numero_anni(number_samples=number_samples)
    reddito_diviso_per_anni = []
    growth_rate = []
    average_growth_rate = []
    start_ref_year = 2022
    ref_month = 9
    date_list = pd.date_range(start=f'{start_ref_year}-{ref_month}', end=f'{start_ref_year-1+numero_anni_osservati}-{ref_month}', freq='MS')
    date_anni = {date_list[0],date_list[-1]}
    date_anni = pd.DatetimeIndex(date_anni)
    for i in range(numero_anni_osservati):
        redd_obs_year = reddito_annuo(reference_year=start_ref_year+i,reference_month=ref_month,path=path,scaling_factor=scaling_factor)
        reddito_diviso_per_anni = np.append(reddito_diviso_per_anni,redd_obs_year)
    # Calcola la differenza tra ogni valore e il precedente
    diff = np.diff(reddito_diviso_per_anni)
    # Rimuovere l'elemento di posizione 0
    diff = np.squeeze(diff)
    # Calcola il tasso di crescita
    growth_rate = diff / reddito_diviso_per_anni[:-1]
    # Calcola il tasso di crescita medio
    average_growth_rate = np.mean(growth_rate)    
    return reddito_diviso_per_anni,growth_rate,average_growth_rate,date_anni

# Time Informations
month,year = month_year()

# Crea una lista di date dal settembre 2021 fino al mese e all'anno correnti
date_list = pd.date_range(start='2021-09', end=f'{year}-{month}', freq='MS')
# Valore finale
values_collect,number_months = collect_data_from_list_csv(path,file_name='Netto',wanted_regexp='Reddito meno spese',scaling_factor=1)
avg_values = dynamic_avg(values=values_collect)
reddito_values,number_months = collect_data_from_list_csv(path,file_name='Reddito',wanted_regexp='Reddito totale',scaling_factor=1)
reddito_avg_values = dynamic_avg(values=reddito_values)
reddito_diviso_per_anni,growth_rate,average_growth_rate,observed_years = reddito_annuo_totale(number_months,scaling_factor=1)
spese_collect,number_months = collect_data_from_list_csv(path,file_name='Spese',wanted_regexp='Spese totali',scaling_factor=1)
investment_collect,number_months = collect_data_from_list_csv(path,file_name='Spese',wanted_regexp='Investimenti',scaling_factor=1)
spese_collect_avg_values = dynamic_avg(values=spese_collect)
investment_collect_avg_values = dynamic_avg(values=investment_collect)
investement_total_list,investment_total = sum(investment_collect)
risparmio_total_list,risparmio_total = sum(values_collect)
spese_minus_investment_values = spese_collect - investment_collect
spese_minus_investment_avg_values = spese_collect_avg_values - investment_collect_avg_values
total_expenses_list,total_expenses = sum(spese_minus_investment_values)
annual_expenses = (total_expenses/number_months)*12
FI = annual_expenses * 25



fig  = create_plot(x=date_list,y=values_collect,name_graph='Reddito meno spese',name_trace='Grafico Risparmio',overlap = 1,y1=avg_values,name_trace_1='Media Reddito meno Spese')
fig1 = create_plot(x=date_list,y=reddito_values,name_graph='Stipendio',name_trace='Stipendio Percepito k€',overlap = 1,y1 = reddito_avg_values, name_trace_1='Stipendio Medio')
fig2 = create_plot(x=observed_years,y=reddito_diviso_per_anni,name_graph='Reddito annuo',name_trace='Reddito annuo',overlap = 1,y1=growth_rate,name_trace_1='Grothw_rate')
fig3 = create_plot(x=date_list,y=spese_collect,name_graph='Spese per mese',name_trace='Spese Mensili',overlap = 1,y1=spese_collect_avg_values,name_trace_1='Spese Medie Mensili')
fig4 = create_plot(x=date_list,y=spese_minus_investment_values,name_graph='Spese - Investimenti',name_trace='Spese - Investimenti Mensili',overlap = 1,y1=spese_minus_investment_avg_values,name_trace_1='Spese - Investimenti Medi')
fig5 = create_plot(x=date_list,y=investement_total_list,name_graph='Investimenti',name_trace='Investimenti Mensili',overlap = 1,y1=risparmio_total_list,name_trace_1='Risparmio Mensili')
