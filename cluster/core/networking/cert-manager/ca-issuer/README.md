This is taken from https://github.com/CrunchyData/postgres-operator-examples/tree/main/kustomize/certmanager/certman

It creates three things:
* A Self signed cluster issuer that just issue certs to anyone
* A self signed CA cert (ca-cert.yaml), from the self signed cluster issuer, which will serve as the new root CA (isCA)
* Then it finally creates a CA Issuer that will act as our actual issuer that issues certs


