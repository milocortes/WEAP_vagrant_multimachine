# -*- coding: utf-8 -*-

import pandas as pd
import os
from flopy.utils.zonbud import ZoneBudget, read_zbarray
from datetime import datetime as dt
import glob
import time
import multiprocessing as mp
import numpy as np


################################################
####    Funciones Procesar archivos .ccf    ####
################################################

def get_scenario(temp):
    return temp[-15:-12]

def get_date(temp):
    diferencia_TS = 0
    temp1 = '1_' + temp[-11:-4]
    temp2 = dt.strptime(temp1, '%d_%Y_%W')
    return temp2 - pd.DateOffset(months=diferencia_TS)   

def get_TS(directorio, zone_analysis, output, zones):
    zones = zones
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

def get_full_balance(path_balance, path_ZB, dir_exit, temp_path, aliases, zones):
    zonefile = read_zbarray(path_ZB)

    # Leer binarios de la carpeta WEAP
    for file in os.listdir(path_balance):
        filename = os.fsdecode(file)
        if filename.endswith(".ccf"):
            t = temp_path + '/' + filename[:-4] + '.csv'
            zb = ZoneBudget(path_balance + '\\' + filename, zonefile, aliases=aliases)
            zb.to_csv(t)
            
    zones = zones
    for zone in zones:
        get_TS(temp_path, zone, dir_exit, zones)

    filelist = [ f for f in os.listdir(temp_path) if f.endswith(".csv") ]
    for f in filelist:
        os.remove(os.path.join(temp_path, f))

################################################
####    Clase de procesamiento    ####
################################################


class LP_WEAP(object):
    """docstring for ."""

    def __init__(self,acciones, activaciones, clima, acciones_valores, clima_valores, start_year, end_year):
        self.acciones = acciones
        self.activaciones = activaciones
        self.clima = clima
        self.acciones_valores = acciones_valores
        self.clima_valores = clima_valores
        self.policies = None
        self.future_id_df = None
        self.start_year = start_year
        self.end_year = end_year

    def build_future_id_df(self):
        policies = self.acciones.merge(self.activaciones, how="cross")[["Acciones","Activacion"]].iloc[2:].reset_index(drop=True)
        policies.loc[0,"Activacion"] = 2200
        policies["ID"] = range(policies.shape[0])
        policies = policies[["ID","Acciones","Activacion"]]

        future = policies.merge(clima, how="cross")[["Acciones","Activacion","GCM"]].reset_index(drop=True)
        future["ID"] = range(future.shape[0])
        future = future[["ID","Acciones","Activacion","GCM"]]

        self.policies = policies
        self.future = future

    def run_WEAP_model(self, action_id):
        # Set action_id 
        self.action_id = action_id

        # Open WEAP sesion
        WEAP = win32.Dispatch("WEAP.WEAPApplication")
        WEAP.ActiveArea = "Ligua_Petorca_WEAP_MODFLOW_RDM"
        WEAP.ActiveScenario = WEAP.Scenarios("Reference")
        WEAP.BaseYear = self.start_year
        WEAP.EndYear = self.end_year

        # Build Variable Branches
        acciones_2_agrupado = self.acciones_valores.groupby("Acciones")
        print("----------------------")
        print("******   CLIMA ********")
        print("----------------------")

        gcm = self.future.iloc[action_id]["GCM"]

        delta_t_20_39 = self.clima_valores.query(f"GCM=='{gcm}'")['Delta T | 20-39'].values[0]
        delta_t_40_59 = self.clima_valores.query(f"GCM=='{gcm}'")['Delta T | 40-59'].values[0]
        delta_p_20_39 = (100 + self.clima_valores.query(f"GCM=='{gcm}'")['Delta P | 20-39'].values[0])/100
        delta_p_40_59 = (100 + self.clima_valores.query(f"GCM=='{gcm}'")['Delta P | 40-59'].values[0])/100

        """
        print(f"WEAP.Branch('\\Key Assumptions\\CC\\DeltaT').Variables(1).Expression = 'Step( 1979,1,  2020,{delta_t_20_39},  2040,{delta_t_40_59} )'")
        print(f"WEAP.Branch('\\Key Assumptions\\CC\\DeltaP').Variables(1).Expression = 'Step( 1979,1,  2020,{delta_p_20_39},  2040,{delta_p_40_59} )'")
        """

        WEAP.Branch('\\Key Assumptions\\CC\\DeltaT').Variables(1).Expression = f"'Step( 1979,1,  2020,{delta_t_20_39},  2040,{delta_t_40_59})'"
        WEAP.Branch('\\Key Assumptions\\CC\\DeltaP').Variables(1).Expression = f"'Step( 1979,1,  2020,{delta_p_20_39},  2040,{delta_p_40_59})'"

        print("----------------------")
        print("******   ACCIONES ********")
        print("----------------------")

        print(self.future.iloc[action_id]["Acciones"], self.future.iloc[action_id]["Activacion"], self.future.iloc[action_id]["GCM"])
        if self.future.iloc[action_id]["Acciones"] == "Sin implementacion de acciones":
            for i in self.acciones_valores["BranchVariable"]:
                #print(f"WEAP.BranchVariable({i}).Expression='{anio_activacion}'")
                WEAP.BranchVariable(i).Expression='2200'
        else:
            ac =  self.future.iloc[action_id]["Acciones"]
            anio_activacion = self.future.iloc[action_id]["Activacion"]

            for i in acciones_2_agrupado.get_group(ac)["BranchVariable"]:
                #print(f"WEAP.BranchVariable({i}).Expression='{anio_activacion}'")
                WEAP.BranchVariable(i).Expression=f"{anio_activacion}"

            acciones_2_agrupado_index = list(acciones_2_agrupado.get_group(ac).index)
            sin_cambios = list(set(list(self.acciones_valores.index)).symmetric_difference(acciones_2_agrupado_index))

            for i in self.acciones_valores.iloc[sin_cambios]["BranchVariable"]:
                #print(f"WEAP.BranchVariable({i}).Expression='2200'")
                WEAP.BranchVariable(i).Expression='2200'

        print("----------------------")
        print("******   RUN MODEL ********")
        print("----------------------")

        WEAP.Calculate()

        print("---------------------------------------")
        print("******   EXPORT WEAP RESULTS  ********")
        print("----------------------------------------")

        favorites = pd.read_excel("../datos/Favorites_WEAP.xlsx")

        for i,j in zip(favorites["BranchVariable"],favorites["WEAP Export"]):
            WEAP.LoadFavorite(i)
            WEAP.ExportResults(f"../output/WEAP/run_id_{action_id}_{j}.csv", True, True, True, False, False)


    def processing_MODFLOW(self, ruta_WEAP,ruta_export):
        ############################################################################
        ####                  PRE-PROCESSING MODFLOW RESULTS                    ####
        ####    COMENTARIO: La versión hace referencia al ID de la ejecución    ####
        ####                ruta_WEAP se especifica según la PC del usuario     ####
        ############################################################################

        print("-----------------------------------------")
        print("******  EXPORT MODFLOW RESULTS  ********")
        print("-----------------------------------------")
    
        version = f'run_id_{self.action_id}'
        ruta = ruta_export

        # Se crea ruta según la versión
        dir_version = ruta + '/' + version
        if not os.path.isdir(dir_version):
            os.mkdir(dir_version)

        self.ZB = ['Zones.zbr', 'Zones_RL.zbr']

        # COMPLETE BALANCE
        if __name__ == "__main__":
            # start the MP pool for asynchronous parallelization
            pool = mp.Pool(int(mp.cpu_count()/2))

            for i in self.ZB:
                # Creación de sub-carpetas para análisis separados
                directorio = ruta + '/' + version + '/' + i[0:-4]
                if not os.path.isdir(directorio):
                    os.mkdir(directorio)

                dir_temp = directorio + '/temp'
                if not os.path.isdir(dir_temp):
                    os.mkdir(dir_temp)
                
                # Variables
                nombre_archivo_ZB = i
                nombre_carpeta_MF = 'NWT_RDM_v22'
                zones = ['P01','P02','P03','P07','P08','L01','L02','L05','L06','L09','L10','L12']  # Zone Budget Zones
                aliases = {1: 'P01',2: 'P02',3: 'P03',4:'P07',5:'P08',6:'L01',7:'L02',8:'L05',9:'L06',10:'L09',11:'L10',12:'L12'} # Alias Zone Budget Zone
                    
                path_salida = directorio
                path_balance = ruta_WEAP + '/' + nombre_carpeta_MF
                path_ZB = ruta + '/' + nombre_archivo_ZB
                temp_path = dir_temp
                
                # Ejecución funciones de Procesamiento
                pool.apply_async(
                    get_full_balance,
                    args = (
                        path_balance, path_ZB, path_salida, temp_path, aliases, zones
                    )
                )

            pool.close()
            pool.join()

        if __name__ == "__main__":
            for i in ZB:
                temp_path = ruta + '/' + version + '/' + i[0:-4] + '/temp'
                # Elimina carpeta temporal
                try:
                    os.rmdir(temp_path)
                except OSError as e:
                    print("Error: %s: %s" % (temp_path, e.strerror))

    def post_processing_MODFLOW(self, ruta_WEAP, ruta_export, anio_final):
        ###################################################
        ####    POST - PROCESSING - MODFLOW RESULTS    ####
        ###################################################

        if __name__ == "__main__":
                        
            ruta_BALANCE_ZB = ruta_export + '/' + version + '/' + self.ZB[0][0:-4]
            ruta_BALANCE_ZB_RL = ruta_export + '/' + version + '/' + self.ZB[1][0:-4]

            ruta_export_BALANCE = ruta_export + '/' + version + '/BALANCE'
            if not os.path.isdir(ruta_export_BALANCE):
                os.mkdir(ruta_export_BALANCE)

            fecha = pd.read_csv('../datos/Fechas.csv')
            años = pd.read_csv('../datos/Años.csv')

            años = años.query(f"Fecha <={anio_final}")
            fecha["anios"] = fecha["Fecha"].apply(lambda x: int(x[-4:]))
            fecha = fecha.query("anios <1985")

            variables = ['Variacion Neta Flujo Interacuifero', 'Recarga desde río', 'Recarga Lateral', 'Recarga distribuida', 'Recarga', 'Variacion Neta Flujo Mar', 'Afloramiento - DRAIN', 
                        'Afloramiento - RIVER', 'Afloramiento total', 'Bombeos', 'Almacenamiento']

            def get_df_ls(df, fecha):
                df_ls = pd.DataFrame()
                for i in df.columns.values[1:-2]:
                    df_ls[i] = pd.DataFrame((df[i].to_numpy())/86400)
                df_ls.set_index(fecha['Fecha'],inplace = True)
                df_temp = df_ls.iloc[117:2145,:]
                return df_temp

            def get_balance_cuenca(inicio, fin, zones, variables, años, cuenca):
                Res = (pd.read_excel(ruta_export_BALANCE + '/Resumen_balance_' + str(zones[inicio]) + '.xlsx').iloc[:,1:12]).to_numpy()
                for q in range (inicio + 1,fin):
                    dato = (pd.read_excel(ruta_export_BALANCE + '/Resumen_balance_' + str(zones[q]) + '.xlsx').iloc[:,1:12]).to_numpy()
                    Res = Res + dato
                Res_cuenca = pd.DataFrame(Res, columns = variables)
                Res_cuenca.set_index(años['Fecha'],inplace = True)
                return Res_cuenca.to_excel(ruta_export_BALANCE + '/Resumen_balance_' + str(cuenca) + '.xlsx')

            # SERIES ANUALES - AÑO HIDROLÓGICO
            for j in zones:
                Resumen = pd.DataFrame(columns = variables)

                df = pd.read_csv(ruta_BALANCE_ZB + '/' + j + '.csv')
                df_RL = pd.read_csv(ruta_BALANCE_ZB_RL + '/' + j + '.csv')
            
                df_temp = get_df_ls(df, fecha)
                df_RL_temp = get_df_ls(df_RL, fecha)
                
                # ANALISIS
                FI_in = (df_temp['FROM_ZONE_0'].to_numpy() + df_temp['FROM_P01'].to_numpy() + df_temp['FROM_P02'].to_numpy() + df_temp['FROM_P03'].to_numpy() + df_temp['FROM_P07'].to_numpy() + 
                        df_temp['FROM_P08'].to_numpy() + df_temp['FROM_L01'].to_numpy() + df_temp['FROM_L02'].to_numpy() + df_temp['FROM_L05'].to_numpy() + df_temp['FROM_L06'].to_numpy() + 
                        df_temp['FROM_L09'].to_numpy() + df_temp['FROM_L10'].to_numpy() + df_temp['FROM_L12'].to_numpy())
                FI_out = (df_temp['TO_ZONE_0'].to_numpy() + df_temp['TO_P01'].to_numpy() + df_temp['TO_P02'].to_numpy() + df_temp['TO_P03'].to_numpy() + df_temp['TO_P07'].to_numpy() + 
                        df_temp['TO_P08'].to_numpy() + df_temp['TO_L01'].to_numpy() + df_temp['TO_L02'].to_numpy() + df_temp['TO_L05'].to_numpy() + df_temp['TO_L06'].to_numpy() + 
                        df_temp['TO_L09'].to_numpy() + df_temp['TO_L10'].to_numpy() + df_temp['TO_L12'].to_numpy())
                Resumen.loc[:,'Variacion Neta Flujo Interacuifero'] = FI_in - FI_out

                Rch_rio = (df_temp['FROM_RIVER_LEAKAGE'].to_numpy())
                Resumen.loc[:,'Recarga desde río'] = Rch_rio
            
                Rch_lat = (df_RL_temp['FROM_WELLS'].to_numpy())
                Resumen.loc[:,'Recarga Lateral'] = Rch_lat

                Rch_well = (df_temp['FROM_WELLS'].to_numpy()) - Rch_lat
                Rch_dist = (df_temp['FROM_RECHARGE'].to_numpy())
                Resumen.loc[:,'Recarga distribuida'] = Rch_dist + Rch_well

                Resumen.loc[:, 'Recarga'] = Rch_rio + Rch_lat + Rch_dist
            
                Resumen.loc[:,'Variacion Neta Flujo Mar'] = (df_temp['FROM_CONSTANT_HEAD'].to_numpy() - df_temp['TO_CONSTANT_HEAD'].to_numpy())
                
                Af_Drain = -(df_temp['TO_DRAINS'].to_numpy())
                Resumen.loc[:,'Afloramiento - DRAIN'] = Af_Drain

                Af_RIVER = -(df_temp['TO_RIVER_LEAKAGE'].to_numpy())
                Resumen.loc[:,'Afloramiento - RIVER'] = Af_RIVER

                Resumen.loc[:,'Afloramiento total'] = Af_Drain + Af_RIVER
                
                Resumen.loc[:,'Bombeos'] = -(df_temp['TO_WELLS'].to_numpy())
            
                Resumen.loc[:,'Almacenamiento'] = -(df_temp['FROM_STORAGE'].to_numpy() - df_temp['TO_STORAGE'].to_numpy())

                Resumen = Resumen.to_numpy()
                data_prom = np.zeros((39,11))
                for n in range(0,11):
                    for m in range(0,39):
                        data_prom[m,n] = np.mean(Resumen[:,n][52*m:52*m+52])   

                Res_anual = pd.DataFrame(data_prom, columns = variables)
                Res_anual.set_index(años['Fecha'],inplace = True)
                Res_anual.to_excel(ruta_export_BALANCE + '/Resumen_balance_' + str(j) + '.xlsx')

            Petorca = get_balance_cuenca(0, 5, zones, variables, años, 'Petorca')
            Ligua = get_balance_cuenca(5, 12, zones, variables, años, 'Ligua')