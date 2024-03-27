import datetime as dt
import glob
import math
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from sklearn.linear_model import Lasso
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures

# Ottieni i nomi dei file CSV nella tua directory
path = "C:\\Users\\Davidde\\Downloads\\Telegram Desktop\\Budget semplice"


def collect_file(path, name):
    filenames = glob.glob(path + f"/*202*-{name}.csv", recursive=True)
    # Ordina i file dal più recente al più vecchio
    filenames.sort(key=os.path.getmtime)
    # Inverti l'ordine della lista per avere i file dal più vecchio al più
    # nuovo
    filenames = filenames[::-1]
    number_sample = len(filenames)
    return filenames, number_sample


def month_year():
    now = dt.datetime.now()
    return now.month, now.year


def collect_data_from_list_csv(path, file_name, wanted_regexp, scaling_factor):
    filenames, number_sample = collect_file(path, file_name)
    # Crea una lista vuota per i valori
    list_collected = []

    # Leggi ogni file e aggiungi il valore alla lista
    for filename in filenames:
        df = pd.read_csv(
            filename, sep=";", header=None, names=["Descrizione", "Valore"]
        )
        collected_data = df[df["Descrizione"] == f"{wanted_regexp}"]["Valore"].values[0]
        collected_data = (
            collected_data.replace("€", "").replace(".", "").replace(",", ".").strip()
        )
        try:
            if collected_data.startswith("-"):
                collected_data = float(collected_data[1:]) * -1
            else:
                collected_data = float(collected_data)
            list_collected = np.append(list_collected, collected_data * scaling_factor)
        except ValueError:
            print(f"Impossibile convertire {collected_data} in float.")
    return list_collected, number_sample


def simple_mean(previous_avg, new_value, n):
    # You need to define this function for computing the new average.
    # Assuming `previous_avg` is the average of the first `n-1` items,
    # `new_value` is the nth item, and `n` is the total count,
    # the new average will be computed as follows:
    return ((previous_avg * (n - 1)) + new_value) / n


def dynamic_avg(values):
    # This function calculates the dynamic average of a list of values.
    risparmio_netto_avg_values = []
    avg_intermediate = []

    for i, value in enumerate(values):
        if i == 0:
            # The average of the first element is the element itself.
            new_avg = value
        else:
            # Compute the new average based on the previous one.
            new_avg = simple_mean(avg_intermediate[i - 1], value, i + 1)

        # Append the new average to the intermediate list.
        avg_intermediate.append(new_avg)

        # Append the new average to the final list of averages.
        risparmio_netto_avg_values.append(new_avg)

    # Convert the list of averages to a numpy array.
    return np.array(risparmio_netto_avg_values)


def sum(values):
    sum_value = 0
    sum_value_list = []
    for i, value in enumerate(values):
        sum_value += value
        sum_value_list.append(sum_value)
    return np.array(sum_value_list), sum_value


def create_plot(x, y, name_trace, name_graph, overlap, n_traces):
    fig = go.Figure()
    # Aggiungi i valori al grafico
    if overlap:
        for i, y_list in enumerate(y):
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y_list,
                    mode="lines+markers",
                    name=f"{
                        name_trace[i]}",
                )
            )
    else:
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=f"{name_trace}"))
    # Imposta le etichette degli assi e il titolo
    fig.update_layout(
        title=f"{name_graph}",
        xaxis_title="",
        yaxis_title="",
        legend_title="Legenda",
        hovermode="x",
    )
    fig.show()
    return fig


def create_subplot(x, y, y1, name_graph, name_trace, name_trace1, overlap, n_graphs):
    # Creazione di un oggetto subplots
    subplots = sp.make_subplots(rows=1, cols=n_graphs)

    # Aggiungi i valori al grafico
    if overlap:
        for i, y_list in enumerate(y):
            subplots.add_trace(
                go.Scatter(
                    x=x,
                    y=y_list,
                    mode="lines+markers",
                    name=f"{
                        name_trace[i]}",
                ),
                row=1,
                col=1,
            )
        for k, y1_list in enumerate(y1):
            subplots.add_trace(
                go.Scatter(
                    x=x,
                    y=y1_list,
                    mode="lines+markers",
                    name=f"{
                        name_trace1[k]}",
                ),
                row=1,
                col=2,
            )
    else:
        subplots.add_trace(
            go.Scatter(x=x, y=y, mode="lines+markers", name=f"{name_trace}"),
            row=1,
            col=1,
        )

    # Imposta le etichette degli assi e il titolo
    subplots.update_layout(
        title=f"{name_graph}",
        xaxis_title="",
        yaxis_title="",
        legend_title="Legenda",
        hovermode="x",
    )

    # Mostra il grafico
    subplots.show()

    return subplots


def reddito_annuo(reference_year, reference_month, path, scaling_factor):
    date_list_annuo = pd.date_range(
        start=f"{
            reference_year - 1}-{reference_month}",
        end=f"{reference_year}-{reference_month}",
        freq="MS",
    )
    reddito_collect, number_months = collect_data_from_list_csv(
        path,
        file_name="Reddito",
        wanted_regexp="Stipendio",
        scaling_factor=scaling_factor,
    )
    initial_date_record = pd.to_datetime("2021-09-01")
    start_date = pd.to_datetime(f"{reference_year}-{reference_month}")
    reddito_annuo_result = 0.0
    try:
        if initial_date_record <= start_date:
            delta = start_date - initial_date_record
            delta_in_months = delta.days / (
                30
                if reference_year % 4 == 0
                and (reference_year % 100 != 0 or reference_year % 400 == 0)
                else 31
            )
            delta_in_months_rounded = (
                math.floor(delta_in_months + 0.5)
                if delta_in_months % 1 >= 0.5
                else math.ceil(delta_in_months - 0.5)
                if delta_in_months % 1 < 0.5
                else delta_in_months
            )
    except ValueError:
        print(f"Impossibile accedere a {reddito_collect} in float.")
    if delta_in_months_rounded <= 12:
        for i in range(delta_in_months_rounded):
            reddito_annuo_result += reddito_collect[i]
    else:
        for i in range(delta_in_months_rounded - 12, delta_in_months_rounded):
            reddito_annuo_result += reddito_collect[i]
    return reddito_annuo_result


def numero_anni(number_samples):
    numero_anni = number_samples // 12
    return numero_anni


def reddito_annuo_totale(number_samples, scaling_factor):
    numero_anni_osservati = numero_anni(number_samples=number_samples)
    reddito_diviso_per_anni = []
    growth_rate = []
    average_growth_rate = []
    start_ref_year = 2022
    ref_month = 9
    date_list = pd.date_range(
        start=f"{start_ref_year}-{ref_month}",
        end=f"{
            start_ref_year - 1 + numero_anni_osservati}-{ref_month}",
        freq="MS",
    )
    date_anni = {date_list[0], date_list[-1]}
    date_anni = pd.DatetimeIndex(date_anni)
    for i in range(numero_anni_osservati):
        redd_obs_year = reddito_annuo(
            reference_year=start_ref_year + i,
            reference_month=ref_month,
            path=path,
            scaling_factor=scaling_factor,
        )
        reddito_diviso_per_anni = np.append(reddito_diviso_per_anni, redd_obs_year)
    # Calcola la differenza tra ogni valore e il precedente
    diff = np.diff(reddito_diviso_per_anni)
    # Rimuovere l'elemento di posizione 0
    diff = np.squeeze(diff)
    # Calcola il tasso di crescita
    growth_rate = diff / reddito_diviso_per_anni[:-1]
    # Calcola il tasso di crescita medio
    average_growth_rate = np.mean(growth_rate)
    return reddito_diviso_per_anni, growth_rate, average_growth_rate, date_anni


def find_best_model(X, y):
    # Definire il range dei parametri da testare
    param_grid = {
        "polynomialfeatures__degree": [0],  # Gradi polinomiali da testare
        "lasso__alpha": [0.001, 0.01, 0.1, 1, 10, 100],  # Valori di alpha da testare
        # Aggiungi un intervallo più ampio se necessario
    }

    # Creare un pipeline con PolynomialFeatures e Lasso Regression
    pipeline = Pipeline(
        [
            ("polynomialfeatures", PolynomialFeatures()),
            ("lasso", Lasso(max_iter=10000, tol=0.01)),
        ]
    )

    # Utilizzare GridSearchCV per trovare il miglior modello e il grado polinomiale
    grid_search = GridSearchCV(
        pipeline, param_grid, cv=3, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    grid_search.fit(X, y)

    # Il miglior modello trovato dalla ricerca su griglia
    best_model = grid_search.best_estimator_
    best_score = -grid_search.best_score_
    best_params = grid_search.best_params_
    best_degree = best_params["polynomialfeatures__degree"]
    best_alpha = best_params["lasso__alpha"]

    print(f"Best polynomial degree: {best_degree}, Best alpha: {best_alpha}")
    print(f"Best MAE score from GridSearchCV: {best_score}")

    return best_model


def project_future_values(data_collected, months_to_project, inflation_rate):
    # Create a time index for the existing data
    month, year = month_year()
    date_index = pd.date_range(start="2021-09", periods=len(data_collected), freq="MS")
    df = pd.DataFrame(data_collected, index=date_index, columns=["Data_Collected"])

    # Prepare data for non-linear regression
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["Data_Collected"].values

    best_model = find_best_model(X, y)

    best_model.fit(X, y)

    # Create the time index for future months
    future_index = pd.date_range(
        start=df.index[-1] + pd.offsets.MonthBegin(1),
        periods=months_to_project,
        freq="MS",
    )

    # Prepare data for prediction
    X_future = np.arange(len(df), len(df) + months_to_project).reshape(-1, 1)

    # Predict new values
    future_values = best_model.predict(X_future)

    # Calculate the monthly inflation from the annual rate
    monthly_inflation_rate = (1 + inflation_rate) ** (1 / 12) - 1

    # Adjust the predicted values for inflation
    inflation_adjustments = (1 + monthly_inflation_rate) ** np.arange(
        1, months_to_project + 1
    )
    adjusted_future_values = future_values * inflation_adjustments

    # Merge historical data with predictions
    future_df = pd.DataFrame(
        adjusted_future_values, index=future_index, columns=["ProjectedDataCollected"]
    )
    total_index = date_index.append(future_index)
    combined_data = np.concatenate([data_collected, adjusted_future_values])
    result_df = pd.DataFrame(
        combined_data, index=total_index, columns=["Data_Combined"]
    )

    return future_df, result_df, total_index


def project_future_values_w_montecarlo(
    data_collected, months_to_project, inflation_rate, num_simulations
):
    # Calcolare la variazione percentuale mensile storica
    monthly_changes = np.diff(data_collected) / data_collected[:-1]

    date_index = pd.date_range(start="2021-09", periods=len(data_collected), freq="MS")
    df = pd.DataFrame(data_collected, index=date_index, columns=["Data_Collected"])
    # Create the time index for future months
    future_index = pd.date_range(
        start=df.index[-1] + pd.offsets.MonthBegin(1),
        periods=months_to_project,
        freq="MS",
    )
    total_index = date_index.append(future_index)

    # Calcolare la media e la deviazione standard del cambiamento percentuale
    avg_change = np.mean(monthly_changes)
    std_change = np.std(monthly_changes)

    # Creare un DataFrame per raccogliere tutte le simulazioni
    all_simulations = pd.DataFrame()

    for simulation in range(num_simulations):
        # Lista per raccogliere i valori simulati
        simulated_values = [data_collected[-1]]  # Inizia dall'ultimo valore noto

        for _ in range(months_to_project):
            # Assumere che i cambiamenti mensili siano distribuiti normalmente attorno alla media storica
            simulated_change = np.random.normal(avg_change, std_change)
            simulated_value = (
                simulated_values[-1]
                * (1 + simulated_change)
                * (1 + inflation_rate / 12)
            )
            simulated_values.append(simulated_value)

        # Aggiungere la simulazione al DataFrame
        all_simulations[simulation] = simulated_values[
            1:
        ]  # Escludere il primo valore che è solo il punto di partenza

    # Calcolare un valore atteso come la media su tutte le simulazioni
    expected_values = all_simulations.mean(axis=1)
    # Calcolare un intervallo di confidenza (ad esempio, il 95%)
    ci_lower = all_simulations.quantile(0.025, axis=1)
    ci_upper = all_simulations.quantile(0.975, axis=1)

    # Costruire un DataFrame con il valore atteso e gli intervalli di confidenza
    future_df = pd.DataFrame(
        {
            "ProjectedDataCollected": expected_values,
            "CILower": ci_lower,
            "CIUpper": ci_upper,
        }
    )

    combined_data = np.concatenate([data_collected, expected_values])
    result_df = pd.DataFrame(
        combined_data, index=total_index, columns=["Data_Combined"]
    )
    future_df.set_index(future_index, inplace=True)

    return future_df, result_df, total_index


# Time Informations
month, year = month_year()

# Crea una lista di date dal settembre 2021 fino al mese e all'anno correnti
date_list = pd.date_range(start="2021-09", end=f"{year}-{month}", freq="MS")

##########################################################################
############################ ESTRAZIONE DATI DA CSV ######################
risparmio_netto_collect, number_months = collect_data_from_list_csv(
    path, file_name="Netto", wanted_regexp="Reddito meno spese", scaling_factor=1
)
reddito_collect, number_months = collect_data_from_list_csv(
    path, file_name="Reddito", wanted_regexp="Reddito totale", scaling_factor=1
)
reddito_only_ifx, number_months = collect_data_from_list_csv(
    path, file_name="Reddito", wanted_regexp="Stipendio", scaling_factor=1
)
spese_collect, number_months = collect_data_from_list_csv(
    path, file_name="Spese", wanted_regexp="Spese totali", scaling_factor=1
)
investment_collect, number_months = collect_data_from_list_csv(
    path, file_name="Spese", wanted_regexp="Investimenti", scaling_factor=1
)
costo_casa_collect, number_months = collect_data_from_list_csv(
    path,
    file_name="Spese",
    wanted_regexp="Immobili (affitto, mutuo, tasse, assicurazione)",
    scaling_factor=1,
)
spese_straordinarie_collect, number_months = collect_data_from_list_csv(
    path, file_name="Spese", wanted_regexp="Spese Straordinarie", scaling_factor=1
)
##########################################################################
##########################################################################
########################## CALCOLI SU DATI ESTRATTI DA CSV ###############
risparmio_netto_avg_values = dynamic_avg(values=risparmio_netto_collect)
reddito_avg_values = dynamic_avg(values=reddito_collect)
reddito_only_ifx_avg_values = dynamic_avg(values=reddito_only_ifx)
ratio_stipendio_reddito = dynamic_avg(reddito_only_ifx_avg_values / reddito_avg_values)
reddito_total_list, reddito_total = sum(reddito_collect)
reddito_diviso_per_anni, growth_rate, average_growth_rate, observed_years = (
    reddito_annuo_totale(number_months, scaling_factor=1)
)
investment_collect_avg_values = dynamic_avg(values=investment_collect)
investement_total_list, investment_total = sum(investment_collect)
risparmio_invest_liquid_total_list, risparmio_invest_liquid_total = sum(
    investment_collect + risparmio_netto_collect
)
risparmio_invest_liquid_avg_values = dynamic_avg(risparmio_invest_liquid_total_list)
risparmio_total_list, risparmio_total = sum(risparmio_netto_collect)
risparmio_total_avg_values = dynamic_avg(risparmio_total_list)
spese_nette_values = spese_collect - investment_collect
spese_nette_total_list, spese_nette_total_value = sum(spese_nette_values)
spese_nette_avg_values = dynamic_avg(spese_nette_values)
spese_straordinarie_collect_avg_values = dynamic_avg(spese_straordinarie_collect)
costo_casa_avg_values = dynamic_avg(costo_casa_collect)
##################################################################
##################################################################
# Simulazione
inflation_rate = 0.05  # % di inflazione annuale
inflation_rate_salary = 0.025  # scala mobile stipendio
inflation_rate_avg_reddito = ratio_stipendio_reddito[-1] * inflation_rate_salary
new_house = 1  # Switch Cambio Casa
if new_house == 0:
    ratio_new_old_apartment = 1
else:
    ratio_new_old_apartment = 1291.54 / 791.84
inflation_rate_casa = 0.02
months_to_project = 36  # Simulazione su N mesi
# Scaling Factor Spese Straordinarie --> 0.2 = -20% , 0.7 = -70% ...
scaling_factor_spese_straordinarie = 0.1
################# VALORI PREDETTI ##############################
(
    costo_casa_predicted_values_montecarlo,
    costo_casa_hystory_values_montecarlo,
    date_index_project_montecarlo,
) = project_future_values_w_montecarlo(
    costo_casa_collect, months_to_project, inflation_rate_casa, 1000
)
costo_casa_predicted_values, costo_casa_hystory_values, date_index_project = (
    project_future_values(
        costo_casa_collect,
        months_to_project,
        inflation_rate_casa,
    )
)
reddito_predicted_values, reddito_hystory_values, date_index_project = (
    project_future_values(
        reddito_avg_values,
        months_to_project,
        inflation_rate_avg_reddito,
    )
)
stipendio_predicted_values, stipendio_hystory_values, date_index_project = (
    project_future_values(
        reddito_only_ifx_avg_values,
        months_to_project,
        inflation_rate_salary,
    )
)
investment_predicted_values, investment_hystory_values, date_index_project = (
    project_future_values(
        investment_collect_avg_values,
        months_to_project,
        0.01,
    )
)
spese_nette_da_predire = spese_nette_avg_values - (
    spese_straordinarie_collect_avg_values * scaling_factor_spese_straordinarie
)
spese_nette_predicted_values, spese_nette_hystory_values, date_index_project = (
    project_future_values(
        spese_nette_da_predire,
        months_to_project,
        inflation_rate,
    )
)
##################################################################
############### CALCOLI PERCENTUALI SU VALORI MEDI #######################
costo_casa_perct_avg_values = dynamic_avg(
    (costo_casa_avg_values / reddito_avg_values) * 100
)
investement_total_perct_avg_values = dynamic_avg(
    (investment_collect_avg_values / reddito_avg_values) * 100
)
spese_nette_perct_avg_values = dynamic_avg(
    (spese_nette_avg_values / reddito_avg_values) * 100
)
risparmio_no_invest_perct_avg_values = dynamic_avg(
    100 - (spese_nette_perct_avg_values + investement_total_perct_avg_values)
)
risparmio_no_invest_mensile_perct_avg_values = dynamic_avg(
    risparmio_no_invest_perct_avg_values
)
risparmio_global_perct_avg_values = dynamic_avg(100 - (spese_nette_perct_avg_values))
############# CALCOLI PERCENTUALI SU VALORI PUNTUALI MEDIATI #########
costo_casa_perct_values = dynamic_avg((costo_casa_collect / reddito_collect) * 100)
investement_total_perct_values = dynamic_avg(
    (investment_collect / reddito_collect) * 100
)
spese_nette_perct_values = dynamic_avg((spese_nette_values / reddito_collect) * 100)
risparmio_no_invest_perct_values = dynamic_avg(
    100 - (spese_nette_perct_values + investement_total_perct_values)
)
################ CALCOLI PERCENTUALI PREDETTI ######################
reddito_predicted_collect = reddito_hystory_values["Data_Combined"].values
reddito_predicted_avg_values = dynamic_avg(reddito_predicted_collect)
reddito_predicted_total_values = sum(reddito_predicted_collect)
stipendio_predicted_collect = stipendio_hystory_values["Data_Combined"].values
stipendio_predicted_avg_values = dynamic_avg(stipendio_predicted_collect)
stipendio_predicted_total_values = sum(stipendio_predicted_collect)
costo_casa_hystory_values[date_list.size :] *= ratio_new_old_apartment
costo_casa_predicted_collect = costo_casa_hystory_values["Data_Combined"].values
costo_casa_predicted_avg_values = dynamic_avg(costo_casa_predicted_collect)
costo_casa_predicted_total_values = sum(costo_casa_predicted_collect)
investment_predicted_collect = investment_hystory_values["Data_Combined"].values
investment_predicted_avg_values = dynamic_avg(investment_predicted_collect)
investment_predicted_total_values = sum(investment_predicted_collect)
spese_nette_predicted_collect = spese_nette_hystory_values["Data_Combined"].values
spese_nette_predicted_avg_values = dynamic_avg(spese_nette_predicted_collect)
spese_nette_predicted_total_values = sum(spese_nette_predicted_collect)
############### CALCOLI PERCENTUALI SU VALORI MEDI #######################
costo_casa_predicted_perct_avg_values = dynamic_avg(
    (costo_casa_predicted_avg_values / reddito_predicted_avg_values) * 100
)
investment_predicted_perct_avg_values = dynamic_avg(
    (investment_predicted_avg_values / reddito_predicted_avg_values) * 100
)
spese_nette_predicted_perct_avg_values = dynamic_avg(
    (spese_nette_predicted_avg_values / reddito_predicted_avg_values) * 100
)
risparmio_predicted_no_invest_perct_avg_values = dynamic_avg(
    100
    - (spese_nette_predicted_perct_avg_values + investment_predicted_perct_avg_values)
)
risparmio_global_predicted_perct_avg_values = dynamic_avg(
    100 - (spese_nette_predicted_perct_avg_values)
)
############# CALCOLI PERCENTUALI SU VALORI PUNTUALI MEDIATI #########
costo_casa_predicted_perct_values = (
    costo_casa_predicted_collect / reddito_predicted_collect
) * 100
investment_predicted_perct_values = (
    investment_predicted_collect / reddito_predicted_collect
) * 100
spese_nette_predicted_perct_values = (
    spese_nette_predicted_collect / reddito_predicted_collect
) * 100
risparmio_predicted_no_invest_perct_values = 100 - (
    spese_nette_predicted_perct_values + investment_predicted_perct_values
)
risparmio_global_predicted_perct_values = 100 - (spese_nette_predicted_perct_values)

####################################################################
##########################################################################
##########################################################################
###################### GRAFICI ###########################################
##########################################################################
##### RISPARMIO ######
# y_list_fig          = [risparmio_netto_collect,risparmio_netto_avg_values]
# name_trace_list_fig = ['Risparmio Netto','Risparmio Netto Medio']
# n_traces_fig        = 2
# fig  = create_plot(x=date_list,y=y_list_fig,name_graph='Grafico Risparmio',name_trace=name_trace_list_fig,overlap = 1,n_traces= n_traces_fig)
# ##### REDDITO   ######
# y_list_fig1          = [reddito_collect,reddito_avg_values]
# name_trace_list_fig1 = ['Reddito Percepito','Reddito Medio']
# n_traces_fig1        = 2
# fig1 = create_plot(x=date_list,y=y_list_fig1,name_graph='Reddito Totale',name_trace=name_trace_list_fig1,overlap = 1,n_traces= n_traces_fig1)
# ##### GROWTH RATE ####
# y_list_fig2          = [reddito_diviso_per_anni,growth_rate]
# name_trace_list_fig2 = ['Reddito annuo','Grothw_rate']
# n_traces_fig2        = 2
# fig2 = create_plot(x=observed_years,y=y_list_fig2,name_graph='Reddito annuo',name_trace=name_trace_list_fig2,overlap = 1,n_traces= n_traces_fig2)
# ##### SPESE MENSILI ##
# y_list_fig3          = [spese_collect,spese_nette_avg_values]
# name_trace_list_fig3 = ['Spese Mensili','Spese Medie Mensili']
# n_traces_fig3        = 2
# fig3 = create_plot(x=date_list,y=y_list_fig3,name_graph='Spese per mese',name_trace=name_trace_list_fig3,overlap = 1,n_traces= n_traces_fig3)
# ##### SPESE - INVESTIMENTI ##
# y_list_fig4          = [spese_nette_values,spese_nette_avg_values]
# name_trace_list_fig4 = ['Spese - Investimenti Mensili','Spese - Investimenti Medi']
# n_traces_fig4        = 2
# fig4                 = create_plot(x=date_list,y=y_list_fig4,name_graph='Spese - Investimenti',name_trace=name_trace_list_fig4,overlap = 1,n_traces= n_traces_fig4)
##### CONFRONTI REDDITO, INVESTIMENTI, RISPARMIO ###
y_list_fig5 = [
    investment_collect_avg_values,
    risparmio_total_avg_values,
    reddito_avg_values,
    investement_total_list,
    risparmio_total_list,
    reddito_total_list,
    spese_nette_total_list,
    risparmio_netto_collect,
    risparmio_invest_liquid_total_list,
]
name_trace_list_fig5 = [
    "Investimenti Mensili Medi",
    "Risparmio Accumulato Medio (Liquidita')",
    "Reddito Mensile Mensile",
    "Investimenti Totali",
    "Risparmio Accumulato (Liquidita')",
    "Reddito Totale",
    "Spese Totali senza Investimenti",
    "Risparmio Mensile senza Investimenti (Liquidita')",
    "Risparmio Liquidita' + Investimenti Mensile",
]
n_traces_fig5 = 8
fig5 = create_plot(
    x=date_list,
    y=y_list_fig5,
    name_graph="Investimenti vs Risparmio vs Reddito Medio",
    name_trace=name_trace_list_fig5,
    overlap=1,
    n_traces=n_traces_fig5,
)
#### CONFRONTI REDDITO, INVESTIMENTI, RISPARMIO PERCENTUALI ###
y_list_fig6 = [
    investement_total_perct_avg_values,
    risparmio_no_invest_perct_avg_values,
    spese_nette_perct_avg_values,
    risparmio_global_perct_avg_values,
    costo_casa_perct_avg_values,
]
name_trace_list_fig6 = [
    "Investimenti/Reddito Percentuali AVG Mensili",
    "Risparmio(senza Investimenti)/Reddito Percentuali Accumulato AVG Mensili",
    "Spese Nette/Reddito Percentuali AVG Mensili",
    "Risparmio Globale Percentuali AVG Mensili",
    "Costo Casa AVG Percentuali Mensili",
]
name_trace1_list_fig6 = [
    "Investimenti/Reddito Percentuali Mensili",
    "Risparmio(senza Investimenti)/Reddito Percentuali Accumulato Mensili",
    "Spese Nette/Reddito Percentuali Mensili",
]
y1_list_fig6 = [
    investement_total_perct_values,
    risparmio_no_invest_perct_values,
    spese_nette_perct_values,
]
n_traces_fig6 = 5
n_graphs_fig6 = 2
spese_nette_mensile_perct_avg_values_round = "{:.2f}".format(
    spese_nette_perct_avg_values[-1]
)
risparmio_mensile_perct_avg_values_round = "{:.2f}".format(
    risparmio_no_invest_mensile_perct_avg_values[-1]
)
investement_total_perct_avg_values_round = "{:.2f}".format(
    investement_total_perct_avg_values[-1]
)
reddito_medio_avg_values_round = "{:.2f}".format(reddito_avg_values[-1])
stipendio_medio_avg_values_round = "{:.2f}".format(reddito_only_ifx_avg_values[-1])
name_graph_fig6 = f"Spese Nette {spese_nette_mensile_perct_avg_values_round}% vs Investimenti {investement_total_perct_avg_values_round}% vs Risparmio (no Investimenti) {
    risparmio_mensile_perct_avg_values_round}%  ---- Reddito Medio € {reddito_medio_avg_values_round}, Stipendio Medio € {stipendio_medio_avg_values_round}"
fig6_sub = create_subplot(
    x=date_list,
    y=y_list_fig6,
    y1=y1_list_fig6,
    name_graph=name_graph_fig6,
    name_trace=name_trace_list_fig6,
    name_trace1=name_trace1_list_fig6,
    overlap=1,
    n_graphs=n_graphs_fig6,
)


# CONFRONTI PROIEZIONI FUTURE REDDITO, INVESTIMENTI, RISPARMIO PERCENTUALI
# ###   IMPLEMENTARE MODO PER POTER FARE N SUBPLOT IN MANIERA SEMPLICE FIXME!!!!!
y_list_fig7 = [
    investment_predicted_perct_avg_values,
    risparmio_predicted_no_invest_perct_avg_values,
    spese_nette_predicted_perct_avg_values,
    risparmio_global_predicted_perct_avg_values,
    costo_casa_predicted_perct_avg_values,
]
name_trace_list_fig7 = [
    "Investimenti/Reddito Percentuali AVG Mensili",
    "Risparmio(senza Investimenti)/Reddito Percentuali Accumulato AVG Mensili",
    "Spese Nette/Reddito Percentuali AVG Mensili",
    "Risparmio Globale Percentuali AVG Mensili",
    "Costo Casa AVG Percentuali Mensili",
]
name_trace1_list_fig7 = [
    "Investimenti/Reddito Percentuali Mensili",
    "Risparmio(senza Investimenti)/Reddito Percentuali Accumulato Mensili",
    "Spese Nette/Reddito Percentuali Mensili",
    "Risparmio Globale Percentuali Mensili",
    "Costo Casa Percentuali Mensili",
]
y1_list_fig7 = [
    investment_predicted_perct_values,
    risparmio_predicted_no_invest_perct_values,
    spese_nette_predicted_perct_values,
    risparmio_global_predicted_perct_values,
    costo_casa_predicted_perct_values,
]
n_traces_fig7 = 5
n_graphs_fig7 = 2
spese_nette_predicted_perct_avg_values_round = "{:.2f}".format(
    spese_nette_predicted_perct_avg_values[-1]
)
risparmio_mensile_predicted_perct_avg_values_round = "{:.2f}".format(
    risparmio_predicted_no_invest_perct_avg_values[-1]
)
investement_total_predicted_perct_avg_values_round = "{:.2f}".format(
    investment_predicted_perct_avg_values[-1]
)
reddito_medio_predicted_avg_values_round = "{:.2f}".format(
    reddito_predicted_collect[-1]
)
stipendio_medio_predicted_avg_values_round = "{:.2f}".format(
    stipendio_predicted_collect[-1]
)
name_graph_fig7 = f"PROIEZIONE DATI SU {months_to_project} MESI  ---- Spese Nette {spese_nette_predicted_perct_avg_values_round}% vs Investimenti {investement_total_predicted_perct_avg_values_round}% vs Risparmio (no Investimenti) {
    risparmio_mensile_predicted_perct_avg_values_round}%  ---- Reddito Medio € {reddito_medio_predicted_avg_values_round}, Stipendio Medio € {stipendio_medio_predicted_avg_values_round}"
fig7_sub = create_subplot(
    x=date_index_project,
    y=y_list_fig7,
    y1=y1_list_fig7,
    name_graph=name_graph_fig7,
    name_trace=name_trace_list_fig7,
    name_trace1=name_trace1_list_fig7,
    overlap=1,
    n_graphs=n_graphs_fig7,
)
