import os, json

basedir = os.path.abspath(os.path.dirname(__file__))

def configure(mode, app):

    if mode == "DEV":

        # APP configuration
        app.config['DEBUG'] = True
        app.config['SECRET_KEY'] = 'you-will-never-guess'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['CORS_HEADERS'] = 'Content-Type'
        app.config['CHUNK_SIZE'] = 4096

    # Create keycloak configuration file
    with open(os.path.abspath(os.path.dirname(__file__))+'/../app/flask_config.json', 'r') as config_file:
        config = config_file.read()

    conf = json.loads(config)

    # App configuration from config file
    app.config['RBAC_MANAGED_SITES_URL'] = conf['rbac_managed_sites_url']
    app.config['UPLOAD_FOLDER'] = '/storage'
    app.config['BZ_SERVICE_URL'] = conf['bz_service_url']
    app.config['BZ_SERVICE_PROD'] = conf['bz_service_product']
    app.config['BZ_SERVICE_COMP'] = conf['bz_service_component']

    # Config file generation (for keycloak)
    kc_config = {}
    kc_config['web'] = {}
    kc_config['web']['client_id'] = conf['kc_client_id']
    kc_config['web']['client_secret'] = conf['kc_client_secret']
    kc_config['web']['issuer'] = "{}{}".format(conf['kc_url'], conf['issuer'])
    kc_config['web']['redirect_uris'] = []
    kc_config['web']['redirect_uris'].append("{}{}".format(conf['kc_url'], conf['redirect_uris'][0]))
    kc_config['web']['auth_uri'] = "{}{}".format(conf['kc_url'], conf['auth_uri'])
    kc_config['web']['userinfo_uri'] = "{}{}".format(conf['kc_url'], conf['userinfo_uri'])
    kc_config['web']['token_uri'] = "{}{}".format(conf['kc_url'], conf['token_uri'])
    kc_config['web']['token_introspection_uri'] = "{}{}".format(conf['kc_url'], conf['token_introspection_uri'])
    kc_config['web']['end_session'] = "{}{}".format(conf['kc_url'], conf['end_session'])
    kc_config['web']['admin_username'] = "{}".format(conf['kc_admin_username'])
    kc_config['web']['admin_password'] = "{}".format(conf['kc_admin_password'])
    kc_config['web']['admin_token_uri'] = "{}{}".format(conf['kc_url'], conf['admin_token_uri'])
    kc_config['web']['admin_token_introspect_uri'] = "{}{}".format(conf['kc_url'], conf['admin_token_introspect_uri'])
    kc_config['web']['admin_users_uri'] = "{}{}".format(conf['kc_url'], conf['admin_users_uri'])
    kc_config['web']['admin_groups_uri'] = "{}{}".format(conf['kc_url'], conf['admin_groups_uri'])
    kc_config['web']['admin_roles_uri'] = "{}{}".format(conf['kc_url'], conf['admin_roles_uri'])

    with open(os.path.abspath(os.path.dirname(__file__))+'/../app/keycloak/keycloak.json',"w+") as f:
        json.dump(kc_config, f)
    f.close()
 
