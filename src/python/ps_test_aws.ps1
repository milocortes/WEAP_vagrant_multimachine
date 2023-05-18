param($p1)

$num_experimentos = [int]($p1)

function run_weap(){

  $vm = [int]((hostname) -replace '\D+(\d+)','$1') - 1

  Write-Host "Comenzamos la ejecución en la Máquina Virtual " $vm

  Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

  $val = 1

  while($val -ne $num_experimentos){
    Write-Host "Run experiment : "$val
    Get-Date -Format "dddd MM/dd/yyyy HH:mm K"
    python test_minimal_aws.py 
    Write-Host "Experiment "$val " finished"
    $val++
    Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

    Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
    Write-Host "-------   SEND EXPERIMENT DATA TO NFS STORAGE ------------"
    Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

    Copy-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\python\*.json" -Destination "S:WEAP"  -Force
    Remove-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\python\*.json"   -Force

  }
}

Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
Write-Host "------------   Mount NFS service --------------"
Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

New-PSDrive S -PsProvider FileSystem -Root \\10.0.1.200\storage

Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
Write-Host "---------------   RUN WEAP -------------------"
Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

run_weap
