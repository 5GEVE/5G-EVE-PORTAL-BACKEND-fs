from flask import ( Blueprint, jsonify, request)
from flask import current_app, send_from_directory
import os, app, requests, json
from app import db

from werkzeug.utils import secure_filename
from app.keycloak.decorators import token_required
from app.keycloak.keycloak_client import KeycloakClient

from app.files_manager.files_manager import *

from app.models.file_data import *
from app.models.file_to_site import *
from app.models.site_data import *

# BLUEPRINT CREATION
bp = Blueprint('auth', __name__, url_prefix='/portal/fs')

kc_client = KeycloakClient()
fs_manager = FilesManager()

# ROUTES DEFINITION
@bp.route('/', methods=['GET'])
@token_required
def get_files(token_data):

    if "SiteManager" in token_data['roles']:
        data, status = fs_manager.get_files_to_deploy(token_data)
        return data, status
    elif "VnfDeveloper" in token_data['roles']:
        data, status = fs_manager.get_uploaded_files(token_data)
        return data, status
    else:
        return jsonify({"details": "Unauthorized"}), 401

''' 
Saves single file uploaded from request.form 
        - uses stream to read in by chunks
        @url_params: 
            - filename: name of the file
        @form_params:
            - file: file to be uploaded
        @NOTE:  When using direct access to flask.request.stream you cannot access request.file or request.form first,
                otherwise stream is already parsed and empty (internal bahaviour of wekzeug)
'''
@bp.route('/upload/<filename>', methods=['POST'])
@token_required
def upload(token_data, filename=None):

    if "VnfDeveloper" in token_data['roles']:
        if "Content-Length" not in request.headers:
            return jsonify({"details":"Content-Length not in headers"}), 400

        if filename is None or filename == '':
            return jsonify({"details":"Filename not provided"}), 400            

        data, status = fs_manager.upload_file(token_data, filename, request)
        return data, status
    else:
        return jsonify({"details": "Unauthorized"}), 401

@bp.route('/sites/<filename>', methods=['POST'])
@token_required
def set_sites(token_data, filename=None):
    if "VnfDeveloper" in token_data['roles']:
        if not request.is_json:
            return jsonify({"details": "No json provided"}), 400

        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({"details": "Provided JSON not correctly formatted"}), 400

        if 'sites' not in data.keys():
            return jsonify({"details":"No sites provided"}), 400
        
        site_managers, status_code = kc_client.get_site_manager_users()

        if status_code == requests.codes.ok:
            sm_map = {}
            for site in data['sites']:
                sm_map[site] = []
                for sm in site_managers:
                    if 'attributes' in sm.keys():
                        if 'managed_sites' in sm['attributes'].keys():
                            if site in sm['attributes']['managed_sites']:
                                sm_map[site].append(sm['email'])
                                
            data, status = fs_manager.set_uploaded_file_sites(token_data, filename, data['sites'], sm_map, request)
            return data, status

        else:
            return jsonify({"details": site_managers}), status_code
    else:
        return jsonify({"details": "Unauthorized"}), 401

@bp.route('/status/<filename>', methods=['POST'])
@token_required
def set_file_status(token_data, filename=None):

    if not "SiteManager" in token_data['roles']:
        return jsonify({"details": "Unauthorized"}), 401

    if not request.is_json:
        return jsonify({"details": "No json provided"}), 400

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"details": "Provided JSON not correctly formatted"}), 400

    if 'status' not in data.keys() or 'site' not in data.keys():
        return jsonify({"details":"No sites provided"}), 400

    if data['status'] not in ['PENDING', 'READY']:
        return jsonify({"details":"Status not supported. Only PENDING or READY can be used."}), 400

    data, status = fs_manager.set_file_status(token_data, filename, data['site'], data['status'])

    return data, status


@bp.route('/download/<filename>', methods=['GET'])
@token_required
def download(token_data, filename=None):

    if filename is None or filename=='':
        return jsonify({"details":"Filename not provided"}), 400
    
    if "SiteManager" in token_data['roles']:
        file_to_download = FileData.query.filter_by(filename=filename).first()
        user_folder_name = "{}/".format(str(file_to_download.creator).split('@')[0])

    elif "VnfDeveloper" in token_data['roles']:
        user_folder_name = "{}/".format(str(token_data['email']).split('@')[0])

    else:
        return jsonify({"details": "Unauthorized"}), 401

    folder_path = os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))
    file_full_path = os.path.join(os.path.join(folder_path, filename))

    if not os.path.exists(file_full_path):
        return jsonify({"details":"File does not exist"}), 400

    return send_from_directory(folder_path, filename)

@bp.route('/delete/<filename>', methods=['POST'])
@token_required
def delete(token_data, filename=None):

    if filename is None or filename=='':
        return jsonify({"details":"Filename not provided"}), 400
    
    if not request.is_json:
        return jsonify({"details": "No json provided"}), 400

    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"details": "Provided JSON not correctly formatted"}), 400

    if 'site' not in data.keys():
        return jsonify({"details":"No site provided"}), 400

    if "SiteManager" in token_data['roles']:
        file_to_download = FileData.query.filter_by(filename=filename).first()
        user_folder_name = "{}/".format(str(file_to_download.creator).split('@')[0])

    elif "VnfDeveloper" in token_data['roles']:
        user_folder_name = "{}/".format(str(token_data['email']).split('@')[0])
    
    else:
        return jsonify({"details": "Unauthorized"}), 401

    folder_path = os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))
    file_full_path = os.path.join(os.path.join(folder_path, filename))

    if not os.path.exists(file_full_path):
        return jsonify({"details":"File does not exist"}), 400

    fs_manager.delete_file(file_full_path, filename, data['site'])

    return jsonify({"details": "file {} correctly removed".format(filename)}), 200

@bp.route('/site-facilities', methods=['GET'])
@token_required
def get_site_facilities(token_data):

    site_facilities = SiteData.query.all()

    site_facilities_names = []
    for site in site_facilities:
        site_facilities_names.append(site.sitename)
    
    return jsonify({"details": { "site_facilities": site_facilities_names}}), 200
