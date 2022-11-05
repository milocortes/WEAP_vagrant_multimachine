import glob
import os


all_lines = []
with open('log_execution.txt') as f:
    for line in f:
      all_lines.append(line.replace("\n",""))

all_lines = ",".join(all_lines)

os.chdir(r"C:\Users\vagrant\Documents\WEAP Areas\Ligua_Petorca_WEAP_MODFLOW_RDM\NWT_RDM_v22")

acumula_asteriscos = "|"
cuenta_files = 0
cuenta_anios = 0

start_year = 1979
final_year = 2050

anios_total = range(start_year,final_year)

ultimo_anio = start_year

for anio_init in [str(i) for i in anios_total]:
    cuenta_files = len(glob.glob(f"*_{anio_init}_*"))
    if cuenta_files > 200:
        acumula_asteriscos += "#"
        cuenta_anios += 1
        ultimo_anio = anio_init
    else:
        acumula_asteriscos += " "
acumula_asteriscos += "|" + f" {ultimo_anio}-{final_year} "  +str(round((cuenta_anios/len(anios_total))*100,2)) + "%"

print(f"Run Id executed : {all_lines}")
print(acumula_asteriscos)
