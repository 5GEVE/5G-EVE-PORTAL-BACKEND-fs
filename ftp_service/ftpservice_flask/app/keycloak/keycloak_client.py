import requests, os, json
from requests.auth import HTTPBasicAuth
from flask import ( jsonify )

class Keycloak:

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
        response = requests.post(self.client_config['web']['admin_token_uri'], data=data)

        if response.status_code != requests.codes.ok:
            print("\tSERVER > [ERROR] Admin token not correctly requested - {}".format(response.json()))
            return None, None
        else:
            response_data = response.json()
            return response_data['access_token'], response_data['refresh_token']
    
    def refresh_admin_token(self):
        status, msg = self.refresh_token(self.refresh_token)
        if status != requests.codes.ok:
            self.admin_access_token, self.admin_refresh_token = self.admin_token()
        else:
            self.admin_access_token = msg['access_token']
            self.admin_refresh_token = msg['refresh_token']

    def get_user_id(self, token):
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
        return data['sub']
        
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

        if response.status_code != requests.codes.ok:
            return False
        return True

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
        return response.status_code, json.loads(json.dumps({"id": data['sub'],"email": data['email'], "roles": data['realm_access']['roles']}))

    def get_user_email(self, token):
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
        return data['email']        

    def get_users(self):
        headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}

        response = requests.get(self.client_config['web']['admin_users_uri'], headers=headers)

        if response.status_code != requests.codes.ok:
            return response.status_code, response.json

        return response.status_code, response.json()

    def get_user_groups(self, user_id):
        # Check if admin token is still valid
        if self.is_token_valid(self.admin_access_token):
            headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}
        else:
            self.refresh_admin_token()
            headers = {'Authorization': 'Bearer {}'.format(self.admin_access_token), 'Content-Type': 'application/json'}

        url = self.client_config['web']['admin_users_uri'] + '/' + user_id + '/groups'
        response = requests.get(url, headers=headers)

        bytes_to_str = str(response.content)[2:-1]
        return response.status_code, json.loads(json.dumps(bytes_to_str))

        