1. Setup for Celery-RabbitMQ for background task management

2. Installation Packages:

3.  sudo apt update
    apt install celery
    sudo apt install rabbitmq-server
    sudo systemctl enable rabbitmq-server
    sudo systemctl start rabbitmq-server
    
    sudo rabbitmqctl add_user hci hci@123
    sudo rabbitmqctl add_vhost hcivhost
    sudo rabbitmqctl set_permissions -p hcivhost hci ".*" ".*" ".*"
