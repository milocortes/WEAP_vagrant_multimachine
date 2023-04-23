# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 23:15:33 2020
@author: KIARA TESEN
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#---    Matriz Agrícola    ----
def matriz_RunID(df_variable, variable, parametro, RunID, ruta_out):
    lista_df = []
    for b in df_variable.columns.values[1:]:
        df = pd.DataFrame()
        df['Anios'] = df_variable.iloc[:,0]
        df[variable] = df_variable[b]
        df['Sector Agricola'] = df_variable[b].name[df_variable[b].name.find("_")+1:df_variable[b].name.find("_")+9]
        df[parametro] =df_variable[b].name[df_variable[b].name.find("\\")+1:]
        df['RunID'] = str(RunID)
        if df_variable[b].name[df_variable[b].name.find("_")+6:].startswith('L'):
            df['Cuenca'] = 'La Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        df = df[['RunID', 'Anios', 'Cuenca','Sector Agricola',parametro, variable]]
        lista_df.append(df)
    concatena_df = pd.concat(lista_df)
    concatena_df['Sector Agricola'] = concatena_df['Sector Agricola'].apply(lambda x: x.replace('"',''))
    concatena_df[parametro] = concatena_df[parametro].apply(lambda x: x.replace('"',''))
    return concatena_df.to_csv(ruta_out + '/RunID_' + str(RunID) + '_' + variable + '_' + parametro + '.csv', index = False, encoding='latin1')

#---    Ordena DataFrame AGR    ----
def get_DataFrame(pd_numpy, pd_base, years):
    pd_numpy = pd.DataFrame(pd_numpy, columns = pd_base.columns.values)
    pd_numpy['Year'] = years
    pd_numpy.insert(0, 'Year', pd_numpy.pop('Year'))
    return pd_numpy

#---    Supply Delivered - AGR    ----
def get_SD(pd_anual, anios, RunID, SR, Variable):
    lista_DF = []
    pd_sd_aq_SR = pd.DataFrame(np.zeros((len(pd_anual.iloc[:,0]),6)), columns = ['Agua subterranea', 'Aporte de ladera', 'Canales', 'Conduccion Agua Desalinizada', 'Conduccion Embalse', 'Rio'])
    df_temp_e1 = pd.DataFrame()
    df_temp_e2 = pd.DataFrame()  
    for m in pd_anual.columns.values:
        df_temp = pd.DataFrame()
        if len(m) == 16 and m.endswith('fict'):
            df_temp_e1[m] = pd_anual[m]
            pd_sd_aq_SR['Agua subterranea'] =  df_temp_e1.sum(axis = 1, skipna = True)
        elif len(m) == 20 and m.endswith('fict'):
            df_temp_e2[m] = pd_anual[m]
            pd_sd_aq_SR['Aporte de ladera'] =  df_temp_e2.sum(axis = 1, skipna = True)
        elif m.startswith('Canal'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Canales'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Desalacion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion Agua Desalinizada'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Embalse'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion Embalse'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Rio') or m.startswith('Estero'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Rio'] =  df_temp.sum(axis = 1, skipna = True)
    pd_sd_aq_SR = pd_sd_aq_SR            
    
    lista_df = []
    for b in pd_sd_aq_SR.columns.values:
        df = pd.DataFrame()
        df[Variable] = pd_sd_aq_SR[b]
        df['Anios'] = anios
        df['Fuente'] =pd_sd_aq_SR[b].name
        df['RunID'] = RunID
        df['Sector Riego'] = pd_anual.columns.values[1][9:]
        if SR.startswith('L'):
            df['Cuenca'] = 'La Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        df = df[['RunID', 'Anios', 'Cuenca', 'Sector Riego', 'Fuente', Variable]]
        lista_df.append(df)

    concatena_df = pd.concat(lista_df)
    lista_DF.append(concatena_df)
    return lista_DF

# Supply Delivered - AP
def get_SD_AP(pd_anual, anios, a, i, Variable):
    lista_DF = []
    pd_sd_aq_SR = pd.DataFrame(np.zeros((len(pd_anual.iloc[:,0]),6)), columns = ['Agua subterranea', 'Camion aljibe', 'Impulsion', 'Aduccion', 'Conduccion', 'Conduccion Agua Desalinizada'])
    df_temp_e1 = pd.DataFrame()
    df_temp_e3 = pd.DataFrame()
    for m in pd_anual.columns.values:
        df_temp = pd.DataFrame()
        if m.endswith('CamAljibe'):
            df_temp_e3[m] = pd_anual[m]
            pd_sd_aq_SR['Camion aljibe'] =  df_temp_e3.sum(axis = 1, skipna = True) 
        elif m.startswith('APR') or m.startswith('APU'):
            df_temp_e1[m] = pd_anual[m]
            pd_sd_aq_SR['Agua subterranea'] =  df_temp_e1.sum(axis = 1, skipna = True)
        elif m.startswith('Impulsion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Impulsion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Aduccion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Aduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Concon'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Desalacion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion Agua Desalinizada'] =  df_temp.sum(axis = 1, skipna = True)
    pd_sd_aq_SR = pd_sd_aq_SR

    lista_df = []
    for b in pd_sd_aq_SR.columns.values:
        df = pd.DataFrame()
        df[Variable] = pd_sd_aq_SR[b]
        df['Anios'] = anios
        df['Fuente'] =pd_sd_aq_SR[b].name
        df['RunID'] = a
        if i[4:].startswith('L') or i[11:].startswith('Cabildo') or i[11:].startswith('LaLigua'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if i.startswith('APR'):
            df['Sector'] = 'Rural'
        elif i.startswith('APU'):
            df['Sector'] = 'Urbana'
        if i[10:].startswith('Petorca') or i[10:].startswith('Chincolco'):
            df['SHAC'] = 'P03'
        elif i[10:].startswith('Cabildo'):
            df['SHAC'] = 'L06'
        elif i[10:].startswith('LaLigua'):
            df['SHAC'] = 'L10 - L12'
        else:
            df['SHAC'] = i[4:7]
        df['Asociacion Agua Potable'] = i[10:]
        df = df[['RunID', 'Anios', 'Cuenca', 'Sector', 'SHAC', 'Asociacion Agua Potable', 'Fuente', Variable]]
        lista_df.append(df)

    concatena_df = pd.concat(lista_df)
    lista_DF.append(concatena_df)
    return lista_DF

def get_SD_AP_2(pd_anual, anios, a, i, Variable):
    lista_DF = []
    pd_sd_aq_SR = pd.DataFrame(np.zeros((len(pd_anual.iloc[:,0]),6)), columns = ['Agua subterranea', 'Camion aljibe', 'Impulsion', 'Aduccion', 'Conduccion', 'Conduccion Agua Desalinizada'])
    df_temp_e1 = pd.DataFrame()
    df_temp_e3 = pd.DataFrame()
    for m in pd_anual.columns.values:
        df_temp = pd.DataFrame()
        if m.endswith('CamAljibe'):
            df_temp_e3[m] = pd_anual[m]
            pd_sd_aq_SR['Camion aljibe'] =  df_temp_e3.sum(axis = 1, skipna = True) 
        elif m.startswith('APR') or m.startswith('APU'):
            df_temp_e1[m] = pd_anual[m]
            pd_sd_aq_SR['Agua subterranea'] =  df_temp_e1.sum(axis = 1, skipna = True)
        elif m.startswith('Impulsion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Impulsion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Aduccion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Aduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Concon'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Desalacion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion Agua Desalinizada'] =  df_temp.sum(axis = 1, skipna = True)
    pd_sd_aq_SR = pd_sd_aq_SR

    pd_sd_aq_SR['Total SD'] = pd_sd_aq_SR.sum(axis = 1)

    new_df = pd.DataFrame()
    new_df['Porcentaje Camion Aljibe vs Total (%)'] = (pd_sd_aq_SR['Camion aljibe']/pd_sd_aq_SR['Total SD'])*100
    new_df.fillna(0, inplace = True)

    lista_df = []
    for b in new_df.columns.values:
        df = pd.DataFrame()
        df['Anios'] = anios
        df[Variable] = new_df[b]
        df['RunID'] = a
        if i[4:].startswith('L') or i[11:].startswith('Cabildo') or i[11:].startswith('LaLigua'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if i.startswith('APR'):
            df['Sector'] = 'Rural'
        elif i.startswith('APU'):
            df['Sector'] = 'Urbana'
        if i[10:].startswith('Petorca') or i[10:].startswith('Chincolco'):
            df['SHAC'] = 'P03'
        elif i[10:].startswith('Cabildo'):
            df['SHAC'] = 'L06'
        elif i[10:].startswith('LaLigua'):
            df['SHAC'] = 'L10 - L12'
        else:
            df['SHAC'] = i[4:7]
        df['Asociacion Agua Potable'] = i[10:]
        df = df[['RunID', 'Anios', 'Cuenca', 'Sector', 'SHAC', 'Asociacion Agua Potable', Variable]]
        lista_df.append(df)

    concatena_df = pd.concat(lista_df)
    lista_DF.append(concatena_df)
    return lista_DF

def get_SD_by_AP(pd_anual, anios):
    pd_sd_aq_SR = pd.DataFrame(np.zeros((len(pd_anual.iloc[:,0]),6)), columns = ['Agua subterranea', 'Camion aljibe', 'Impulsion', 'Aduccion', 'Conduccion', 'Conduccion Agua Desalinizada'])
    df_temp_e1 = pd.DataFrame()
    df_temp_e3 = pd.DataFrame()
    for m in pd_anual.columns.values:
        df_temp = pd.DataFrame()
        if m.endswith('CamAljibe'):
            df_temp_e3[m] = pd_anual[m]
            pd_sd_aq_SR['Camion aljibe'] =  df_temp_e3.sum(axis = 1, skipna = True) 
        elif m.startswith('APR') or m.startswith('APU'):
            df_temp_e1[m] = pd_anual[m]
            pd_sd_aq_SR['Agua subterranea'] =  df_temp_e1.sum(axis = 1, skipna = True)
        elif m.startswith('Impulsion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Impulsion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Aduccion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Aduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Concon'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Cond_Desalacion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion Agua Desalinizada'] =  df_temp.sum(axis = 1, skipna = True)
    pd_sd_aq_SR = pd_sd_aq_SR
    pd_sd_aq_SR.set_index(anios, inplace = True)
    return pd_sd_aq_SR

def get_matriz_AP(pd_AP, anios, a, variable, parametro, ruta_out):
    lista_df = []
    for b in pd_AP.columns.values:
        df = pd.DataFrame()
        df[variable] = pd_AP[b]
        df['Anios'] = anios
        df['Fuente'] = parametro
        df['RunID'] = a
        if b[4:].startswith('L'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        df['Sector'] = 'Rural'
        df['SHAC'] = b[4:7]
        df['Asociacion Agua Potable'] = b[10:]

        df = df[['RunID', 'Anios', 'Cuenca', 'Sector', 'SHAC', 'Asociacion Agua Potable', 'Fuente', variable]]
        lista_df.append(df)

    concatena_df = pd.concat(lista_df)
    concatena_df.to_csv(ruta_out + '/RunID_' + str(a) + '_' + variable + '_' + parametro + '.csv', index = False, encoding='latin1')


def concatena(RunID,variable,parametro,ruta_out):
    m0 = []
    concat_ls = pd.DataFrame()  
    for b in RunID:
        m1 = pd.read_csv(ruta_out + '//RunID_' + str(b) + '_' + variable + '_' + parametro + '.csv', encoding='latin1')
        m0.append(m1)
    concat_ls = pd.concat(m0)
    concat_ls.index = range(concat_ls.shape[0])
    concat_ls.to_csv(ruta_out + '//RunID_' + variable + '_' + parametro + '.csv', index = False, encoding='latin1')
    #print(concat_ls)




def get_SD_AP_3(pd_anual, anios, a, i, Variable):
    lista_DF = []
    pd_sd_aq_SR = pd.DataFrame(np.zeros((len(pd_anual.iloc[:,0]),5)), columns = ['Agua subterranea', 'Camion aljibe', 'Impulsion', 'Aduccion', 'Conduccion'])
    df_temp_e1 = pd.DataFrame()
    df_temp_e3 = pd.DataFrame()
    for m in pd_anual.columns.values:
        #print(i, 'COLUMNA:',m,len(m))
        df_temp = pd.DataFrame()
        #if m.startswith(' APR') or m.startswith(' APU') and m.endswith('Aljibe'):
        if (len(m) == 25 and m.endswith('Aljibe')) or m.endswith('AljibeLaLigua'):
            df_temp_e3[m] = pd_anual[m]
            pd_sd_aq_SR['Camion aljibe'] =  df_temp_e3.sum(axis = 1, skipna = True) 
        elif m.startswith('APR') or m.startswith('APU'):
            df_temp_e1[m] = pd_anual[m]
            pd_sd_aq_SR['Agua subterranea'] =  df_temp_e1.sum(axis = 1, skipna = True)
        elif m.startswith('Impulsion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Impulsion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Aduccion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Aduccion'] =  df_temp.sum(axis = 1, skipna = True)
        elif m.startswith('Conduccion'):
            df_temp[m] = pd_anual[m]
            pd_sd_aq_SR['Conduccion'] =  df_temp.sum(axis = 1, skipna = True)
    pd_sd_aq_SR = pd_sd_aq_SR  

    new_df = pd.DataFrame()
    new_df['Costo Produccion AP - Camion Aljibe (CLP)'] = (pd_sd_aq_SR['Camion aljibe']*86.4*365)*8079
    new_df.fillna(0, inplace = True)
    #print(new_df)

    lista_df = []
    for b in new_df.columns.values:
        df = pd.DataFrame()
        df[Variable] = new_df[b]
        df['Anios'] = anios
        df['RunID'] = a
        if i[11:14].startswith('L') or i[7:].startswith('Cabildo') or i[7:].startswith('LaLigua'):
            df['Cuenca'] = 'Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if i.startswith('APR'):
            df['Sector'] = 'Rural'
        elif i.startswith('APU'):
            df['Sector'] = 'Urbana'
        if i[7:].startswith('Petorca') or i[7:].startswith('Chincolco'):
            df['SHAC'] = 'P03'
        elif i[7:].startswith('Cabildo'):
            df['SHAC'] = 'L06'
        elif i[7:].startswith('LaLigua'):
            df['SHAC'] = 'L10 - L12'
        else:
            df['SHAC'] = i[11:14]
        if i.startswith('APR'):
            df['Asociacion Agua Potable'] = i[19:]
        else:
            df['Asociacion Agua Potable'] = i[7:]
        df = df[['RunID', 'Anios', 'Cuenca', 'Sector', 'SHAC', 'Asociacion Agua Potable', Variable]]
        lista_df.append(df)

    concatena_df = pd.concat(lista_df)
    lista_DF.append(concatena_df)
    return lista_DF

def matriz_RunID4(df_variable, anios, variable, RunID, ruta_out):
    lista_df = []
    for b in df_variable.columns.values[1:]:
        df = pd.DataFrame()
        df['Anios'] = anios
        df['RunID'] = RunID
        df[variable] = df_variable[b]
        if b.startswith('APR_L') or b.startswith('APU_L'):
            df['Cuenca'] = 'La Ligua'
        else:
            df['Cuenca'] = 'Petorca'
        if b.startswith('APR'):
            df['Sector'] = 'Rural'
        elif b.startswith('APU'):
            df['Sector'] = 'Urbana'
        df['SHAC'] = df_variable[b].name[4:7]
        df['Asociacion Agua Potable'] = df_variable[b].name[df_variable[b].name.find("F_")+2:df_variable[b].name.find("\\")]
        df['Pozo'] = df_variable[b].name[df_variable[b].name.find("\\")+1:-6]

        df = df[['RunID', 'Anios', 'Cuenca', 'Sector', 'SHAC', 'Asociacion Agua Potable', 'Pozo', variable]]
        lista_df.append(df)
    concatena_df = pd.concat(lista_df)
    return concatena_df.to_csv(ruta_out + '/RunID_' + str(RunID) + '_' + variable + '_Asociacion Agua Potable.csv', index = False)