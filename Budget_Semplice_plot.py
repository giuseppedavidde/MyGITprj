import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import os
import glob
import plotly.graph_objects as go

# Ottieni i nomi dei file CSV nella tua directory
path = 'C:\\Users\\Davidde\\Downloads\\Telegram Desktop\\Budget semplice'

def collect_file_netto(path):
    filenames = glob.glob(path + "/*202*-Netto.csv", recursive=True)
    # Ordina i file dal più recente al più vecchio
    filenames.sort(key=os.path.getmtime)
    # Inverti l'ordine della lista per avere i file dal più vecchio al più nuovo
    filenames = filenames[::-1]
    number_sample = len(filenames)
    return filenames, number_sample

def month_year():
    now = dt.datetime.now()
    return now.month, now.year

def dynamic_mean(previous,current):
    avg = float ((previous + current)/2)
    return avg

filenames,number_sample = collect_file_netto(path)
month,year = month_year()

# Crea una lista di date dal settembre 2021 fino al mese e all'anno correnti
date_list = pd.date_range(start='2021-09', end=f'{year}-{month}', freq='MS')

# Crea una lista vuota per i valori
values = []

# Leggi ogni file e aggiungi il valore alla lista
for filename in filenames:
    df = pd.read_csv(filename, sep=';', header=None, names=['Descrizione', 'Valore'])
    reddito_meno_spese = df[df['Descrizione'] == 'Reddito meno spese']['Valore'].values[0]
    reddito_meno_spese = (reddito_meno_spese.replace('€', '').replace('.', '').replace(',', '.').strip())
    try:
        if reddito_meno_spese.startswith('-'):
            reddito_meno_spese = float(reddito_meno_spese[1:]) * -1
        else:
            reddito_meno_spese = float(reddito_meno_spese)
        values.append(reddito_meno_spese)
    except ValueError:
        print(f"Impossibile convertire {reddito_meno_spese} in float.")

# Valore finale
sum_values = sum(values)
avg_values = []

for i in range(len(values)):
    try:
        if i == len(values):
            avg_intermediate = dynamic_mean(values[i],values[i])
        if i > 0:
            avg_intermediate = dynamic_mean(values[i-1],values[i])
        else:
            avg_intermediate = dynamic_mean(values[i],values[i])
    except ValueError:
        print(f"Impossibile accedere a {values} in float.")
    avg_values.append(avg_intermediate)

##### matplotlib Version  ###
############################# 
# Crea un grafico
# fig, ax = plt.subplots()
# ax.plot(date_list, values, marker='o', linestyle='-')
# # Disegna la media
# ax.plot(date_list, avg_values, marker='*', linestyle='--' )

# # Formatta l'asse x per mostrare le date nel formato MM.YYYY
# ax.xaxis.set_major_locator(mdates.MonthLocator())
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%m'))


# plt.xlabel(f'09.21 - {month}.{year}')
# plt.ylabel('Reddito meno spese (€)')
# plt.title('Reddito meno spese per file')
# plt.legend('o = month_value , * = dynamic_avg_2_months')
# plt.show()# Crea un grafico
#############################

fig = go.Figure()

# Aggiungi i valori al grafico
fig.add_trace(go.Scatter(x=date_list, y=values, mode='lines+markers', name='Valori'))

# Aggiungi la media al grafico
fig.add_trace(go.Scatter(x=date_list, y=avg_values, mode='lines+markers', name='Media'))

# Imposta le etichette degli assi e il titolo
fig.update_layout(
    title='Reddito meno spese per file',
    xaxis_title=f'09.21 - {month}.{year}',
    yaxis_title='Reddito meno spese (€)',
    legend_title='Legenda',
    hovermode="x"
)

# Mostra il grafico
fig.show()



