# -*- coding: utf-8 -*-

import pandas as pd
import os
from flopy.utils.zonbud import ZoneBudget, read_zbarray # Se trabaja con versión flopy == 3.3.4
import flopy.utils.binaryfile as bf
from itertools import chain
from datetime import datetime as dt
import glob
import time
import multiprocessing as mp
import numpy as np
import win32com.client as win32

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
            #zb = ZoneBudget(path_balance + '\\' + filename, zonefile, aliases=aliases)
            zb = ZoneBudget(os.path.join(path_balance, filename), zonefile, aliases=aliases)
            zb.to_csv(t)
            
    zones = zones
    for zone in zones:
        get_TS(temp_path, zone, dir_exit, zones)

    filelist = [ f for f in os.listdir(temp_path) if f.endswith(".csv") ]
    for f in filelist:
        os.remove(os.path.join(temp_path, f))

######################################
####    Clase de procesamiento    ####
######################################

class LP_WEAP(object):
    """docstring for ."""

    def __init__(self,clima, demanda, start_year, end_year, output_path_WEAP,output_path_MODFLOW, path_WEAP, ZB, zones, ZR, Sc, demanda_valores):
        self.clima = clima
        self.demanda = demanda
        self.demanda_valores = demanda_valores
        #self.policies = None
        self.future_id_df = None
        self.start_year = start_year
        self.end_year = end_year
        self.output_path_WEAP = output_path_WEAP
        self.output_path_MODFLOW = output_path_MODFLOW
        self.path_WEAP = path_WEAP
        self.ZB = ZB
        self.zones = zones
        self.ZR = ZR
        self.Sc = Sc

    def build_future_id_df(self):
        clima = self.clima
        future = clima.merge(self.demanda, how = "cross")[["GCM","Demanda"]].reset_index(drop=True)
        future["ID"] = range(future.shape[0])
        future = future[["ID", "GCM","Demanda"]]

        self.future = future
        future.to_csv('RunIDs.csv')
        print(future)

    def run_WEAP_model(self, action_id):
        self.action_id = action_id

        # Open WEAP sesion
        WEAP = win32.Dispatch("WEAP.WEAPApplication")
        WEAP.ActiveArea = "Ligua_Petorca_WEAP_MODFLOW_RDM"
        WEAP.ActiveScenario = WEAP.Scenarios("Current Accounts")
        WEAP.BaseYear = self.start_year
        WEAP.EndYear = self.end_year

        # Build Variable Branches
        print("-------------------------")
        print("******   CLIMA   ********")
        print("-------------------------")

        gcm = self.future.iloc[action_id]["GCM"]

        for k in self.ZR:
            Branch_ZR_P = "\\Demand Sites and Catchments\\" + str(k) + ":Precipitation"
            Branch_ZR_MinT = "\\Demand Sites and Catchments\\" + str(k) + ":Min Temperature"
            Branch_ZR_MaxT = "\\Demand Sites and Catchments\\" + str(k) + ":Max Temperature"
            if gcm == 'Clima historico':
                RF_ZR_P = 'ReadFromFile(Datos\\variables climaticas LPQ\pr_Agro_LPQ_Corregida.csv, "' + str(k) +'", , Average, , Interpolate)'                
                RF_ZR_MinT = 'ReadFromFile(Datos\\variables climaticas LPQ\\tmin_Agro_LPQ.csv, "' + str(k) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmin\\' + str(k)
                RF_ZR_MaxT = 'ReadFromFile(Datos\\variables climaticas LPQ\\tmax_Agro_LPQ.csv, "' + str(k) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmax\\' + str(k)
            else:
                RF_ZR_P = 'ReadFromFile(Datos\GCMs\pr_LPQ_' + gcm + '.csv, "' + str(k) +'", , Average, , Interpolate)'
                RF_ZR_MinT = 'ReadFromFile(Datos\GCMs\\tasmin_LPQ_' + gcm + '.csv, "' + str(k) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmin\\' + str(k)
                RF_ZR_MaxT = 'ReadFromFile(Datos\GCMs\\tasmax_LPQ_' + gcm + '.csv, "' + str(k) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmax\\' + str(k)

            WEAP.BranchVariable(Branch_ZR_P).Expression = RF_ZR_P # Precipitation
            WEAP.BranchVariable(Branch_ZR_MinT).Expression = RF_ZR_MinT # Min Temperature
            WEAP.BranchVariable(Branch_ZR_MaxT).Expression = RF_ZR_MaxT # Max Temperature
            #print(Branch_ZR_P, RF_ZR_P)

        for m in self.Sc:
            Branch_Sc_P = '\\Key Assumptions\\Series SMM\\PP\\' + str(m)
            Branch_Sc_T = '\\Key Assumptions\\Series SMM\T\\' + str(m)
            if gcm == 'Clima historico':
                RF_Sc_P = 'ReadFromFile(Datos\\variables climaticas LPQ\pr_Subc_LPQ_Corregida.csv, "Subcuenca_' +str(m) + '", , Sum, , Replace)*PP'
                RF_Sc_T = 'ReadFromFile(Datos\\variables climaticas LPQ\\t2m_Subc_LPQ.csv, "Subcuenca_' + str(m) + '", , Average, , Replace)'
            else:
                RF_Sc_P = 'ReadFromFile(Datos\GCMs\pr_LPQ_' + gcm + '.csv, "Subcuenca_' +str(m) + '", , Sum, , Replace)*PP'
                RF_Sc_T = 'ReadFromFile(Datos\GCMs\\tas_LPQ_' + gcm + '.csv, "Subcuenca_' + str(m) + '", , Average, , Replace)'
            WEAP.Branch(Branch_Sc_P).Variables(1).Expression = RF_Sc_P # Precipitation
            WEAP.Branch(Branch_Sc_T).Variables(1).Expression = RF_Sc_T # Temperature

        print("---------------------------")
        print("******   DEMANDA   ********")
        print("---------------------------")

        demand = self.future.iloc[action_id]["Demanda"]

        delta_riego = round(self.demanda_valores.query(f"Demanda=='{demand}'")['AreasRiego'].values[0],2)
        delta_poblacion = round(self.demanda_valores.query(f"Demanda=='{demand}'")['Poblacion'].values[0],2)

        WEAP.Branch('\\Key Assumptions\\VariacionAreasRiego').Variables(1).Expression = f"Step( 1979,1,  2021,{delta_riego})"
        WEAP.Branch('\\Key Assumptions\\VariacionPoblacion').Variables(1).Expression = f"Step( 1979,1,  2021,{delta_poblacion})"

        WEAP.Calculate()

        print("---------------------------------------")
        print("******   EXPORT WEAP RESULTS   ********")
        print("---------------------------------------")

        favorites = pd.read_excel("../datos/Favorites_WEAP.xlsx")

        for i,j in zip(favorites["BranchVariable"],favorites["WEAP Export"]):
            WEAP.LoadFavorite(i)
            WEAP.ExportResults(os.path.join(self.output_path_WEAP,f"run_id_{action_id}_{j}.csv"), True, True, True, False, False)

    ############################################################################
    ####                  PRE-PROCESSING MODFLOW RESULTS                    ####
    ####    COMENTARIO: La versión hace referencia al ID de la ejecución    ####
    ####                ruta_WEAP se especifica según la PC del usuario     ####
    ############################################################################

    def processing_MODFLOW(self):
        
        print("----------------------------------------")
        print("******  EXPORT MODFLOW RESULTS  ********")
        print("----------------------------------------")
    
        version = f'run_id_{self.action_id}'

        # Se crea ruta según runID
        dir_version = os.path.join(self.output_path_MODFLOW, version)
        if not os.path.isdir(dir_version):
            os.mkdir(dir_version)

        ZB = self.ZB

        # COMPLETE BALANCE
        # start the MP pool for asynchronous parallelization
        pool = mp.Pool(int(mp.cpu_count()/2))

        for i in self.ZB:
            # Creación de sub-carpetas para análisis separados
            directorio = os.path.join(self.output_path_MODFLOW, version, i[0:-4])
            if not os.path.isdir(directorio):
                os.mkdir(directorio)

            dir_temp = os.path.join(directorio,'temp')
            if not os.path.isdir(dir_temp):
                os.mkdir(dir_temp)
            
            # Variables
            nombre_archivo_ZB = i
            nombre_carpeta_MF = 'NWT_RDM_v22'
            zones = self.zones
            aliases = {1: 'P01',2: 'P02',3: 'P03',4:'P07',5:'P08',6:'L01',7:'L02',8:'L05',9:'L06',10:'L09',11:'L10',12:'L12'} # Alias Zone Budget Zone
                
            path_salida = directorio
            path_balance = os.path.join(self.path_WEAP,nombre_carpeta_MF)
            path_ZB = nombre_archivo_ZB
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

        for i in self.ZB:
            temp_path = os.path.join(self.output_path_MODFLOW, version, i[0:-4], 'temp')
            # Elimina carpeta temporal
            try:
                os.rmdir(temp_path)
            except OSError as e:
                print("Error: %s: %s" % (temp_path, e.strerror))

    def post_processing_MODFLOW(self):
        ###################################################
        ####    POST - PROCESSING - MODFLOW RESULTS    ####
        ###################################################

        version = f'run_id_{self.action_id}'
                    
        ruta_BALANCE_ZB = os.path.join(self.output_path_MODFLOW, version ,self.ZB[0][0:-4])
        ruta_BALANCE_ZB_RL = os.path.join(self.output_path_MODFLOW, version, self.ZB[1][0:-4])
        
        ruta_export_BALANCE = os.path.join(self.output_path_MODFLOW, version, 'BALANCE')
        if not os.path.isdir(ruta_export_BALANCE):
            os.mkdir(ruta_export_BALANCE)

        fecha = pd.read_csv('../datos/Fechas.csv')
        fecha["anios"] = fecha["Fecha"].apply(lambda x: int(x[-4:]))
        fecha = fecha.query(f"anios <= {self.end_year}")
        anios = pd.DataFrame({'Fecha': range(self.start_year+2,self.end_year+1)}) # Para año calendario
        #anios = pd.DataFrame({'Fecha': range(self.start_year+2,self.end_year)}) # Para año hidrológico

        variables = ['Variacion Neta Flujo Interacuifero', 'Recarga desde río', 'Recarga Lateral', 'Recarga distribuida', 'Recarga', 'Variacion Neta Flujo Mar', 
                    'Afloramiento - DRAIN', 'Afloramiento - RIVER', 'Afloramiento total', 'Bombeos', 'Almacenamiento']

        def get_df_ls(df, fecha):
            df_ls = pd.DataFrame()
            for i in df.columns.values[1:-2]:
                df_ls[i] = pd.DataFrame((df[i].to_numpy())/86400)
            df_ls.set_index(fecha['Fecha'],inplace = True)
            #df_temp = df_ls.iloc[117:-39,:] # Para año hidrológico
            df_temp = df_ls.iloc[104:,:] # Para año calendario
            return df_temp

        def get_balance_cuenca(inicio, fin, zones, variables, años, cuenca):
            Res = (pd.read_excel(os.path.join(ruta_export_BALANCE, 'Resumen_balance_' + str(zones[inicio]) + '.xlsx')).iloc[:,1:12]).to_numpy()
            for q in range (inicio + 1,fin):
                dato = (pd.read_excel(os.path.join(ruta_export_BALANCE, 'Resumen_balance_' + str(zones[q]) + '.xlsx')).iloc[:,1:12]).to_numpy()
                Res = Res + dato
            Res_cuenca = pd.DataFrame(Res, columns = variables)
            Res_cuenca.set_index(años['Fecha'],inplace = True)
            return Res_cuenca.to_excel(os.path.join(ruta_export_BALANCE, 'Resumen_balance_' + str(cuenca) + '.xlsx'))

        # SERIES ANUALES - AÑO HIDROLÓGICO
        for j in self.zones:
            Resumen = pd.DataFrame(columns = variables)

            df = pd.read_csv(os.path.join(ruta_BALANCE_ZB, j + '.csv'))
            df_RL = pd.read_csv(os.path.join(ruta_BALANCE_ZB_RL, j + '.csv'))
        
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
            data_prom = np.zeros((len(anios),11))
            for n in range(0,11):
                for m in range(0,len(anios)):
                    data_prom[m,n] = np.mean(Resumen[:,n][52*m:52*m+52])   

            Res_anual = pd.DataFrame(data_prom, columns = variables)
            Res_anual.set_index(anios['Fecha'],inplace = True)
            Res_anual.to_excel(os.path.join(ruta_export_BALANCE,'Resumen_balance_' + str(j) + '.xlsx'))

        Petorca = get_balance_cuenca(0, 5, self.zones, variables, anios, 'Petorca')
        Ligua = get_balance_cuenca(5, 12, self.zones, variables, anios, 'Ligua')

        #----------------------------------
        #----    Volumenes por Shac    ----
        #----------------------------------

        # Leer archivo .hed o .cbb para extraer flujo en las celdas y volumenes
        #ruta_WEAP = r'C:\Users\aimee\OneDrive\Documentos\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM'
        nombre_carpeta_MF = 'NWT_RDM_v22'
        Path_out = os.path.join(self.output_path_MODFLOW, version, 'VOLUMEN')
        if not os.path.isdir(Path_out):
            os.mkdir(Path_out)

        # Lectura de resultados y archivos nativos
        prj = 'con_dren_sin_aisladas_NWT'
        path_balance = os.path.join(self.path_WEAP,nombre_carpeta_MF)
        Pth_DIS = os.path.join(path_balance, prj + 'dis')#path_balance+'\\'+prj+'.dis'
        Pth_UPW = os.path.join(path_balance, prj + 'upw')#path_balance+'\\'+prj+'.upw'
        Pth_ZB = 'Zones.zbr'#path_balance + '\\Zones.zbr' 
        filelisthed = glob.glob(path_balance+'\\*.hed')

        key_hed = lambda s: s.rsplit('_')[-3]    # Con esto selecciono el escenario con el cual generare grupos
        Scenario = []

        zones = self.zones  # Zone Budget Zones
        aliases = {1: 'P01',2: 'P02',3: 'P03',4:'P07',5:'P08',6:'L01',7:'L02',8:'L05',9:'L06',10:'L09',11:'L10',12:'L12'}
        Shac = len(zones)

        cell_A = 200*200    # Tamaño celda, info que se debe extraer manualmente de la grilla MODFLOW
        rows = 267          # Cantidad de filas, info que se puede extraer de la grilla MODFLOW, el .dis, .zbr o el .zb_zones
        columns = 373      # Cantidad de columnas, info que se puede extraer de la grilla MODFLOW, el .dis, .zbr o el .zb_zones

        # Leer archivo .DIS para extraer info de TOP y BOTTOM
        f = open(Pth_DIS,'r')
        DIS_T = []
        DIS_B = []

        count = 0
        for line in f:
            if 'TOP' in line or 'BOTM' in line:
                count += 1
            if '#' in line:
                continue
            if count == 1:
                line = line[1:]
                line = line.split('  ')
                if line == ['']:
                    continue
                else:
                    line = [float(x) for x in line]
                    DIS_T.append(line)
            if count == 2:
                line = line[1:]
                line = line.split('  ')
                if line == ['']:
                    continue
                else:
                    line = [float(x) for x in line]
                    DIS_B.append(line)
            if 'NSTEP' in line:
                break
        f.close

        # Arreglo de info row,columns
        DIS_B = np.array(list(chain(*DIS_B)))
        DIS_B.resize((rows, columns), refcheck=False)

        DIS_T = np.array(list(chain(*DIS_T)))
        DIS_T.resize((rows, columns), refcheck=False)

        # Leer archivo .ZBR para extraer info de ZoneBudgets  
        fp = open(Pth_ZB, 'r')
        lines = fp.readlines()

        data = []
        for line in lines[2:]:
            data.append([int(v) for v in line.split()])
        fp.close()
        
        Zones = np.array(list(chain(*data)))
        Zones.resize((rows,columns), refcheck=False)

        # Extraer Ss y Sy a partir de .upw
        f = open(Pth_UPW,'r')
        Values_Ss = []

        lines_to_read = list(range(20316, 30462))
        for position, line in enumerate(f):
            if position in lines_to_read:
                line = line[2:]
                line = line.split('  ')
                line = [float(x) for x in line]
                Values_Ss.append(line)    
        f.close

        Ss_mod = np.array(list(chain(*Values_Ss)))
        Ss_mod.resize((rows,columns), refcheck=False)

        f = open(Pth_UPW,'r')
        Values_Sy = []
        lines_to_read = list(range(30463, 40609))

        for position, line in enumerate(f):
            if position in lines_to_read:
                line = line[2:]
                line = line.split('  ')
                line = [float(x) for x in line]
                Values_Sy.append(line)    
        f.close

        Sy_mod = np.array(list(chain(*Values_Sy)))
        Sy_mod.resize((rows,columns), refcheck=False)

        for i in range(len(filelisthed)-1):
            if key_hed(filelisthed[i]) =='S00' or key_hed(filelisthed[i])=='S01':   #Descarto corrida 0 y año base
                pass
            elif key_hed(filelisthed[i]) in Scenario:
                continue
            else:
                Scenario.append(key_hed(filelisthed[i]))

        def find_indices(lst, condition):
            retorno = [x for x, elem in enumerate(lst) if condition(elem)]
            return retorno

        #Guarda las series de volumenes segun shac en cada escenario, VOLSZB[escenario][shac]
        VOLSZB = [[] for i in range(len(Scenario))]

        #Son los archivos .hed agrupados
        subHed = [[] for i in range(len(Scenario))]
            
        for i in range(len(Scenario)):
            # Selecciona los elementos (indices) que comparten escenario
            index_listhed = find_indices(filelisthed, lambda s: s.rsplit('_')[-3]==Scenario[i])
            subHed[i] = filelisthed[index_listhed[0]:index_listhed[len(index_listhed)-1]+1]

        year = [[] for i in range(len(Scenario))]
        anio = [[] for i in range(len(Scenario))]
        week = [[] for i in range(len(Scenario))]
        for f in range(len(Scenario)):
            #volZB = [[] for i in range(Shac+1)]
            volZB = [[] for i in range(Shac)]
            HEAD = []
            for file in subHed[f]:
                filename = os.fsdecode(file)
                hds = filename
                sp = filename[-11:-4]
                cut_ = sp.index("_")+1
                year_ = int(sp[0:4])
                week_ = int(sp[cut_::])
                time_ = year_+round((week_-1)/52,3)
                HedF = bf.HeadFile(hds, precision='single')
                Hd = HedF.get_data(kstpkper=(0,0))
                Hd = Hd[0]
                Hd = np.where(Hd==-999., 0, Hd) #cero para el plot
                Hd = np.where(Hd==-888., 0, Hd) #cero para el plot
                HEAD = Hd
                DIS_B[Hd==0]=0
                Vol_T = (HEAD-DIS_B)*cell_A #nf-bottom por celda tamaño
                Vol_H = np.multiply(Vol_T, Sy_mod) #Multiplica volumen por Sy
                Vol_T[DIS_T<HEAD]=(DIS_T[DIS_T<HEAD]-DIS_B[DIS_T<HEAD])*cell_A
                Vol_H[DIS_T<HEAD] = np.multiply(Vol_T[DIS_T<HEAD], Ss_mod[DIS_T<HEAD]) # Cuando TOP < HEAD, se multiplica por Ss
                Vol_T[DIS_T>=HEAD]=(HEAD[DIS_T>=HEAD]-DIS_B[DIS_T>=HEAD])*cell_A
                Vol_H[DIS_T>=HEAD] = np.multiply(Vol_T[DIS_T>=HEAD], Sy_mod[DIS_T>=HEAD]) # Cuando TOP >= HEAD, se multiplica por Sy
                Vol_T = np.where(Vol_T<0., 0, Vol_T)
                VolT = sum(sum(Vol_T))
                VolH = sum(sum(Vol_H))
                #for i in range(Shac+1):
                for i in range(Shac):
                    ZBud = np.where(Zones != i+1,0, 0)
                    ZBud = np.where(Zones == i+1,1, 0)
                    Vol_z = np.multiply(Vol_H, ZBud)
                    Vol_z = sum(sum(Vol_z))/(10**6)
                    volZB[i].append(Vol_z)
                year[f].append(time_)    
                anio[f].append(year_)
                week[f].append(week_)
                    #volt=sum(volZB) #verificacion de volumen
            print('Volumen Total bajo NF :  ', VolT/10**6, 'Mm3')
            print('Volumen Total Extraible :  ', VolH/10**6, 'Mm3')
            VOLSZB[f] = volZB

        for i in range(Shac):
            Escenarios_Volumen_Freatico = pd.DataFrame()
            #for e in range(1,len(Scenario)):
            for e in range(0,1):   
                Escenarios_Volumen_Freatico[Scenario[e] + 'Volumen - [Mm3]'] = VOLSZB[e][i]    #Aca es importante tener las zones ordenadas segun los ordenes de shac 
                Escenarios_Volumen_Freatico['Year'] = anio[e]
                Escenarios_Volumen_Freatico['Week'] = week[e]
                Escenarios_Volumen_Freatico.to_csv(os.path.join(Path_out,'Volumen - SHAC - '+zones[i]+'.csv'))
