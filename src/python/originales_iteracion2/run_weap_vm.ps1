param($p1, $p2)

$dim_exp_design = [int]($p1)
$total_number_vm = [int]($p2)

function valores_array($n,$total_mv,$mv){
   $chunk = [int][Math]::Floor($n/$total_mv)

   $rango_inicio = $chunk*($mv-1) + 1

   if(-Not ($mv -eq $total_mv)){
       $rango_final = $rango_inicio + ($chunk-1)
   }else{
       $rango_final = $n
   }
   return $rango_inicio..$rango_final
}

function run_weap(){

  $vm = [int]((hostname) -replace '\D+(\d+)','$1') - 1

  Write-Host "Comenzamos la ejecución en la Máquina Virtual " $vm

  Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

  $experimentos = valores_array $dim_exp_design $total_number_vm $vm
  foreach($experimento in $experimentos){
      Write-Host "Run experiment : "$experimento
      Get-Date -Format "dddd MM/dd/yyyy HH:mm K"
      python run_LP_model.py $experimento
      Write-Host "Experiment "$experimento " finished"
      Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

    Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
    Write-Host "-------   SEND EXPERIMENT DATA TO NFS STORAGE ------------"
    Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

    Copy-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP\*" -Destination "S:WEAP" -recurse -Force
    Copy-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW\*"  -Destination "S:MODFLOW" -recurse -Force
    Remove-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\WEAP\*"  -recurse -Force
    Remove-Item "C:\Users\vagrant\Documents\WEAP_vagrant_multimachine\src\output\MODFLOW\*" -recurse -Force
  }
}

Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
Write-Host "------------   Mount NFS service --------------"
Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

New-PSDrive S -PsProvider FileSystem -Root \\10.0.0.200\storage

Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"
Write-Host "---------------   RUN WEAP -------------------"
Write-Host "*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*"

run_weap


