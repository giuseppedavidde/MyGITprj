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
ref_year  = 2021
ref_month = 9

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
            values_collected.append(collected_data*scaling_factor)
        except ValueError:
            print(f"Impossibile convertire {collected_data} in float.")
    return values_collected,number_sample

def simple_mean(previous,current):
    avg = float ((previous + current)/2)
    return avg

def dynamic_avg(values):
    # Media Dinamica
    avg_values = []

    for i in range(len(values)):
        try:
            if i == len(values):
                avg_intermediate = simple_mean(values[i],values[i])
            if i > 0:
                avg_intermediate = simple_mean(values[i-1],values[i])
            else:
                avg_intermediate = simple_mean(values[i],values[i])
            avg_values.append(avg_intermediate)
        except ValueError:
            print(f"Impossibile accedere a {values} in float.")
    return avg_values

def create_plot(start_date,end_date,x,y,name_trace,name_graph,overlap,y1,name_trace_1):
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
    xaxis_title=f'{start_date}-{end_date}',
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
    start_date                   = pd.to_datetime(date_list_annuo[0])
    try:
            if initial_date_record <= start_date:
                delta = (start_date - initial_date_record)
                delta_in_months = delta.days / (30 if reference_year % 4 == 0 and (reference_year % 100 != 0 or reference_year % 400 == 0) else 31)
                delta_in_months_rounded = math.floor(delta_in_months + 0.5) if delta_in_months % 1 >= 0.5 else math.ceil(delta_in_months - 0.5) if delta_in_months % 1 < 0.5 else delta_in_months
    except ValueError:
            print(f"Impossibile accedere a {reddito_values} in float.")
    reddito_annuo_result = np.sum(reddito_values[delta_in_months_rounded:delta_in_months_rounded+12])
    return reddito_annuo_result

def numero_anni(number_samples):
    numero_anni = number_samples // 12
    return numero_anni

def reddito_annuo_totale(number_samples,ref_year,ref_month,scaling_factor):
    numero_anni_osservati = numero_anni(number_samples=number_samples)
    reddito_diviso_per_anni = []
    growth_rate = []
    average_growth_rate = []
    start_ref_year = ref_year
    ref_month_int  = ref_month
    start_ref_date = pd.to_datetime(f'{start_ref_year}-{ref_month}')
    end_date       = pd.to_datetime(f'{start_ref_year+numero_anni_osservati}-{ref_month}')
    date_list      = pd.date_range(start_ref_date, end_date,freq='MS')
    date_list      = date_list[::-1]
    observed_years = pd.to_datetime({date_list[0],date_list[-1]})
    for i in range(numero_anni_osservati):
        redd_obs_year = reddito_annuo(reference_year=start_ref_year+1+i,reference_month=ref_month,path=path,scaling_factor=scaling_factor)
        reddito_diviso_per_anni.append(redd_obs_year)
    # Calcola la differenza tra ogni valore e il precedente
    diff = np.diff(reddito_diviso_per_anni)
    # Rimuovere l'elemento di posizione 0
    diff = np.squeeze(diff)
    # Calcola il tasso di crescita
    growth_rate = diff / reddito_diviso_per_anni[:-1]
    # Calcola il tasso di crescita medio
    average_growth_rate = np.mean(growth_rate)    
    return reddito_diviso_per_anni,growth_rate,average_growth_rate,observed_years

# Time Informations
month,year = month_year()

# Crea una lista di date dal settembre 2021 fino al mese e all'anno correnti
date_list = pd.date_range(start='2021-09', end=f'{year}-{month}', freq='MS')
# Valore finale
values,number_months = collect_data_from_list_csv(path,file_name='Netto',wanted_regexp='Reddito meno spese',scaling_factor=1)
avg_values = dynamic_avg(values)
reddito_values,number_months = collect_data_from_list_csv(path,file_name='Reddito',wanted_regexp='Stipendio',scaling_factor=1)
reddito_avg_values = dynamic_avg(reddito_values)
reddito_diviso_per_anni,growth_rate,average_growth_rate,observed_years = reddito_annuo_totale(number_months,ref_year=ref_year,ref_month=ref_month,scaling_factor=0.001)

fig  = create_plot(start_date='2021-09-01',end_date=f'{year}-{month}',x=date_list,y=values,name_graph='Reddito meno spese',name_trace='Grafico Risparmio',overlap = 1,y1=avg_values,name_trace_1='Media Reddito meno Spese')
fig1 = create_plot(start_date='2021-09-01',end_date=f'{year}-{month}',x=date_list,y=reddito_values,name_graph='Stipendio',name_trace='Stipendio Percepito k€',overlap = 0,y1 = 0, name_trace_1='')
fig2 = create_plot(start_date=f'{ref_year}-{ref_month}',end_date=f'{year}-{month}',x=observed_years,y=reddito_diviso_per_anni,name_graph='Reddito annuo',name_trace='Reddito annuo',overlap = 1,y1=growth_rate,name_trace_1='Grothw_rate')
