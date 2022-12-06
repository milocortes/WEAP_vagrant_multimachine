import pandas as pd
import sys
from utils import *
import warnings
warnings.filterwarnings('ignore')

if __name__ == "__main__":

    ## Guarda en el archivo log la ejecución en curso
    file_object = open("log_execution.txt", 'a')
    #file_object.write(f"{run_id}\n")
    file_object.close()
    
    #### Cargamos datos
    acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
    activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
    clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
    demanda = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Demanda")

    acciones_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")
    clima_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")

    start_year = 1979
    end_year = 2059 ###

    output_path_WEAP = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP"
    output_path_MODFLOW = r"C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW"

    ZB = ['Zones.zbr', 'Zones_RL.zbr']
    zones = ['P01','P02','P03','P07','P08','L01','L02','L05','L06','L09','L10','L12']
    path_WEAP = r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM"
    
    #### Inicializamos el modelo 
    weap_model = LP_WEAP(acciones, activaciones, clima, demanda, acciones_valores, 
                        clima_valores, start_year, end_year, output_path_WEAP, output_path_MODFLOW, path_WEAP, ZB, zones)

    #### Generamos el data frame de futuros
    weap_model.build_future_2_id_df()