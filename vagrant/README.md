# Multi Machine windows 10 box with vagrant

## Creación de máquina virtual base

Para la creación de la máquina virtual base utilizamos la box pública de Vagrant ```windows-10-1709-base-winrm``` con sistema operativo Windows 10 ([here](https://app.vagrantup.com/eyewaretech/boxes/windows-10-1709-base-winrm "Title")). La ventaja de esta box es que usan ```vagrant rdp``` para acceder a la VM usando Windows Remote Desktop Connection. Para usar la box ejecutamos las instrucciones:

```
vagrant init eyewaretech/windows-10-1709-base-winrm --box-version 0.0.1
vagrant up
```

Una vez creada la VM, accedemos y realizamos los siguientes pasos:
* Instalar WEAP:
	* En la carpeta ```_Backup``` agregamos los archivos txt y zip de las últimas versiones del modelo LP.
	* Abrimos el archivo ```.Weap```.
* Instalar ambiente Anaconda para utilizar python.
* Configuración para ejecutar instrucciones remotas con winrm:
	* Desactivar Firewalls.
	* Cambiar el tipo de conexión de red a privada. Esto lo hacemos desde PowerShell ejecutando la instrucción ```Set-NetConnectionProfile -NetworkCategory Private```
	* Restaurar la configuración de listener ejecutando las siguientes instrucciones ([here](https://docs.microsoft.com/en-us/troubleshoot/windows-client/system-management-components/errors-when-you-run-winrm-commands "Title")):
	 ```
	 # Run the following command to restore the listener configuration:
	 winrm invoke Restore winrm/Config
	 # Run the following command to perform a default configuration of 
	 # the Windows Remote Management service and its listener:
	 winrm quickconfig
	 ```


## Maquina virtual a box de Vagrant
Convertimos la maquina virtual (VM) que actualmente está en VirtualBox en una box de Vagrant:

```
 vagrant package --base=v_windows_10_base --output=v_windows_10_base.box
```

La VM en VirtualBox se llama ```v_windows_10_base``` y la box se llamanrá ```v_windows_10_base.box```.

Ahora copiamos la box a nuestro ambiente local de Vagrant.

```
 vagrant box add .\v_windows_10_base.box --name v_windows_10_base
```

Creamos un Vagrantfile minimal al ejecutar la instrucción:

```
 vagrant init -m
```

Despues de esto, editamos el Vagrantfile y creamos tantas áreas de configuración como VM's necesitemos. Para este ejemplo, crearemos tres VM. Dentro de cada configuración definimos la dirección IP a cada máquina en una red privada. Con ```vm.box``` asignamos qué box será utilizada en la configuración de cada VM. En este caso, las tres máquinas tendrán la box de la VM ```v_win_10_base``` que ya estaba creada en VirtualBox. 

El Vagrantfile quedaría de la siguiente manera:
```
# -*- mode: ruby -*-
# vi: set ft=ruby :

NODE_COUNT = 4
Vagrant.configure("2") do |config|
  #Configure the machines
  #config.vm.network "forwarded_port" , host: 33390 , guest: 3389   
  config.vm.communicator = "winrm"
  config.winrm.username = "vagrant"
  config.winrm.password = "vagrant"
	
  config.vm.guest = :windows
  config.windows.halt_timeout = 600

  (1..NODE_COUNT).each do |i|

    config.vm.define "node#{i}" do |subconfig|
    subconfig.vm.box = "v_windows_10_base"
    subconfig.vm.hostname = "vm#{i}"
    subconfig.vm.network "private_network", ip: "10.0.0.#{i+10}"

    end
  
   end
end
```

Ahora ejecutamos la instrucción para levantar y provisionar las VM:

```
vagrant up
```


## Eliminar una box

Para eliminar una box: 

```
vagrant box remove [BOX_NAME]
vagrant box remove v_windows_10_base
```

## Configuración en la máquina master

La máquina master se encargará de realizar solicitudes de procesamiento a las máquinas workers. Para esto, inicialmente necesita agregar a las máquinas workers como Trusted Hosts:

```
winrm set winrm/config/client '@{TrustedHosts="[VM_NAME]"}'
```

El comando anterior sólo permite agregar un Trusted Hosts. La siguiente instrucción de PowerShell nos permite agregar múltiples hosts a la lista:

```
Set-Item WSMan:\localhost\Client\TrustedHosts -Value 'machineA,machineB'
```

Con la siguiente instrucción se ejecutan instrucciones remotos:

```
winrs -r:http://vm2:5985 -p:vagrant -u:testdom\vagrant "dir"
winrs -r:http://vm3:5985 -p:vagrant -u:testdom\vagrant "python prueba.py"
```

## Recursos

Click [here](https://app.vagrantup.com/eyewaretech/boxes/windows-10-1709-base-winrm "Title") vagrant box configurado con winrm.

Click [here](https://sites.google.com/a/orabuntu-lxc.com/brandydandyoracle/openvswitch-ovs/configuring-virtualbox-vms-for-openvswitch-networking "Title") OpenvSwitch Networking.

Click [here](https://docs.openvswitch.org/en/latest/intro/install/windows/ "Title") OpenvSwitch Networking on Windows.

Click [here](https://manski.net/2016/09/vagrant-multi-machine-tutorial/ "Title") Vagrant tutorial-From Nothing to Multi-Machine.

Click [here](https://medium.com/oracledevs/two-birds-with-one-home-cloned-vagrant-multi-machines-2ee5ba75fad8 "Title") Two birds with one home — cloned Vagrant multi-machines!

Click [here](https://www.youtube.com/watch?v=xxKmakXetv4 "Title") How to set up a client and server in Virtual Box.


Click [here](https://docs.microsoft.com/en-us/troubleshoot/windows-client/system-management-components/errors-when-you-run-winrm-commands "Title") Errors when you run WinRM commands to check local functionality in a Windows Server 2008 environment.