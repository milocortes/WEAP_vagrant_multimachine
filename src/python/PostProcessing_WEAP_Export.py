# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 23:15:33 2020
@author: KIARA TESEN
"""
from Processing_functions import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import win32com.client as win32
import warnings
warnings.filterwarnings('ignore')

ruta_export_WEAP = r'..\src\output\WEAP'
ruta_export_MODFLOW = r'..\src\output\MODFLOW'
ruta_export_processing = r'..\src\output_processing'
ruta_data = r'..\src\data'

#RunID = range(81)
RunID = [80]

start_year = 2015
end_year = 2060
move = 2020 - start_year

anios = pd.DataFrame({'Fecha': range(start_year+5, end_year+1)})
SR_red = ['L05', 'L06', 'L07', 'L08', 'L09', 'L10', 'P02', 'P05', 'P06', 'P07', 'P08']
ZB = ['L01','L02','L05','L06','L09','L10','L12','P01','P02','P03','P07','P08']
QEco = ['AlicahueEnColliguay', 'PedernalEnTejada', 'SobranteEnPinadero']
ZR = ['Agricola_ZR02_P01', 'Agricola_ZR05_L01', 'Agricola_ZR05_P02', 'Agricola_ZR06_L02', 'Agricola_ZR06_P03', 'Agricola_ZR07_L05', 'Agricola_ZR07_P07', 'Agricola_ZR08_L06', 
      'Agricola_ZR08_P08', 'Agricola_ZR09_L09', 'Agricola_ZR10_L10_L12']

for a in RunID:
    ####    INDICADORES AGRÍCOLAS    ####
    
    #----    AREA    ---- 
    pd_area_agr = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AGR_Area.csv', skiprows = 3)[move:]
    
    # TEMPORAL #
    for i in pd_area_agr.columns.values:
        if i.endswith('Cereales'):
            pd_area_agr = pd_area_agr.drop(columns = [i])

    pd_area_agr_ha = pd_area_agr.iloc[:,1:]*0.0001
    pd_area_agr_ha['Año'] = pd_area_agr.iloc[:,0]
    pd_area_agr_ha.insert(0, 'Año', pd_area_agr_ha.pop('Año'))
    matriz_RunID(pd_area_agr_ha, 'Area Agricola (ha)', 'Cultivo', a, ruta_export_processing)

    #---    WATER DEMAND - ETp    ----
    pd_etp_agr = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AGR_ETp.csv', skiprows=3)[move*365+1:]
    pd_etp_agr['Branch'] = pd_etp_agr['Branch'].apply(lambda x: x[-4:])

    # TEMPORAL #
    for i in pd_etp_agr.columns.values:
        if i.endswith('Cereales'):
            pd_etp_agr = pd_etp_agr.drop(columns = [i])

    pd_etp_agr_anual = pd_etp_agr.groupby('Branch').sum()
    etp_agr_anual_ls = (pd_area_agr.iloc[:,1:].to_numpy() * pd_etp_agr_anual.to_numpy())/(365*86.4)
    pd_etp_agr_anual_ls = get_DataFrame(etp_agr_anual_ls, pd_etp_agr_anual, anios)
    matriz_RunID(pd_etp_agr_anual_ls, 'Demanda de Agua (l_s)', 'Cultivo', a, ruta_export_processing)
    
    #---    SUPPLY DELIVERED - ETa    ----
    pd_eta_agr = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AGR_ETa.csv', skiprows=3)[move*365+1:]  
    pd_eta_agr['Branch'] = pd_eta_agr['Branch'].apply(lambda x: x[-4:])

    # TEMPORAL #
    for i in pd_eta_agr.columns.values:
        if i.endswith('Cereales'):
            pd_eta_agr = pd_eta_agr.drop(columns = [i])

    pd_eta_agr_anual = pd_eta_agr.groupby('Branch').sum()
    eta_agr_anual_ls = (pd_area_agr.iloc[:,1:].to_numpy() * pd_eta_agr_anual.to_numpy())/(365*86.4)
    pd_eta_agr_anual_ls = get_DataFrame(eta_agr_anual_ls, pd_eta_agr_anual, anios)
    matriz_RunID(pd_eta_agr_anual_ls, 'Demanda Atendida (l_s)', 'Cultivo', a, ruta_export_processing)
    
    #---    UNMET DEMAND - AGR    ----
    ud_agr_ls = pd_etp_agr_anual_ls.iloc[:,1:].to_numpy() - pd_eta_agr_anual_ls.iloc[:,1:].to_numpy()
    pd_ud_agr_ls = get_DataFrame(ud_agr_ls, pd_etp_agr_anual_ls.iloc[:,1:], anios)
    matriz_RunID(pd_ud_agr_ls, 'Demanda No Atendida (l_s)', 'Cultivo', a, ruta_export_processing) 

    #---    UNMET DEMAND vs WATER DEMAND    ----
    extra = pd_ud_agr_ls.iloc[:,1:].to_numpy()/pd_etp_agr_anual_ls.iloc[:,1:].to_numpy()
    ud_agr_perc =  np.around(extra*100,3)
    pd_ud_agr_perc = get_DataFrame(ud_agr_perc, pd_ud_agr_ls.iloc[:,1:], anios)
    matriz_RunID(pd_ud_agr_perc, 'Demanda No Atendida vs Demanda Total (%)', 'Cultivo', a, ruta_export_processing) 

    #---    RIEGO    ----
    pd_riego_agr = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) +'_AGR_DailyIrrigation_m3.csv', skiprows=3)[move*365+1:] 
    pd_riego_agr['Branch'] = pd_riego_agr['Branch'].apply(lambda x: x[-4:])

    # TEMPORAL #
    for i in pd_riego_agr.columns.values:
        if i.endswith('Cereales'):
            pd_riego_agr = pd_riego_agr.drop(columns = [i])

    pd_riego_agr_anual_m3 = pd_riego_agr.groupby('Branch').sum()
    riego_agr_anual_m3_ha = pd_riego_agr_anual_m3.to_numpy()/pd_area_agr_ha.iloc[:,1:].to_numpy()  
    pd_riego_agr_anual_m3_ha = get_DataFrame(riego_agr_anual_m3_ha, pd_riego_agr_anual_m3, anios)
    matriz_RunID(pd_riego_agr_anual_m3_ha, 'Riego (m3_ha_anio)', 'Cultivo', a, ruta_export_processing)
    
    #---    SUPPLY DELIVERED    ----
    LISTA_DF = []
    for i in SR_red:
        pd_sd_agr = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AGR_SD_' + str(i) + '.csv', skiprows = 3)[(move*52):] 
        pd_sd_agr['Source'] = pd_sd_agr['Source'].apply(lambda x: x[-4:])
        pd_sd_agr = pd_sd_agr.astype(float)
        pd_sd_agr_anual = (pd_sd_agr.groupby('Source').mean())*1000 # l/s
        pd_sd_agr_anual = pd_sd_agr_anual.reset_index()
        
        LISTA_DF += get_SD(pd_sd_agr_anual, anios, a, i, 'Demanda Atendida por Fuente (l_s)')
    concatena_DF = pd.concat(LISTA_DF)
    concatena_DF.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Demanda Atendida por Fuente (l_s)_Sector Agricola.csv', index = False, encoding='latin1')
    
    #---    ANNUAL CROP PRODUCTION    ----
    pd_acp = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AGR_AnnualCropProduction.csv', skiprows = 3)[move:]
    
    # TEMPORAL #
    for i in pd_acp.columns.values:
        if i.endswith('Cereales'):
            pd_acp = pd_acp.drop(columns = [i])

    matriz_RunID(pd_acp, 'Produccion Anual (Ton)', 'Cultivo', a, ruta_export_processing)
    
    #---    RENDIMIENTO    ----
    rend_agr = (pd_acp.iloc[:,1:].to_numpy()*1000)/pd_area_agr_ha.iloc[:,1:].to_numpy() #Kg/ha
    pd_rend_agr = get_DataFrame(rend_agr, pd_acp.iloc[:,1:], anios) 
    matriz_RunID(pd_rend_agr, 'Rendimiento (kg_ha)', 'Cultivo', a, ruta_export_processing)

    rend_agr_ton = (pd_acp.iloc[:,1:].to_numpy())/pd_area_agr_ha.iloc[:,1:].to_numpy()
    pd_rend_agr_ton = get_DataFrame(rend_agr_ton, pd_acp.iloc[:,1:], anios)
    
    ####    INDICADORES AGUA POTABLE    ####
    AP_list = pd.read_csv(ruta_data + '/AP_list.csv')
    
    #---    WATER DEMAND    ----
    pd_wd_ap = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AP_WD.csv', skiprows = 3)[move*52:]
    pd_wd_ap['Branch'] = pd_wd_ap['Branch'].apply(lambda x: x[-4:])
    pd_wd_ap = pd_wd_ap.astype(float)
    pd_wd_ap_anual = (pd_wd_ap.groupby('Branch').mean())*1000 # l/s
    pd_wd_ap_anual = pd_wd_ap_anual.reset_index()
    
    lista_df_wd = []
    for k in pd_wd_ap_anual.iloc[:,1:].columns.values:
        df = pd.DataFrame()
        df['Demanda de Agua (l_s)'] = pd_wd_ap_anual[k]
        if k.startswith('APR'):
            df['Asociacion Agua Potable'] = k[10:]
        else:
            df['Asociacion Agua Potable'] = k
        df['RunID'] = a
        df['Anios'] = anios
        if k.startswith('APR_L') or k.startswith('Cabildo') or k.startswith('LaLigua'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if k.startswith('APR'):
            df['Sector'] = 'Rural'
        else:
            df['Sector'] = 'Urbana'
        if k.startswith('Petorca') or k.startswith('Chincolco'):
            df['SHAC'] = 'P03'
        elif k.startswith('Cabildo'):
            df['SHAC'] = 'L06'
        elif k.startswith('LaLigua'):
            df['SHAC'] = 'L10 - L12'
        else:
            df['SHAC'] = k[4:7]
            
        df = df[['RunID', 'Anios', 'Cuenca', 'SHAC', 'Sector', 'Asociacion Agua Potable','Demanda de Agua (l_s)']]
        lista_df_wd.append(df)

    concatena_wd = pd.concat(lista_df_wd)
    concatena_wd.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Demanda de Agua (l_s)_Asociacion Agua Potable.csv', index = False)

    #---    SUPPLY DELIVERED    ----
    #---    PORCENTAJE ATENDIDO POR CAMIONES ALJIBE    ----
    LISTA_DF = []
    LISTA_DF2 = []
    index = 0
    for i in AP_list['Asociacion AP']:
        pd_sd_ap = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_' + str(i) + '.csv', skiprows = 3)[(move*52):]
        pd_sd_ap['Source'] = pd_sd_ap['Source'].apply(lambda x: x[-4:])
        pd_sd_ap = pd_sd_ap.astype(float)
        pd_sd_ap_anual = (pd_sd_ap.groupby('Source').mean())*1000 # l/s
        pd_sd_ap_anual = pd_sd_ap_anual.reset_index()
        
        LISTA_DF += get_SD_AP(pd_sd_ap_anual, anios, a, AP_list.loc[index, 'Reducido'], 'Demanda Atendida por Fuente (l_s)')
        LISTA_DF2 += get_SD_AP_2(pd_sd_ap_anual, anios, a, AP_list.loc[index, 'Reducido'], 'Porcentaje Camion Aljibe vs Total (%)')
        index += 1

    concatena_DF = pd.concat(LISTA_DF)
    concatena_DF.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Demanda Atendida por Fuente (l_s)_Asociacion Agua Potable.csv', index = False, encoding='latin1')
    concatena_DF_2 = pd.concat(LISTA_DF2)
    concatena_DF_2.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Porcentaje Camion Aljibe vs Total (%)_Asociacion Agua Potable.csv', index = False, encoding='latin1')

    #---    DEMANDA NO CUBIERTA    ----
    pd_ud_ap = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AP_UD.csv', skiprows = 3)[move*52:]
    pd_ud_ap['Demand Site'] = pd_ud_ap['Demand Site'].apply(lambda x: x[-4:])
    pd_ud_ap = pd_ud_ap.astype(float)
    pd_ud_ap_anual = (pd_ud_ap.groupby('Demand Site').mean())*1000 # l/s
    pd_ud_ap_anual = pd_ud_ap_anual.reset_index()
    
    lista_df_ud = []
    for k in pd_ud_ap_anual.iloc[:,1:].columns.values:
        df = pd.DataFrame()
        df['Demanda No Atendida (l_s)'] = pd_ud_ap_anual[k]
        if k.startswith('APR'):
            df['Asociacion Agua Potable'] = k[10:]
        else:
            df['Asociacion Agua Potable'] = k
        df['RunID'] = a
        df['Anios'] = anios
        if k.startswith('APR_L') or k.startswith('Cabildo') or k.startswith('LaLigua'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if k.startswith('APR'):
            df['Sector'] = 'Rural'
        else:
            df['Sector'] = 'Urbana'
        if k.startswith('Petorca') or k.startswith('Chincolco'):
            df['SHAC'] = 'P03'
        elif k.startswith('Cabildo'):
            df['SHAC'] = 'L06'
        elif k.startswith('LaLigua'):
            df['SHAC'] = 'L10 - L12'
        else:
            df['SHAC'] = k[4:7]
            
        df = df[['RunID', 'Anios', 'Cuenca', 'SHAC', 'Sector', 'Asociacion Agua Potable','Demanda No Atendida (l_s)']]
        lista_df_ud.append(df)

    concatena_ud = pd.concat(lista_df_ud)
    concatena_ud.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Demanda No Atendida (l_s)_Asociacion Agua Potable.csv', index = False)
    
    #---    FALLA DE POZOS    ----
    pd_pozos = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_AP_Operacion_Pozos.csv', skiprows = 3)[move*52:]
    pd_pozos = pd_pozos.set_index('Branch')
    
    Num_col = pd_pozos.to_numpy().shape[1]
    num = np.zeros((len(anios),Num_col))
    for i in range(0,Num_col):
        for j in range(0,len(anios)):
            num[j][i]=len(np.where(pd_pozos.to_numpy()[:,i][52*j:52*(j+1)] < 0.000007)[0])
    pd_falla_pozos = pd.DataFrame(num, columns = pd_pozos.columns.values)
    pd_falla_pozos['Year'] = anios
    pd_falla_pozos.insert(0, 'Year', pd_falla_pozos.pop('Year'))
    
    matriz_RunID4(pd_falla_pozos, anios,  'Semanas en Falla', str(a), ruta_export_processing)
    
    ####    INDICADORES SUSTENTABILIDAD    ####

    #---    VOLUMEN ALMACENADO - SHACs    ----
    lista_DF = []
    for k in ZB:
        vol = pd.read_csv(ruta_export_MODFLOW + '/run_id_' + str(a) + '/VOLUMEN/Volumen - SHAC - ' + str(k) + '.csv')[(move-1)*52:]
        df = pd.DataFrame()
        df['Volumen - (Mm3)'] = vol['S09Volumen - [Mm3]']
        df['Anios'] = vol['Year']
        df['Semana'] = vol['Week']
        df['RunID'] = a
        if k.startswith('L'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        df['SHAC'] = k
        df = df[['RunID', 'Anios', 'Semana', 'Cuenca', 'SHAC', 'Volumen - (Mm3)']]
        lista_DF.append(df)
    concatena_sust = pd.concat(lista_DF)        
    concatena_sust.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Volumen Almacenado (Mm3)_SHACs.csv', index = False)
    """
    #---    CAUDAL ECOLÓGICO    ----
    pd_qeco_data = pd.read_csv(ruta_data + '/Qecologico.csv', encoding = 'latin1')
    print(pd_qeco_data)

    pd_new_cec = pd.DataFrame()
    for j in QEco:
        pd_cec = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_CEC_' + str(j) + '.csv', skiprows = 3)[move*52:]
        print(pd_cec)

        pd_new_cec[j] = (pd_qeco_data[j].to_numpy() - pd_cec.iloc[:,1].to_numpy())*1000
    print(pd_new_cec)
    
    for m in range(3):
        for n in range(2080):
            if pd_new_cec.iloc[n,m] < 0:
                pd_new_cec.iloc[n,m] = 0
    #print(pd_new_cec)

    lista_df_cec = []
    for k in pd_new_cec.columns.values:
        #print(k)
        df = pd.DataFrame()
        df['Brecha entre caudal pasante y ecologico (l_s)'] = pd_new_cec[k]
        df['Estacion'] = pd_new_cec[k].name
        df['Anios'] = pd_qeco_data['Year']
        df['Semana'] = pd_qeco_data['Week']
        df['RunID'] = a
        if k.startswith('Pedernal') or k.startswith('Sobrante'):
            df['Cuenca'] = 'Petorca'
        else:
            df['Cuenca'] = 'Ligua'
        df = df[['RunID', 'Anios', 'Semana', 'Cuenca', 'Estacion', 'Brecha entre caudal pasante y ecologico (l_s)']]
        lista_df_cec.append(df)

    concatena_cec = pd.concat(lista_df_cec)
    #print(concatena_cec)
    concatena_cec.to_csv(ruta_export_processing + '/RunID_' + str(a) + '_Brecha Caudal Ecologico (l_s)_Estaciones Cabecera.csv', index = False)
    """

    ####    INDICADORES SOCIOECONÓMICOS    ####
    
    #---    REDUCCIÓN DEL VALOR DE LA PRODUCCIÓN AGRÍCOLA ($)    ----
    rend_pot = pd.read_csv('../src/data/AGR_Rend_Potencial.csv', skiprows = 3)[move:]    
    # TEMPORAL #
    for i in rend_pot.columns.values:
        if i.endswith('Cereales'):
            rend_pot = rend_pot.drop(columns = [i])
    
    precio = pd.read_csv('../src/data/AGR_CLP_ton.csv', skiprows = 3)[move:]
    # TEMPORAL #
    for i in precio.columns.values:
        if i.endswith('Cereales'):
            precio = precio.drop(columns = [i])

    a_ = rend_pot.iloc[:,1:].to_numpy()
    b_ = np.around(pd_rend_agr_ton.iloc[:,1:].to_numpy(),1)
    c_ = pd_area_agr_ha.iloc[:,1:].to_numpy()
    d_ = precio.iloc[:,1:].to_numpy()
    
    VPA = (a_ - b_)*c_*d_
    VPA_unit = (a_ - b_)*d_
    
    pd_VPA = get_DataFrame(VPA, pd_rend_agr_ton.iloc[:,1:], anios)
    matriz_RunID(pd_VPA, 'Reduccion del Valor de la Produccion Agricola (CLP)', 'Cultivo', a, ruta_export_processing)

    pd_VPA_unit = get_DataFrame(VPA_unit, pd_rend_agr_ton.iloc[:,1:], anios)
    matriz_RunID(pd_VPA_unit, 'Reduccion del Valor de la Produccion Agricola Unitario (CLP_ha)', 'Cultivo', a, ruta_export_processing)

    #---    REDUCCIÓN DEL EMPLEO AGRÍCOLA    ----
    jornada = pd.read_csv('../src/data/AGR_JH_ton.csv', skiprows = 3)[move:]
    # TEMPORAL #
    for i in jornada.columns.values:
        if i.endswith('Cereales'):
            jornada = jornada.drop(columns = [i])
    
    e_ = jornada.iloc[:,1:].to_numpy()
    empleo = (a_ - b_)*c_*e_
    empleo_unit = (a_ - b_)*e_
    
    pd_empleo = get_DataFrame(empleo, pd_rend_agr_ton.iloc[:,1:], anios)
    matriz_RunID(pd_empleo, 'Reduccion del Empleo Agricola (JH)', 'Cultivo', a, ruta_export_processing)

    pd_empleo_unit = get_DataFrame(empleo_unit, pd_rend_agr_ton.iloc[:,1:], anios)
    matriz_RunID(pd_empleo_unit, 'Reduccion del Empleo Agricola Unitario (JH_ha)', 'Cultivo', a, ruta_export_processing)

    #---    COSTO DE ABASTECIMIENTO POR VOLUMEN DE AGUA - AP / POZOS    ----
    pd_ctp_ligua = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_CT-P_AprsLigua.csv', skiprows = 3)[move:]
    pd_ctp_ligua.set_index("Branch", inplace = True)

    pd_ctp_petorca = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_CT-P_AprsPetorca.csv', skiprows = 3)[move:]
    pd_ctp_petorca.set_index("Branch", inplace = True)

    pd_ctp = pd.concat([pd_ctp_ligua, pd_ctp_petorca], axis = 1)
    
    index = 0
    APR_list = pd.read_csv(ruta_data + '/APR_list.csv')
    c_ab_ap_pozos = pd.DataFrame()
    for i in APR_list['Asociacion AP']:
        # TEMPORAL #
        if i == "APR_SD_APR_L06_Dem_LaHiguera":
            pass
        else:
            pd_sd_ap = pd.read_csv(ruta_export_WEAP + '/run_id_' + str(a) + '_' + str(i) + '.csv', skiprows = 3)[(move*52):]
            pd_sd_ap['Source'] = pd_sd_ap['Source'].apply(lambda x: x[-4:])
            pd_sd_ap = pd_sd_ap.astype(float)
            pd_sd_ap_anual_m3 = (pd_sd_ap.groupby('Source').mean())*(60*60*24*365) # m3/año
            pd_sd_ap_anual_m3 = pd_sd_ap_anual_m3.reset_index()
            
            pd_sd_ap_anual_m3_by_AP = get_SD_by_AP(pd_sd_ap_anual_m3, anios['Fecha'])
            c_ab_ap_pozos[APR_list.loc[index, 'Reducido']] = pd_ctp[APR_list.loc[index, 'Reducido']]/pd_sd_ap_anual_m3_by_AP['Agua subterranea']
        index += 1
    c_ab_ap_pozos = c_ab_ap_pozos.reset_index()
    # FALTA CTC, CTA, CTD #
    get_matriz_AP(c_ab_ap_pozos.iloc[:,1:], anios, str(a), 'Costo de Abastecimiento - Pozos (CLP_m3)', 'Pozos', ruta_export_processing)

####    CONCATENAR TODOS LOS ID's    ####
concatena(RunID, 'Area Agricola (ha)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Costo de Abastecimiento - Pozos (CLP_m3)', 'Pozos', ruta_export_processing)
concatena(RunID, 'Demanda Atendida (l_s)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Demanda Atendida por Fuente (l_s)', 'Sector Agricola', ruta_export_processing)
concatena(RunID, 'Demanda Atendida por Fuente (l_s)', 'Asociacion Agua Potable', ruta_export_processing)
concatena(RunID, 'Demanda de Agua (l_s)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Demanda de Agua (l_s)', 'Asociacion Agua Potable', ruta_export_processing)
concatena(RunID, 'Demanda No Atendida (l_s)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Demanda No Atendida (l_s)', 'Asociacion Agua Potable', ruta_export_processing)
concatena(RunID, 'Demanda No Atendida vs Demanda Total (%)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Porcentaje Camion Aljibe vs Total (%)', 'Asociacion Agua Potable', ruta_export_processing)
concatena(RunID, 'Produccion Anual (Ton)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Reduccion del Empleo Agricola (JH)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Reduccion del Empleo Agricola Unitario (JH_ha)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Reduccion del Valor de la Produccion Agricola (CLP)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Reduccion del Valor de la Produccion Agricola Unitario (CLP_ha)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Rendimiento (kg_ha)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Riego (m3_ha_anio)', 'Cultivo', ruta_export_processing)
concatena(RunID, 'Semanas en Falla', 'Asociacion Agua Potable', ruta_export_processing)
concatena(RunID, 'Volumen Almacenado (Mm3)', 'SHACs', ruta_export_processing)
#concatena(RunID, 'Brecha Caudal Ecologico (l_s)', 'Estaciones Cabecera', ruta_export_processing)