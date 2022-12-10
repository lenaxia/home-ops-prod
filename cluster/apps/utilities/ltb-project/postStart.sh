#!/bin/bash

apt update
apt install wget
wget "https://s3.${SECRET_DEV_DOMAIN}/public/customlogo.png" -O /var/www/html/images/custom-logo.png
wget "https://s3.${SECRET_DEV_DOMAIN}/public/favicon.ico" -O /var/www/html/images/favicon.ico
sed 's/\"Email\"\;/"Reset by Email\"\;/' /var/www/lang/en.inc.php -i.bak
