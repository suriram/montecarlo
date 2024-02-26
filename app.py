from pathlib import Path
import uuid
import pyodbc
import dash_uploader as du
import dash
from dash import dcc, html, Input, Output, State, dash_table
from tempfile import NamedTemporaryFile
import base64
import os
from dash.exceptions import PreventUpdate
from flask import request
import pandas as pd
import random
import plotly_express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.MINTY],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

UPLOAD_FOLDER_ROOT = r"C:\Users\mariu\PycharmProjects\Monte carlo Sim Effekt\.venv\Uploads"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)
filnavn=[]
load_figure_template('minty')
# uploads = os.listdir(r"C:\Users\mariu\PycharmProjects\Monte carlo Sim Effekt\.venv\Uploads")

# Gjennomsnitt og std
mu = 1
Sigma = 0.2

def get_upload_component(id):
    return du.Upload(
        id=id,
        text='Slipp filen her eller trykk for å laste opp EFFEKT base',
        text_completed='Lastet opp: ',
        cancel_button=True,
        max_files=1,
        max_file_size=20000,  # 20000 Mb
        filetypes=['MDB'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


def get_app_layout():

    return dbc.Container([
        html.Div(
        [
            html.Div(
                [
                    html.Div(id='callback-output', className='m-5'),
                    dbc.Row([dbc.Col(get_upload_component(id='dash-uploader'),className='m-5')]),
                ]),
        ],
        style={
            'textAlign': 'center',
        },
    )])


# get_app_layout is a function
# This way we can use unique session id's as upload_id's
app.layout = get_app_layout


@du.callback(
    output=Output("callback-output", "children"),
    )
# def callback_on_completion(status: du.UploadStatus):
# #     return str(status.uploaded_files[0])

def callback_on_completion(status: du.UploadStatus):
    simulations = []
    Sti = status.uploaded_files[0]
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                r'DBQ=%s;' % Sti)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    query = "SELECT * FROM TotKostPlanlagt;"  # trafikk, anleggskostnader, ulykker, D&V, Sjekk ut Concept. begrens deg til store verdier, en tabell med anbefalte fordelinger.
    # query2 = "SELECT * FROM Lenke"
    cursor.execute(query)
    data = cursor.fetchall()
    # query = "SELECT * FROM TotKostPlanlagt;"
    sql2 = "SELECT * FROM TotKostAlt0"
    sql3 = "SELECT * FROM Prosjekt"

    # Behandling av data fra access
    Tiltak = pd.read_sql_query(query, conn)
    Referanse = pd.read_sql_query(sql2, conn)
    Prosjekt = pd.read_sql_query(sql3, conn)
    Navn = Prosjekt.iat[0, 1]
    Kalkrente = Prosjekt.iat[0, 3]
    Prisnivå = Prosjekt.iat[0, 4]
    Sammenligningsår = Prosjekt.iat[0, 5]
    Levetid = Prosjekt.iat[0, 6]
    Ansvarlig = Prosjekt.iat[0, 45]

    conn.close()

    Alt = Tiltak['Alternativ'].unique()
    Plan = Tiltak['PlanNr'].unique()

    Referanse.År = Referanse.År.astype('int32')
    Referanse.År = pd.to_datetime(Referanse.År, format='%Y')
    Referanse.set_index('År', inplace=True)
    Tiltak.År = Tiltak.År.astype('int32')
    Tiltak.År = pd.to_datetime(Tiltak.År, format='%Y')
    Tiltak.set_index('År', inplace=True)

    # gruppering av data
    Referanse = Referanse.query('Alternativ ==0')
    Tiltak1 = Tiltak.query('Alternativ ==0')
    Referansekostnader = Referanse.iloc[:, 3:24].fillna(0)
    Tiltakskostnader = Tiltak.iloc[:, 3:23].fillna(0)

    TrafnytteTil = Tiltakskostnader['Trafikantnytte'].sum()
    DogVTil = Tiltakskostnader['Drift_vedlikehold'].sum()
    UlykkerTil = Tiltakskostnader['Ulykker'].sum()
    Investring = Tiltakskostnader['Investeringer'].sum()
    DogVRef = Referansekostnader['Drift_vedlikehold'].sum()
    UlykkerRef = Referansekostnader['Ulykker'].sum()
    TiltakNytte = (Tiltakskostnader['Kjøretøykostnader'] + Tiltakskostnader['Direkteutgifter'] + Tiltakskostnader[
        'Tidskostnader'] + Tiltakskostnader['Nyskapt'] + Tiltakskostnader['Ulempeskostnader'] + Tiltakskostnader[
                       'Helsevirkninger'] + Tiltakskostnader['Utrygghetskostnader'] + Tiltakskostnader[
                       'Operatørkostnader'] + Tiltakskostnader['Operatøroverføringer'] + Tiltakskostnader[
                       'Offentlige_overføringer'] + Tiltakskostnader['Skatte_avgiftsinntekter'] + Tiltakskostnader[
                       'Støy_luft'] + Tiltakskostnader['Andre_kostnader'] + Tiltakskostnader['Restverdi'] +
                   Tiltakskostnader['Skattekostnad']).sum()
    ReferanseNytte = (
                Referansekostnader['Kjøretøykostnader'] + Referansekostnader['Direkteutgifter'] + Referansekostnader[
            'Tidskostnader'] + Referansekostnader['Nyskapt'] + Referansekostnader['Ulempeskostnader'] +
                Referansekostnader['Helsevirkninger'] + Referansekostnader['Utrygghetskostnader'] + Referansekostnader[
                    'Operatørkostnader'] + Referansekostnader['Operatøroverføringer'] + Referansekostnader[
                    'Offentlige_overføringer'] + Referansekostnader['Skatte_avgiftsinntekter'] + Referansekostnader[
                    'Støy_luft'] + Referansekostnader['Andre_kostnader'] + Referansekostnader['Skattekostnad']).sum()
    diff = TiltakNytte - ReferanseNytte
    for _ in range(20000):
        x = random.normalvariate(mu, Sigma)
        y = random.normalvariate(mu, Sigma)
        z = random.normalvariate(mu, Sigma)
        a = random.normalvariate(mu, Sigma)
        Sim = TrafnytteTil * x + (DogVTil - DogVRef) * y + (UlykkerTil - UlykkerRef) * z + Investring * a + diff
        # simulation_result = np.mean(Sim)
        simulations.append(Sim)
    simulations = pd.Series(simulations, name='Netto nytte')
    fig1 = px.histogram(simulations, marginal='box')
    fig1.update_layout(
        xaxis_title='%s Kroner' % Prisnivå,
        yaxis_title='Antall',
        legend_title=''

    )

    fig3 = px.ecdf(simulations, marginal='box')
    fig3.update_layout(
        xaxis_title='%s Kroner' % Prisnivå,
        yaxis_title='Sannsynlighet',
        legend_title=''
    )

    # fig2 = go.Figure(data=[go.Histogram(x=simulations, cumulative_enabled=True)])

    def format_with_space(number):
        return '{:,.0f}'.format(number).replace(',', ' ')

    testi = pd.Series(simulations, name='Netto nytte')
    std = testi.std().round(1)
    std = format_with_space(std)
    mean = testi.mean().round(1)
    mean = format_with_space(mean)
    return html.Div(children=[html.H1("Monte Carlo simulering %s" % Navn, className="text-header, mb-4"),
    html.Div(children='Simuleringen varierer trafikantnytten, drift og vedlikehold, investeringskostnader og ulykkeskostnader. Alle variasjonene er normalfordelt med et standardavvik på 20 prosent', className="text-body, mb-4"),
    html.Div(children="%s har en analyseperiode på %s år. Prisnivået er %s og det er benyttet en kalkulasjonsrente på %s prosent. Gjennomsnittsverdien i fordelingen er: %s. Utvalget har et standardavvik på %s. Ansvarlig for EFFEKTbasen er %s." % (Navn,Levetid,Prisnivå,Kalkrente,mean, std, Ansvarlig), className="text-body,mb-4"),
    # html.Div([
    #         dcc.Dropdown(
    #             df1['PlanNr'].unique(),
    #             'Valgt utbyggingsplan i EFFEKT',
    #             id='xaxis-column'
    #         )]),
    dcc.Graph(figure=fig1),
    html.Div(children="Kumulativ fordeling vises nedenfor : ", className="text-body, mb-4"),
    dcc.Graph(figure=fig3)])


if __name__ == '__main__':
    app.run_server(debug=True)
