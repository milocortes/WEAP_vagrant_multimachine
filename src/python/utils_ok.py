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

######################################
####    Clase de procesamiento    ####
######################################

class LP_WEAP(object):
    """docstring for ."""

    def __init__(self, acciones, activaciones, clima, demanda, start_year, end_year, output_path_WEAP,output_path_MODFLOW, path_WEAP, ZB, zones, ZR, Sc, demanda_valores):
        self.acciones = acciones
        self.activaciones = activaciones
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
        acciones = self.acciones
        future = acciones.merge(self.clima, how = "cross")[["Acciones","GCM"]].reset_index(drop=True)
        future = future.merge(self.demanda, how = "cross")[["Acciones","GCM","Demanda"]].reset_index(drop=True)
        future["ID"] = range(future.shape[0])   
        future = future[["ID", "Acciones", "GCM","Demanda"]]

        self.future = future
        future.to_csv('RunIDs.csv')
    
    def run_WEAP_model(self, action_id):
        self.action_id = action_id

        # Open WEAP sesion
        WEAP = win32.Dispatch("WEAP.WEAPApplication")
        WEAP.ActiveArea = "Ligua_Petorca_WEAP_MODFLOW_RDM"
        WEAP.ActiveScenario = WEAP.Scenarios("Current Accounts")
        WEAP.BaseYear = self.start_year
        WEAP.EndYear = self.end_year

        # Build Variable Branches
        print(self.future.iloc[action_id]["Acciones"], self.future.iloc[action_id]["GCM"], self.future.iloc[action_id]["Demanda"])

        print("-------------------------")
        print("******   CLIMA   ********")
        print("-------------------------")

        gcm = self.future.iloc[action_id]["GCM"]

        for k in self.ZR:
            Branch_ZR_P = "\\Demand Sites and Catchments\\" + str(k) + ":Precipitation"
            Branch_ZR_MinT = "\\Demand Sites and Catchments\\" + str(k) + ":Min Temperature"
            Branch_ZR_MaxT = "\\Demand Sites and Catchments\\" + str(k) + ":Max Temperature"
            if gcm == 'Clima historico':
                RF_ZR_P = 'ReadFromFile(Datos\\variables climaticas LPQ\pr_Agro_LPQ_Corregida.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)'                
                RF_ZR_MinT = 'ReadFromFile(Datos\\variables climaticas LPQ\\tmin_Agro_LPQ.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmin\\Agricola_' + str(k[14:15]) + str(k[11:13])
                RF_ZR_MaxT = 'ReadFromFile(Datos\\variables climaticas LPQ\\tmax_Agro_LPQ.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmax\\Agricola_' + str(k[14:15]) + str(k[11:13])
            else:
                RF_ZR_P = 'ReadFromFile(Datos\GCMs\pr_LPQ_' + gcm + '.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)'
                RF_ZR_MinT = 'ReadFromFile(Datos\GCMs\\tasmin_LPQ_' + gcm + '.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmin\\Agricola_' + str(k[14:15]) + str(k[11:13])
                RF_ZR_MaxT = 'ReadFromFile(Datos\GCMs\\tasmax_LPQ_' + gcm + '.csv, "Agricola_' + str(k[14:15]) + str(k[11:13]) + '", , Average, , Interpolate)+Key\Ajuste_T_MABIA\Tmax\\Agricola_' + str(k[14:15]) + str(k[11:13])

            WEAP.BranchVariable(Branch_ZR_P).Expression = RF_ZR_P # Precipitation
            WEAP.BranchVariable(Branch_ZR_MinT).Expression = RF_ZR_MinT # Min Temperature
            WEAP.BranchVariable(Branch_ZR_MaxT).Expression = RF_ZR_MaxT # Max Temperature

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

        delta_riego = round(self.demanda_valores.query(f"Demanda=='{demand}'")['Areas Riego'].values[0],2)
        delta_poblacion = round(self.demanda_valores.query(f"Demanda=='{demand}'")['Poblacion'].values[0],2)

        WEAP.Branch('\\Key Assumptions\\VariacionAreasRiego').Variables(1).Expression = f"Interp( 1979,1,  2021,1, 2030,{delta_riego})"
        WEAP.Branch('\\Key Assumptions\\VariacionPoblacion').Variables(1).Expression = f"Step( 1979,1,  2021,{delta_poblacion})"
        
        print("----------------------------")
        print("******   ACCIONES   ********")
        print("----------------------------")
        WEAP.ActiveScenario = WEAP.Scenarios("Reference")

        policy = self.future.iloc[action_id]["Acciones"]
        #print(policy, policy_year)
        
        if self.future.iloc[action_id]["Acciones"] == "Sin implementacion de acciones":
            for i in self.activaciones["BranchVariable"]:
                if i == "\Key Assumptions\Factor_Prorrateo":
                    WEAP.BranchVariable(i).Expression='1'
                elif i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Estero_Alicahue:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Oriente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Cabildo:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Pueblo:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Costa:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Pedernal:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Petorca_Oriente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Petorca_Poniente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Estero_LaPatagua\Flow Requirements\Estero_Patagua:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Sobrante\Flow Requirements\Rio_Del_Sobrante:Minimum Flow Requirement':       
                    WEAP.BranchVariable(i).Expression='0'
                else:
                    WEAP.BranchVariable(i).Expression='2200'
                #print(i, policy_year)
        else:
            ac =  self.future.iloc[action_id]["Acciones"]
            acciones_2_agrupado = self.activaciones.groupby("Acciones")
            policy_year = self.activaciones.query(f"Acciones=='{policy}'")['Activacion'].values[0]
        
            for i in acciones_2_agrupado.get_group(ac)["BranchVariable"]:
                WEAP.BranchVariable(i).Expression=f"{policy_year}"
                #print(i, policy_year)

            acciones_2_agrupado_index = list(acciones_2_agrupado.get_group(ac).index)
            sin_cambios = list(set(list(self.activaciones.index)).symmetric_difference(acciones_2_agrupado_index))

            for i in self.activaciones.iloc[sin_cambios]["BranchVariable"]:
                if i == "\Key Assumptions\Factor_Prorrateo":
                    WEAP.BranchVariable(i).Expression='1'
                elif i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Estero_Alicahue:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Oriente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Cabildo:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Pueblo:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_LaLigua\Flow Requirements\Rio_Ligua_Costa:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Pedernal:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Petorca_Oriente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Petorca\Flow Requirements\Rio_Petorca_Poniente:Minimum Flow Requirement' or i == '\Supply and Resources\River\Estero_LaPatagua\Flow Requirements\Estero_Patagua:Minimum Flow Requirement' or i == '\Supply and Resources\River\Rio_Sobrante\Flow Requirements\Rio_Del_Sobrante:Minimum Flow Requirement':
                    WEAP.BranchVariable(i).Expression='0'
                else:
                    WEAP.BranchVariable(i).Expression='2200'
                #print(i)
        
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

        version = f'run_id_{self.action_id}'

        print("---------------------------------------------------------")
        print("******  EXPORT MODFLOW RESULTS - VOLUMENES SHAC  ********")
        print("---------------------------------------------------------")

        # Leer archivo .hed o .cbb para extraer flujo en las celdas y volumenes
        nombre_carpeta_MF = 'NWT_RDM_v23_2014'

        # Se crea ruta según runID
        dir_version = os.path.join(self.output_path_MODFLOW, version)
        if not os.path.isdir(dir_version):
            os.mkdir(dir_version)

        Path_out = os.path.join(self.output_path_MODFLOW, version, 'VOLUMEN')
        if not os.path.isdir(Path_out):
            os.mkdir(Path_out)

        # Lectura de resultados y archivos nativos
        prj = 'con_dren_sin_aisladas_NWT'
        path_balance = os.path.join(self.path_WEAP,nombre_carpeta_MF)
        Pth_DIS = os.path.join(path_balance, prj + '.dis')#path_balance+'\\'+prj+'.dis'
        Pth_UPW = os.path.join(path_balance, prj + '.upw')#path_balance+'\\'+prj+'.upw'
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

        lines_to_read = list(range(20317, 30463))
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
        lines_to_read = list(range(30464, 40611))

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
            #print('Volumen Total bajo NF :  ', VolT/10**6, 'Mm3')
            #print('Volumen Total Extraible :  ', VolH/10**6, 'Mm3')
            VOLSZB[f] = volZB

        for i in range(Shac):
            Escenarios_Volumen_Freatico = pd.DataFrame()
            #for e in range(1,len(Scenario)):
            for e in range(0,1):   
                Escenarios_Volumen_Freatico[Scenario[e] + 'Volumen - [Mm3]'] = VOLSZB[e][i]    #Aca es importante tener las zones ordenadas segun los ordenes de shac 
                Escenarios_Volumen_Freatico['Year'] = anio[e]
                Escenarios_Volumen_Freatico['Week'] = week[e]
                Escenarios_Volumen_Freatico.to_csv(os.path.join(Path_out,'Volumen - SHAC - '+zones[i]+'.csv'))
