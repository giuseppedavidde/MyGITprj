import pandas as pd
import datetime as dt
import os
import glob
import plotly.graph_objects as go
import numpy as np

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
            values_collected.append(collected_data*scaling_factor)
        except ValueError:
            print(f"Impossibile convertire {collected_data} in float.")
    return values_collected

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

# Time Informations
month,year = month_year()

# Crea una lista di date dal settembre 2021 fino al mese e all'anno correnti
date_list = pd.date_range(start='2021-09', end=f'{year}-{month}', freq='MS')

# Valore finale
values = collect_data_from_list_csv(path,file_name='Netto',wanted_regexp='Reddito meno spese',scaling_factor=1)
avg_values = dynamic_avg(values)
reddito_values = collect_data_from_list_csv(path,file_name='Reddito',wanted_regexp='Stipendio',scaling_factor=0.001)
reddito_avg_values = dynamic_avg(reddito_values)
# Calcola la differenza tra ogni valore e il precedente
diff = np.diff(reddito_values)
# Calcola il tasso di crescita
growth_rate = diff / reddito_values[:-1]
# Calcola il tasso di crescita medio
average_growth_rate = np.mean(growth_rate)

fig  = create_plot(x=date_list,y=values,name_graph='Reddito meno spese',name_trace='Grafico Risparmio',overlap = 1,y1=avg_values,name_trace_1='Media Reddito meno Spese')
fig1 = create_plot(x=date_list,y=reddito_values,name_graph='Stipendio',name_trace='Stipendio Percepito k€',overlap = 1,y1=growth_rate,name_trace_1='Grothw_rate')
