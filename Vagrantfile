# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  config.vm.synced_folder ".", "/home/vagrant/tootexporter"

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update -y
    apt-get install python3 python3-pip python3-dev libpq-dev redis-server -y
    cd tootexporter/
    gem install foreman
    pip3 install -r requirements.txt
    # postgresql
    sudo apt-get install -y postgresql
    sudo echo "host all all all md5" >> /etc/postgresql/9.3/main/pg_hba.conf
    sudo echo "listen_addresses = '*'" >> /etc/postgresql/9.3/main/postgresql.conf
    sudo service postgresql restart
    # create db
    echo "alter role postgres with password 'pass';create database tootexporter;" |  sudo -u postgres psql
    cat schema.sql |  sudo -u postgres psql -d tootexporter
  SHELL
end

