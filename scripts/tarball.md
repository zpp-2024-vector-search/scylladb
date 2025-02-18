run script: bash tarball.sh
enter password: admin
paste the generated hash into the internal_users.yml file in line 14 in the hash field
it should look something like this:
---
# This is the internal user database
# The hash value is a bcrypt hash and can be generated with plugin/tools/hash.sh

_meta:
   type: "internalusers"
   config_version: 2

# Define your internal users here

admin:
   hash: "$2y$1EXAMPLEQqwS8TUcoEXAMPLEeZ3lEHvkEXAMPLERqjyh1icEXAMPLE."
   reserved: true
   backend_roles:
   - "admin"
   description: "Admin user"

then execute the commands: cd opensearch-2.18.0/bin
./opensearch
open a new terminal and execute:
OPENSEARCH_JAVA_HOME=~/scylladb/scripts/opensearch-2.18.0/jdk ./securityadmin.sh -cd ~/scylladb/scripts/opensearch-2.18.0/config/opensearch-security/ -cacert ~/scylladb/scripts/opensearch-2.18.0/config/root-ca.pem -cert ~/scylladb/scripts/opensearch-2.18.0/config/admin.pem -key ~/scylladb/scripts/opensearch-2.18.0/config/admin-key.pem -icl -nhnv
stop and restart the running OpenSearch process to apply the changes
curl localhost:9200 -u admin:admin -k