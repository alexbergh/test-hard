#!/bin/bash

CERT_DIR="./config/wazuh-indexer/certs"
mkdir -p $CERT_DIR

# 1. Генерация Root CA
openssl genrsa -out $CERT_DIR/root-ca.key 2048
openssl req -new -x509 -sha256 -key $CERT_DIR/root-ca.key -out $CERT_DIR/root-ca.pem -days 3650 -subj "/C=US/ST=State/L=City/O=Organization/CN=Wazuh Root CA"

# 2. Генерация admin сертификата
openssl genrsa -out $CERT_DIR/admin.key 2048
openssl req -new -key $CERT_DIR/admin.key -out $CERT_DIR/admin.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=admin"
openssl x509 -req -in $CERT_DIR/admin.csr -CA $CERT_DIR/root-ca.pem -CAkey $CERT_DIR/root-ca.key -CAcreateserial -out $CERT_DIR/admin.pem -days 3650 -sha256

# 3. Генерация node-1 сертификата
openssl genrsa -out $CERT_DIR/node-1.key 2048
openssl req -new -key $CERT_DIR/node-1.key -out $CERT_DIR/node-1.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=node-1"
openssl x509 -req -in $CERT_DIR/node-1.csr -CA $CERT_DIR/root-ca.pem -CAkey $CERT_DIR/root-ca.key -CAcreateserial -out $CERT_DIR/node-1.pem -days 3650 -sha256

# 4. Установка правильных прав
chmod 644 $CERT_DIR/*.pem
chmod 600 $CERT_DIR/*.key

# 5. Очистка временных файлов
rm -f $CERT_DIR/*.csr $CERT_DIR/root-ca.srl

echo "Сертификаты успешно сгенерированы в $CERT_DIR"
