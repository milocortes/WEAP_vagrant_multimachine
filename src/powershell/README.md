# Ejecución del modelo en PowerShell

Para correr el programa de PowerShell desde cmd, ejecute la siguiente instrucción:
```
powershell ./run_weap_mv.ps1
```

# Instrucciones de administración

Agregar nodos a la lista de TrustedHosts:

```
Set-Item WSMan:\localhost\Client\TrustedHosts -Value 'vm2, vm3, vm4, vm5, vm6, vm7, vm8, vm9’
```

Verifica si fueron agregados los nodos a TrustedHosts:

```
(Get-Item WSMan:\localhost\Client\TrustedHosts).value
```

Lanzar orden ejecución de experimentos WEAP – MODFLOW en las n máquinas worker:

```
foreach($i in 2..6){ Invoke-Command -ComputerName "vm$i" -ScriptBlock {cd C:\Users\vagrant\python_venvs ; 
									.\lp\Scripts\activate ; 
									cd C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\python; 
									powershell './run_weap_vm_rust_server.ps1 384'} -AsJob
                                    }
```

Verificación de procesos activos en las máquinas worker:

```
foreach($i in 2..6){
                    "Verificación procesos vm$i" 
			        Invoke-Command -ComputerName "vm$i" -ScriptBlock {Get-Process powershell*, python*, weap*}
                    }
```
