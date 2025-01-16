wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.18.0/opensearch-2.18.0-linux-x64.tar.gz
tar -xvf opensearch-2.18.0-linux-x64.tar.gz
cd opensearch-2.18.0/

./opensearch-tar-install.sh
export OPENSEARCH_INITIAL_ADMIN_PASSWORD="admin"
curl -X GET https://localhost:9200 -u 'admin:admin' --insecure
curl -X GET https://localhost:9200/_cat/plugins?v -u 'admin:admin' --insecure

cd config/
CONFIG_FILE="opensearch.yml"
cat >>"$CONFIG_FILE" <<EOF
network.host: 0.0.0.0
discovery.type: single-node
plugins.security.disabled: false
EOF

CONFIG_FILE="jvm.options"
sed -i '22,23d' "$CONFIG_FILE"
cat >>"$CONFIG_FILE" <<EOF
-Xms4g
-Xmx4g
EOF

cd ..
export OPENSEARCH_JAVA_HOME=/jdk
cd config/
openssl genrsa -out root-ca-key.pem 2048
openssl req -new -x509 -sha256 -key root-ca-key.pem -subj "/C=CA/ST=ONTARIO/L=TORONTO/O=ORG/OU=UNIT/CN=ROOT" -out root-ca.pem -days 730
openssl genrsa -out admin-key-temp.pem 2048
openssl pkcs8 -inform PEM -outform PEM -in admin-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out admin-key.pem
openssl req -new -key admin-key.pem -subj "/C=CA/ST=ONTARIO/L=TORONTO/O=ORG/OU=UNIT/CN=A" -out admin.csr
openssl x509 -req -in admin.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out admin.pem -days 730
openssl genrsa -out node1-key-temp.pem 2048
openssl pkcs8 -inform PEM -outform PEM -in node1-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out node1-key.pem
openssl req -new -key node1-key.pem -subj "/C=CA/ST=ONTARIO/L=TORONTO/O=ORG/OU=UNIT/CN=node1.dns.a-record" -out node1.csr
echo 'subjectAltName=DNS:node1.dns.a-record' > node1.ext
openssl x509 -req -in node1.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out node1.pem -days 730 -extfile node1.ext
rm *temp.pem *csr *ext

CONFIG_FILE="opensearch.yml"
cat >>"$CONFIG_FILE" <<EOF
plugins.security.ssl.transport.pemcert_filepath: node1.pem
plugins.security.ssl.transport.pemkey_filepath: node1-key.pem
plugins.security.ssl.transport.pemtrustedcas_filepath: root-ca.pem
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: node1.pem
plugins.security.ssl.http.pemkey_filepath: node1-key.pem
plugins.security.ssl.http.pemtrustedcas_filepath: root-ca.pem
plugins.security.allow_default_init_securityindex: true
plugins.security.authcz.admin_dn:
  - 'CN=A,OU=UNIT,O=ORG,L=TORONTO,ST=ONTARIO,C=CA'
plugins.security.nodes_dn:
    - 'CN=node1.dns.a-record,OU=UNIT,O=ORG,L=TORONTO,ST=ONTARIO,C=CA'
plugins.security.audit.type: internal_opensearch
plugins.security.enable_snapshot_restore_privilege: true
plugins.security.check_snapshot_restore_write_privileges: true
plugins.security.restapi.roles_enabled: [all_access]
EOF

cd ..
cd plugins/opensearch-security/tools
chmod 755 *.sh
OPENSEARCH_JAVA_HOME=~/scylladb/scripts/opensearch-2.18.0/jdk ./hash.sh

cd ../../../
cd config/opensearch-security
CONFIG_FILE="internal_users.yml"
sed -i '13,63d' "$CONFIG_FILE"
cat >>"$CONFIG_FILE" <<EOF
admin:
  hash: ""
  reserved: true
  backend_roles:
  - "admin"
  description: "admin user"
EOF