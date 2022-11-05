import glob
import os

os.chdir(r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM\NWT_RDM_v22")

acumula_asteriscos = "|"
cuenta_files = 0
cuenta_anios = 0

anios_total = range(1979,2050)

for anio_init in [str(i) for i in anios_total]:
    cuenta_files = len(glob.glob(f"*_{anio_init}_*"))
    if cuenta_files > 200:
        acumula_asteriscos += "#"
        cuenta_anios += 1
    else:
        acumula_asteriscos += " "
acumula_asteriscos += "|" + str(round((cuenta_anios/len(anios_total))*100,2)) + "%"

print(acumula_asteriscos)
