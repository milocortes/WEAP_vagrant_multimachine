# -*- coding: utf-8 -*-
"""
Created on Mon May 16 11:47:36 2022

@author: Kiara Tesen
"""
import win32com.client as win32
import pandas as pd
import time
import os
import sys

from flopy.utils.zonbud import ZoneBudget, read_zbarray
from datetime import datetime as dt
import glob

import numpy as np
import matplotlib.pyplot as plt

import socket
import yaml


# Cargamos los parametros iniciales
with open(r'weap_config.yaml') as file:
    weap_config = yaml.load(file, Loader=yaml.FullLoader)


'''
Define funciones
'''
def get_scenario(temp):
    return temp[-15:-12]

def get_date(temp):
    temp1 = '1_' + temp[-11:-4]
    temp2 = dt.strptime(temp1, '%d_%Y_%W')
    return temp2 - pd.DateOffset(months=diferencia_TS)

def get_TS(directorio, zone_analysis, output):
    new_df = pd.DataFrame()
    os.chdir(directorio)
    for file in glob.glob('*.csv'):
        df = pd.read_csv(file)
        melted = df.melt(id_vars=['name'], value_vars=zones)
        wk2 = melted.loc[melted['variable'] == zone_analysis]
        wk2 = wk2.drop(['variable'], axis=1)
        wk2 = wk2.T
        wk2['name_file'] = file
        new_df = pd.concat([wk2, new_df])
        #os.remove(file)

    new_df.columns = new_df.iloc[0]
    new_df = new_df.drop(['name'], axis=0)
    column_list = list(new_df.columns.values)
    last_name = column_list[-1]
    new_df.rename(columns={last_name: 'file'}, inplace=True)
    new_df['Scenario'] = new_df.apply(lambda x: get_scenario(x['file']), axis=1)
    new_df['date'] = new_df.apply(lambda x: get_date(x['file']), axis=1)
    new_df.set_index('date', inplace=True)
    new_df = new_df.sort_values(['date'],ascending=True)
    new_df.drop(['file'], axis=1, inplace=True)
    dir_out = output + '/' + zone_analysis + '.csv'
    new_df.to_csv(dir_out)

def get_full_balance(path_balance, path_ZB, dir_exit):
    zonefile = read_zbarray(path_ZB)  # Archivo con zonas
    # Leer binarios de la carpeta WEAP
    for file in os.listdir(path_balance):
        filename = os.fsdecode(file)
        if filename.endswith(".ccf"):
            t = path_balance + '/' + filename[:-4] + '.csv'
            zb = ZoneBudget(path_balance + '\\' + filename, zonefile, aliases=aliases)
            zb.to_csv(t)

    for zone in zones:
        get_TS(path_balance, zone, dir_exit)

    filelist = [ f for f in os.listdir(path_balance) if f.endswith(".csv") ]
    for f in filelist:
        os.remove(os.path.join(path_balance, f))

'''
Carga modelo
'''

WEAP = win32.Dispatch("WEAP.WEAPApplication")

WEAP.ActiveArea = "Ligua_Petorca_WEAP_MODFLOW_RDM"
WEAP.BaseYear = 1979
WEAP.EndYear = 1991

Var_escenarios = pd.read_excel(weap_config["paths"]["src_path"] + '/EscenarioEjecucion_v2.xlsx')

WEAP.ActiveScenario = WEAP.Scenarios("Reference")

experimento = int(sys.argv[1])

t_1 = time.time()
print('Escenario en ejecución: ', Var_escenarios.iloc[experimento+1,0], ' - Delta_P: ', Var_escenarios.iloc[experimento+1,71], ' - Delta_T: ', Var_escenarios.iloc[experimento+1,72])

# Planta de desalación
WEAP.BranchVariable('\Supply and Resources\Other Supply\Planta de desalacion:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,1]
WEAP.BranchVariable('\Supply and Resources\Other Supply\Planta de desalacion:Inflow').Expression = '1'*Var_escenarios.iloc[experimento+1,2]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion Agua desalinizada rio petorca:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,3]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion Agua desalinizada rio petorca\Flow Requirements\FR_conduccion rio petorca:Minimum Flow Requirement').Expression = '1'*Var_escenarios.iloc[experimento+1,4]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion Agua desalinizada rio petorca\Flow Requirements\FR_conduccion rio petorca:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,5]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion agua desalinizada rio La Ligua:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,6]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion agua desalinizada rio La Ligua\Flow Requirements\FR_Conduccion rio La Ligua:Minimum Flow Requirement').Expression = '1'*Var_escenarios.iloc[experimento+1,7]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion agua desalinizada rio La Ligua\Flow Requirements\FR_Conduccion rio La Ligua:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,8]

# Carretera hídrica
WEAP.BranchVariable('\Supply and Resources\Other Supply\Caudal carretera hidrica a Estero Alicahue:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,9]
WEAP.BranchVariable('\Supply and Resources\Other Supply\Caudal carretera hidrica a Estero Alicahue:Inflow').Expression = '2.87/2'*Var_escenarios.iloc[experimento+1,10]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion Ligua_carretera hidrica:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,11]
WEAP.BranchVariable('\Supply and Resources\Other Supply\Caudal Carretera Hidrica a rio Petorca:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,12]
WEAP.BranchVariable('\Supply and Resources\Other Supply\Caudal Carretera Hidrica a rio Petorca:Inflow').Expression = '2.87/2'*Var_escenarios.iloc[experimento+1,13]
WEAP.BranchVariable('\Supply and Resources\River\conduccion Petorca_carretera hidrica:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,14]

# Aducciones
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L01_APRConduccionAlicahue:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,15]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L01_APRConduccionAlicahue:Weekly Demand').Expression = '10*3.6*24*7'*Var_escenarios.iloc[experimento+1,16]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L02_APRConduccionAlicahue:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,17]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L02_APRConduccionAlicahue:Weekly Demand').Expression = '15*3.6*24*7'*Var_escenarios.iloc[experimento+1,18]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L06_APRConduccionAlicahue:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,19]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_L06_APRConduccionAlicahue:Weekly Demand').Expression = '7.3*3.6*24*7'*Var_escenarios.iloc[experimento+1,20]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P02_APRAduccion:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,21]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P02_APRAduccion:Weekly Demand').Expression = '30*3.6*24*7'*Var_escenarios.iloc[experimento+1,22]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P03_APRAduccion:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,23]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P03_APRAduccion\Pozo1:Weekly Demand').Expression = '4*3.6*24*7'*Var_escenarios.iloc[experimento+1,24]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P03_APRAduccion\Pozo2:Weekly Demand').Expression = '4*3.6*24*7'*Var_escenarios.iloc[experimento+1,25]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P03_APRAduccion\Pozo3:Weekly Demand').Expression = '3*3.6*24*7'*Var_escenarios.iloc[experimento+1,26]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P08_APRAduccion:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,27]
WEAP.BranchVariable('\Demand Sites and Catchments\DemOTRAS_P08_APRAduccion:Weekly Demand').Expression = '1*3.6*24*7'*Var_escenarios.iloc[experimento+1,28]
WEAP.BranchVariable('\Supply and Resources\River\Aduccion Hierro Viejo:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,29]
WEAP.BranchVariable('\Supply and Resources\River\Aduccion Hierro Viejo:Maximum Diversion').Expression = '0.041'*Var_escenarios.iloc[experimento+1,30]
WEAP.BranchVariable('\Supply and Resources\River\ImpulsionLongotoma:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,31]
WEAP.BranchVariable('\Supply and Resources\River\ImpulsionLongotoma:Maximum Diversion').Expression = '0.005'*Var_escenarios.iloc[experimento+1,32]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionAlicahue:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,33]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionAlicahue:Maximum Diversion').Expression = '0.05'*Var_escenarios.iloc[experimento+1,34]

# Embalse Las Palmas
WEAP.BranchVariable('\Supply and Resources\River\EsteroLasPalmas\Reservoirs\Embalse_LasPalmas:Startup Year').Expression = Var_escenarios.iloc[experimento+1,35]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseLasPalmas_fict:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,36]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseLasPalmas_fict:Weekly Demand').Expression = '0.0012*PrevTSValue(Supply and Resources\River\EsteroLasPalmas\Reservoirs\Embalse_LasPalmas:Storage Volume[m^3])/1000000+0.0004'*Var_escenarios.iloc[experimento+1,37]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLasPalmas:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,38]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLasPalmas:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,39]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLasPalmas\Flow Requirements\RF_EmbalseLasPalmas:Minimum Flow Requirement').Expression = 'If(TS>27,0.5,0)'*Var_escenarios.iloc[experimento+1,40]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLasPalmas\Flow Requirements\RF_EmbalseLasPalmas:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,41]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Las Palmas:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,42]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Las Palmas:Maximum Diversion').Expression = '2'*Var_escenarios.iloc[experimento+1,43]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Las Palmas\Flow Requirements\FR Canal Embalse Las Palmas:Minimum Flow Requirement').Expression = '2'*Var_escenarios.iloc[experimento+1,44]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Las Palmas\Flow Requirements\FR Canal Embalse Las Palmas:Priority').Expression = '99'*Var_escenarios.iloc[experimento+1,45]

# Embalse Pedernal
WEAP.BranchVariable('\Supply and Resources\River\Petorca\Reservoirs\Embalse Pedernal:Startup Year').Expression = Var_escenarios.iloc[experimento+1,46]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalsePedernal_fict:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,47]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalsePedernal_fict:Weekly Demand').Expression = '0.0012*PrevTSValue(Supply and Resources\River\Petorca\Reservoirs\Embalse Pedernal:Storage Volume[m^3])/1000000+0.0004'*Var_escenarios.iloc[experimento+1,48]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalsePedernal:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,49]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalsePedernal:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,50]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalsePedernal\Flow Requirements\RF_EmbalsePedernal:Minimum Flow Requirement').Expression = 'If(TS>27,0.5,0)'*Var_escenarios.iloc[experimento+1,51]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalsePedernal\Flow Requirements\RF_EmbalsePedernal:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,52]

# Embalse Angeles
WEAP.BranchVariable('\Supply and Resources\River\Estero Los Angeles\Reservoirs\Embalse Los Angeles:Startup Year').Expression = Var_escenarios.iloc[experimento+1,53]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseAngeles_fict:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,54]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseAngeles_fict:Weekly Demand').Expression = '0.0012*PrevTSValue(Supply and Resources\River\Estero Los Angeles\Reservoirs\Embalse Los Angeles:Storage Capacity[Million m^3])/1000000+0.0004'*Var_escenarios.iloc[experimento+1,55]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLosAngeles:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,56]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLosAngeles:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,57]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLosAngeles\Flow Requirements\RF_EmbalseLosAngeles:Minimum Flow Requirement').Expression = 'If(TS>27,0.5,0)'*Var_escenarios.iloc[experimento+1,58]
WEAP.BranchVariable('\Supply and Resources\River\ConduccionEmbalseLosAngeles\Flow Requirements\RF_EmbalseLosAngeles:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,59]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Los Angeles:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,60]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Los Angeles:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,61]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Los Angeles\Flow Requirements\FR Canal Embalse Los Angeles:Minimum Flow Requirement').Expression = '2'*Var_escenarios.iloc[experimento+1,62]
WEAP.BranchVariable('\Supply and Resources\River\Canal Alimentador Embalse Los Angeles\Flow Requirements\FR Canal Embalse Los Angeles:Priority').Expression = '99'*Var_escenarios.iloc[experimento+1,63]

# Embalse La Chupalla
WEAP.BranchVariable('\Supply and Resources\River\Ligua\Reservoirs\Embalse_LaChupalla:Startup Year').Expression = Var_escenarios.iloc[experimento+1,64]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseLaChupalla_fict:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,65]
WEAP.BranchVariable('\Demand Sites and Catchments\DemInfiltracion_EmbalseLaChupalla_fict:Weekly Demand').Expression = '0.01*PrevTSValue(Supply and Resources\River\Ligua\Reservoirs\Embalse_LaChupalla:Storage Volume[m^3])'*Var_escenarios.iloc[experimento+1,66]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion_EmbalseLaChupala:Startup Year').Expression = '1979'*Var_escenarios.iloc[experimento+1,67]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion_EmbalseLaChupala:Maximum Diversion').Expression = '1'*Var_escenarios.iloc[experimento+1,68]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion_EmbalseLaChupala\Flow Requirements\RF_EmbalseLaChupalla:Minimum Flow Requirement').Expression = 'If(TS>27,0.5,0)'*Var_escenarios.iloc[experimento+1,69]
WEAP.BranchVariable('\Supply and Resources\River\Conduccion_EmbalseLaChupala\Flow Requirements\RF_EmbalseLaChupalla:Priority').Expression = '1'*Var_escenarios.iloc[experimento+1,70]

# Variación climática
WEAP.BranchVariable('\\Key Assumptions\\CC\\Delta_Pp').Expression = Var_escenarios.iloc[experimento+1,71]
WEAP.BranchVariable('\\Key Assumptions\\CC\\Delta_T').Expression = Var_escenarios.iloc[experimento+1,72]
t_2 = time.time()
tiempo_cambio = (t_2 - t_1)/60
print("Tiempo transcurrido en cambio de variables (min): " + str(int(tiempo_cambio)))

# Cálcilo WEAP
WEAP.Calculate()
t_3 = time.time()
tiempo_ejecucion = (t_3 - t_2)/60
print("Tiempo transcurrido en ejecución (min): " + str(int(tiempo_ejecucion)))

# Export Resultados desde WEAP
WEAP.LoadFavorite('Demanda\\Unmet Demand - APRs y APUs')
WEAP.ExportResults(weap_config["paths"]["src_path"] +"/WEAP/Unmet Demand_AP_" + Var_escenarios.iloc[experimento+1,0] + "_.csv", True, True, True, True, False)

WEAP.LoadFavorite('Demanda\\Unmet Demand -agricola')
WEAP.ExportResults(weap_config["paths"]["src_path"] +"/WEAP/Unmet Demand_AGRICOLA_" + Var_escenarios.iloc[experimento+1,0] + "_.csv", True, True, True, True, False)

t_4 = time.time()
tiempo_export_weap = (t_4 - t_3)/60
print("Tiempo transcurrido en Export WEAP (min): " + str(int(tiempo_export_weap)))

# Export Resultados desde MODFLOW
ruta_salida = weap_config["paths"]["src_path"]
os.makedirs('MODFLOW/MODFLOW_' + Var_escenarios.iloc[experimento+1,0])
os.makedirs('MODFLOW/MODFLOW_' + Var_escenarios.iloc[experimento+1,0] + '/BALANCE')
os.makedirs('MODFLOW/MODFLOW_' + Var_escenarios.iloc[experimento+1,0] + '/BALANCE_RL')

# BALANCE COMPLETO
current_path = os.path.abspath(os.getcwd())

nombre_carpeta_MF = 'NWT_v3_v4_dns_V2'
nombre_archivo_ZB = 'Zones.zbr'
diferencia_TS = 0
zones = ['ZR1','ZR2','ZR3','ZR4','ZR5','ZR6','ZR7','ZR8','ZR9','ZR10','ZR11','ZR12']  # Nombre Zone Budget Zone
aliases = {1: 'ZR1',2: 'ZR2',3: 'ZR3',4:'ZR4',5:'ZR5',6:'ZR6',7:'ZR7',8:'ZR8',9:'ZR9',10:'ZR10',11:'ZR11',12:'ZR12'}  # Alias Zone Budget Zone

path_balance = weap_config["paths"]["weap_areas_path"] +'/Ligua_Petorca_WEAP_MODFLOW_RDM/' + nombre_carpeta_MF
path_ZB = ruta_salida + '/' + nombre_archivo_ZB
path_salida = ruta_salida + '/MODFLOW/MODFLOW_' + Var_escenarios.iloc[experimento+1,0] + '/BALANCE'
get_full_balance(path_balance, path_ZB, path_salida)

    # RECARGA LATERAL
current_path = os.path.abspath(os.getcwd())

nombre_carpeta_MF = 'NWT_v3_v4_dns_V2'
nombre_archivo_ZB = 'Zones_WELLS.zbr'
diferencia_TS = 0
zones = ['ZR1','ZR2','ZR3','ZR4','ZR5','ZR6','ZR7','ZR8','ZR9','ZR10','ZR11','ZR12']  # Nombre Zone Budget Zone
aliases = {1: 'ZR1',2: 'ZR2',3: 'ZR3',4:'ZR4',5:'ZR5',6:'ZR6',7:'ZR7',8:'ZR8',9:'ZR9',10:'ZR10',11:'ZR11',12:'ZR12'}  # Alias Zone Budget Zone

path_balance = weap_config["paths"]["weap_areas_path"] + '/Ligua_Petorca_WEAP_MODFLOW_RDM/' + nombre_carpeta_MF
path_ZB = ruta_salida + '/' + nombre_archivo_ZB
path_salida = ruta_salida + '/MODFLOW/MODFLOW_' + Var_escenarios.iloc[experimento+1,0] + '/BALANCE_RL'
get_full_balance(path_balance, path_ZB, path_salida)

t_5 = time.time()
tiempo_export_modflow = (t_5 - t_4)/60
print("Tiempo transcurrido en Export MODFLOW (min): " + str(int(tiempo_export_modflow)))
