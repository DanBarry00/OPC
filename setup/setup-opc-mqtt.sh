sudo apt update
sudo apt install -y mosquitto mosquitto-clients

sudo tee /etc/mosquitto/conf.d/opc.conf >/dev/null <<'EOF'
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

sudo mosquitto_passwd -c -b /etc/mosquitto/passwd opc 'password'

sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/passwd

sudo systemctl restart mosquitto.service
