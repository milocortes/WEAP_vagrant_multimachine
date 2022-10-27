import pandas as pd
import win32com.client as win32

class LP_WEAP(object):
    """docstring for ."""

    def __init__(self,acciones, activaciones, clima, acciones_valores, clima_valores):
        self.acciones = acciones
        self.activaciones = activaciones
        self.clima = clima
        self.acciones_valores = acciones_valores
        self.clima_valores = clima_valores
        self.policies = None
        self.future_id_df = None

    def build_future_id_df(self):
        policies = acciones.merge(self.activaciones, how="cross")[["Acciones","Activacion"]].iloc[2:].reset_index(drop=True)
        policies.loc[0,"Activacion"] = 2200
        policies["ID"] = range(policies.shape[0])
        policies = policies[["ID","Acciones","Activacion"]]

        future = policies.merge(clima, how="cross")[["Acciones","Activacion","GCM"]].reset_index(drop=True)
        future["ID"] = range(future.shape[0])
        future = future[["ID","Acciones","Activacion","GCM"]]

        self.policies = policies
        self.future = future

    def run_WEAP_branches_future_id(self, action_id):

        # Open WEAP sesion
        WEAP = win32.Dispatch("WEAP.WEAPApplication")
        WEAP.ActiveArea = "Ligua_Petorca_WEAP_MODFLOW_RDM"
        WEAP.ActiveScenario = WEAP.Scenarios("Reference")

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


acciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones")
activaciones = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Activacion")
clima = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima")

acciones_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Acciones2")
clima_valores = pd.read_excel("../datos/Characterization.xlsx",sheet_name="Clima2")


weap_model = LP_WEAP(acciones, activaciones, clima, acciones_valores, clima_valores)
weap_model.build_future_id_df()
weap_model.run_WEAP_branches_future_id(88)
