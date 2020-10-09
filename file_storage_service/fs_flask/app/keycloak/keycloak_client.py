
import requests, os, json
from requests.auth import HTTPBasicAuth
from flask import ( jsonify )

class KeycloakClient:

    def __init__(self):
        with open(os.path.abspath(os.path.dirname(__file__))+'/keycloak.json') as config:
            self.client_config = json.load(config)

        self.user_tokens = {}
        self.user_details = {}
        self.admin_access_token, self.admin_refresh_token = self.admin_token()

    def admin_token(self):
        data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': self.client_config['web']['admin_username'],
            'password': self.client_config['web']['admin_password']
        }

        url = self.client_config['web']['admin_token_uri']
        response = requests.post(url, data=data)

        if response.status_code != requests.codes.ok:
            print("\tSERVER > [ERROR] Admin token not correctly requested - {}".format(response.json()))
            return None, None
        else:
            response_data = response.json()
            return response_data['access_token'], response_data['refresh_token']

    def is_token_valid(self, token):
        data = {
            'grant_type': 'password',
            'client_id': self.client_config['web']['client_id'],
            'client_secret': self.client_config['web']['client_secret'],
            'username': self.client_config['web']['admin_username'],
            'password': self.client_config['web']['admin_password'],
            'token': token
        }
        url = self.client_config['web']['token_introspection_uri']
        response = requests.post(url, data=data)

        data = response.json()

        return data['active']

    def refresh_admin_token(self):
        self.admin_access_token, self.admin_refresh_token = self.admin_token()

    def token_to_user(self, token):
        headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_config['web']['client_id'],
            'client_secret': self.client_config['web']['client_secret'],
            'username': self.client_config['web']['admin_username'],
            'password': self.client_config['web']['admin_password'],
            'token': token
        }

        url = self.client_config['web']['token_introspection_uri']
        response = requests.post(url, data=data)

        if response.status_code != requests.codes.ok:
            return response.status_code, response.json()

        data = response.json()

        if data['active'] == False:
            return requests.codes['unauthorized'], jsonify({"message": "Invalid token"})

        return response.status_code, json.loads(json.dumps({"id": data['sub'],"email": data['email'], "roles": data['realm_access']['roles']}))

    def get_site_manager_users(self):

        if self.is_token_valid(self.admin_access_token):
            headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}
        else:
            self.refresh_admin_token()
            headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}

        #url = "http://10.5.7.11:8080/auth/admin/realms/5geve/roles/SiteManager/users"
        url = "{}/SiteManager/users".format(self.client_config['web']['admin_roles_uri'])
        response = requests.get(url, headers=headers)

        return response.json(), response.status_code