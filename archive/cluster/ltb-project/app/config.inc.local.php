<?php // My SSP configuration
$keyphrase = getenv('SECRET_LTB_KEYPHRASE');
$debug = true;
$ldap_url = "ldap://192.168.0.120:389";
$ldap_binddn = getenv('SECRET_LTB_LDAP_BINDDN');
$ldap_bindpw = getenv('SECRET_LTB_LDAP_PASSWORD');
$ldap_base = getenv('SECRET_LTB_LDAP_BASE');
$ldap_filter = "(&(objectClass=posixAccount)(uid={login}))";
$who_change_password = "user";

$use_sms = false;

$hash = "clear";
#$logo = "images/ltb-logo.png";
$logo = getenv('SECRET_LTB_LOGO');
$background_image = "images/unsplash-sky.jpeg";
$custom_css = "css/custom.css";
$display_footer = false;
$header_name_preset_login = "Remote-User";

$pwd_min_length = 8;
$pwd_min_lower = 3;
$pwd_min_upper = 1;
$pwd_min_digit = 1;
$pwd_min_special = 1;
$pwd_no_special_at_ends = false;
$use_pwnedpasswords = true;
$pwd_no_reuse = false;
$pwd_show_policy = "onerror";

$use_tokens = true;
$mail_address_use_ldap = true;
$crypt_answers = true;
$token_lifetime = "3600";
$reset_request_log = "/var/backups/self-service-password";
$reset_url = getenv('SECRET_LTB_PASSWORD_RESET_URL');

$mail_from = getenv('SECRET_LTB_SMTP_MAIL_FROM');
$mail_from_name = getenv('SECRET_LTB_SMTP_MAIL_FROM_NAME');;
$mail_signature = "";
$notify_on_change = true;

$mail_sendmailpath = '/usr/sbin/sendmail';
$mail_protocol = 'smtp';
$mail_smtp_debug = 0;
$mail_debug_format = 'html';
$mail_smtp_host = getenv('SECRET_LTB_SMTP_HOST');
$mail_smtp_auth = true;
$mail_smtp_user = getenv('SECRET_LTB_SMTP_USER');
$mail_smtp_pass = getenv('SECRET_LTB_SMTP_PASSWORD');
$mail_smtp_port = 587;
$mail_smtp_secure = 'starttls';
$mail_smtp_autotls = true;
$mail_smtp_options = array();
$mail_contenttype = 'text/plain';
$mail_wordwrap = 0;
$mail_charset = 'utf-8';
$mail_priority = 3;

$change_sshkey = true;
$who_change_sshkey = "manager";    
$change_sshkey_attribute = "sshPublicKey";
$change_sshkey_objectClass = "ldapPublicKey";
$ssh_valid_key_types = array('ssh-rsa', 'ssh-dss', 'ecdsa-sha2-nistp256', 'ssh-ed25519');
$notify_on_sshkey_change = true;

$use_questions = false;
?>
