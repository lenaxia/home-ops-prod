import logging

# Application log level - one of:
#   CRITICAL 50
#   ERROR    40
#   WARNING  30
#   SQL      25
#   INFO     20
#   DEBUG    10
#   NOTSET    0
CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.DEBUG

# Log format.
CONSOLE_LOG_FORMAT = '%(asctime)s: %(levelname)s\t%(name)s:\t%(message)s'
FILE_LOG_FORMAT = '%(asctime)s: %(levelname)s\t%(name)s:\t%(message)s'


##########################################################################
# Authentication Configuration
##########################################################################
AUTHENTICATION_SOURCES = ['oauth2']

##########################################################################
# OAuth2 Configuration
##########################################################################

# Multiple OAUTH2 providers can be added in the list like [{...},{...}]
# All parameters are required

OAUTH2_CONFIG = [
    {
        # The name of the of the oauth provider, ex: github, google
        'OAUTH2_NAME': '${SECRET_CLOUD_NAME_SHORT}',
        # The display name, ex: Google
        'OAUTH2_DISPLAY_NAME': '${SECRET_CLOUD_NAME}',
        # Oauth client id
        'OAUTH2_CLIENT_ID': 'pgadmin',
        # Oauth secret
        'OAUTH2_CLIENT_SECRET': '${SECRET_PGADMIN_OAUTH_CLIENT_SECRET}',
        # URL to generate a token,
        # Ex: https://github.com/login/oauth/access_token
        'OAUTH2_TOKEN_URL': "https://authelia.${SECRET_DEV_DOMAIN}/api/oidc/token",
        # URL is used for authentication,
        # Ex: https://github.com/login/oauth/authorize
        'OAUTH2_AUTHORIZATION_URL': "https://authelia.${SECRET_DEV_DOMAIN}/api/oidc/authorization",
        # server metadata url might optional for your provider
        'OAUTH2_SERVER_METADATA_URL': 'https://authelia.${SECRET_DEV_DOMAIN}/.well-known/openid-configuration',
        # Oauth base url, ex: https://api.github.com/
        'OAUTH2_API_BASE_URL': "https://authelia.${SECRET_DEV_DOMAIN}/",
        # Name of the Endpoint, ex: user
        'OAUTH2_USERINFO_ENDPOINT': "https://authelia.${SECRET_DEV_DOMAIN}/api/oidc/userinfo",
        # Oauth scope, ex: 'openid email profile'
        # Note that an 'email' claim is required in the resulting profile
        'OAUTH2_SCOPE': 'openid email profile',
        # The claim which is used for the username. If the value is empty the
        # email is used as username, but if a value is provided,
        # the claim has to exist.
        'OAUTH2_USERNAME_CLAIM': 'email',
        # Font-awesome icon, ex: fa-github
        'OAUTH2_ICON': 'keycdn',
        # UI button colour, ex: #0000ff
        'OAUTH2_BUTTON_COLOR': None,
        # The additional claims to check on user ID Token or Userinfo response.
        # This is useful to provide additional authorization checks
        # before allowing access.
        # Example for GitLab: allowing all maintainers teams, and a specific
        # developers group to access pgadmin:
        # 'OAUTH2_ADDITIONAL_CLAIMS': {
        #     'https://gitlab.org/claims/groups/maintainer': [
        #           'kuberheads/applications',
        #           'kuberheads/dba',
        #           'kuberheads/support'
        #      ],
        #     'https://gitlab.org/claims/groups/developer': [
        #           'kuberheads/applications/team01'
        #      ],
        # }
        # Example for AzureAD:
        # 'OAUTH2_ADDITIONAL_CLAIMS': {
        #     'groups': ["0760b6cf-170e-4a14-91b3-4b78e0739963"],
        #     'wids': ["cf1c38e5-3621-4004-a7cb-879624dced7c"],
        # }
        'OAUTH2_ADDITIONAL_CLAIMS': None,
    }
]

# After Oauth authentication, user will be added into the SQLite database
# automatically, if set to True.
# Set it to False, if user should not be added automatically,
# in this case Admin has to add the user manually in the SQLite database.

OAUTH2_AUTO_CREATE_USER = True
