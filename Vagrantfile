# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
	# Base box to build off, and download URL for when it doesn't exist on the user's system already
	config.vm.box = "ubuntu/focal64"

	config.vm.provider "virtualbox" do |v|
		v.memory = 4096
	end

	# Boot with a GUI so you can see the screen. (Default is headless)
	# config.vm.boot_mode = :gui
	
	# Assign this VM to a host only network IP, allowing you to access it
	# via the IP.
	# config.vm.network "33.33.33.10"
	
	# Forward a port from the guest to the host, which allows for outside
	# computers to access the VM, whereas host only networking does not.
	config.vm.network "forwarded_port", guest: 8060, host: 8060
	
	# Share an additional folder to the guest VM.
	config.vm.synced_folder ".", "/home/vagrant/geocoder"
	
	# Enable provisioning with a shell script.
	config.vm.provision :shell, :path => "etc/install/install.sh", :args => "geocoder"
end
