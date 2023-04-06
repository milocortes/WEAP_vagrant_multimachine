import pandas as pd
import sys
from utils import *
import warnings
warnings.filterwarnings('ignore')

## Recibe run_id
run_id = int(sys.argv[1]) - 1

all_lines = []
with open('log_execution.txt') as f:
    for line in f:
      all_lines.append(line.replace("\n",""))

if not all_lines:

    if __name__ == "__main__":

        ## Guarda en el archivo log la ejecución en curso
        file_object = open("log_execution.txt", 'a')
        file_object.write(f"{run_id}\n")
        file_object.close()
        
        #### Cargamos datos
        acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones")
        activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones2")
        clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
        demanda = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda")
        demanda_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda2")

        start_year = 2015
        end_year = 2060 ###

        output_path_WEAP = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP"
        output_path_MODFLOW = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW"

        ZB = ['Zones.zbr', 'Zones_RL.zbr']
        zones = ['P01','P02','P03','P07','P08','L01','L02','L05','L06','L09','L10','L12']
        path_WEAP = r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM"
        ZR = ['Agricola_ZR02_P01', 'Agricola_ZR05_L01', 'Agricola_ZR05_P02', 'Agricola_ZR06_L02', 'Agricola_ZR06_P03', 'Agricola_ZR07_L05', 'Agricola_ZR07_P07', 'Agricola_ZR08_L06', 
              'Agricola_ZR08_P08', 'Agricola_ZR09_L09', 'Agricola_ZR10_L10_L12']
        Sc = ['L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L07', 'L08', 'L09', 'L10', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08']
        
        #### Inicializamos el modelo 
        weap_model = LP_WEAP(acciones, activaciones, clima, demanda, start_year, end_year, output_path_WEAP, output_path_MODFLOW, path_WEAP, ZB, zones, ZR, Sc, demanda_valores)

        #### Generamos el data frame de futuros
        weap_model.build_future_id_df()

        #### Corremos el modelo
        weap_model.run_WEAP_model(run_id)

        #### Procesamiento MODFLOW
        weap_model.processing_MODFLOW()   

## Verificamos si el experimento ya fue ejecutado
elif str(run_id) in all_lines[:-1]:
    print(f"El experimento {run_id} ya fue ejecutado")

## Verificamos si el experimento tiene que ser reanudado
elif  str(run_id) == all_lines[-1]:
    print(f"Reanudamos ejecución del experimento {run_id}")

    if __name__ == "__main__":

        #### Cargamos datos
        acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones")
        activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones2")
        clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
        demanda = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda")
        demanda_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda2")

        start_year = 2015
        end_year = 2060 ###

        output_path_WEAP = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP"
        output_path_MODFLOW = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW"

        ZB = ['Zones.zbr', 'Zones_RL.zbr']
        zones = ['P01','P02','P03','P07','P08','L01','L02','L05','L06','L09','L10','L12']
        path_WEAP = r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM"
        ZR = ['Agricola_ZR02_P01', 'Agricola_ZR05_L01', 'Agricola_ZR05_P02', 'Agricola_ZR06_L02', 'Agricola_ZR06_P03', 'Agricola_ZR07_L05', 'Agricola_ZR07_P07', 'Agricola_ZR08_L06', 
              'Agricola_ZR08_P08', 'Agricola_ZR09_L09', 'Agricola_ZR10_L10_L12']
        Sc = ['L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L07', 'L08', 'L09', 'L10', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08']

        #### Inicializamos el modelo 
        weap_model = LP_WEAP(acciones, activaciones, clima, demanda, start_year, end_year, output_path_WEAP, output_path_MODFLOW, path_WEAP, ZB, zones, ZR, Sc, demanda_valores)

        #### Generamos el data frame de futuros
        weap_model.build_future_id_df()

        #### Corremos el modelo
        weap_model.run_WEAP_model(run_id)

        #### Procesamiento MODFLOW
        weap_model.processing_MODFLOW()

## Ejecutamos el nuevo experimento
else:

    if __name__ == "__main__":

        ## Guarda en el archivo log la ejecución en curso
        file_object = open("log_execution.txt", 'a')
        file_object.write(f"{run_id}\n")
        file_object.close()

        #### Cargamos datos
        acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones")
        activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones2")
        clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
        demanda = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda")
        demanda_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda2")

        start_year = 2015
        end_year = 2060

        output_path_WEAP = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP"
        output_path_MODFLOW = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW"

        ZB = ['Zones.zbr', 'Zones_RL.zbr']
        zones = ['P01','P02','P03','P07','P08','L01','L02','L05','L06','L09','L10','L12']
        path_WEAP = r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM"
        ZR = ['Agricola_ZR02_P01', 'Agricola_ZR05_L01', 'Agricola_ZR05_P02', 'Agricola_ZR06_L02', 'Agricola_ZR06_P03', 'Agricola_ZR07_L05', 'Agricola_ZR07_P07', 'Agricola_ZR08_L06', 
              'Agricola_ZR08_P08', 'Agricola_ZR09_L09', 'Agricola_ZR10_L10_L12']
        Sc = ['L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L07', 'L08', 'L09', 'L10', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08']

        #### Inicializamos el modelo 
        weap_model = LP_WEAP(acciones, activaciones, clima, demanda, start_year, end_year, output_path_WEAP, output_path_MODFLOW, path_WEAP, ZB, zones, ZR, Sc, demanda_valores)

        #### Generamos el data frame de futuros
        weap_model.build_future_id_df()

        #### Corremos el modelo
        weap_model.run_WEAP_model(run_id)

        #### Procesamiento MODFLOW
        weap_model.processing_MODFLOW()
