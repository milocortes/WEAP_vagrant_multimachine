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

  $vm = [int]((hostname) -replace '\D+(\d+)','$1')

  Write-Host "Comenzamos la ejecución en la Máquina Virtual " $vm

  Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

  $experimentos = valores_array 35 5 $vm
  foreach($experimento in $experimentos){
      Write-Host "Run experiment : "$experimento
      Get-Date -Format "dddd MM/dd/yyyy HH:mm K"
      python 2_EjecucionEscenarios_RDM_parameter.py $experimento
      Write-Host "Experiment "$experimento " finished"
      Get-Date -Format "dddd MM/dd/yyyy HH:mm K"

  }
}

run_weap
