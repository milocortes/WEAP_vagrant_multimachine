import pandas as pd
import win32com.client as win32
from utils import *


#### Cargamos datos
acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones")
activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Activacion")
clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")

acciones_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones2")
clima_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima2")

start_year = 1979
end_year = 1983

#### Inicializamos el modelo 
weap_model = LP_WEAP(acciones, activaciones, clima, acciones_valores, clima_valores, start_year, end_year)

#### Generamos el data frame de futuros
weap_model.build_future_id_df()

#### Corremos el modelo
weap_model.run_WEAP_model(88)

#### Exportamos resultados de WEAP
ruta_WEAP = "C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM"
ruta_export = "C:\Users\hermi\OneDrive\Documents\egtp\ligua_petorca\WEAP_vagrant_multimachine\src\output\WEAP"

weap_model.processing_MODFLOW(ruta_WEAP, ruta_export)