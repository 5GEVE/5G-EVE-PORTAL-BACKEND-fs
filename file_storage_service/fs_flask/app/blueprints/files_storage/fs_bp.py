from flask import ( Blueprint, jsonify, request)
from flask import current_app, send_from_directory, send_file
import os, app, requests, json, sys
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
"""
Retrieves all uploaded files
"""
@bp.route('/', methods=['GET'])
@token_required
def get_files(token_data):
    if "VnfDeveloper" in token_data['roles']: 
        data, status = fs_manager.get_uploaded_files(token_data['email'])
        return data, status
    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Retrieves file information
"""
@bp.route('/<filename>', methods=['GET'])
@token_required
def get_file(token_data, filename=None):
    if filename is None or filename == '':
        return jsonify({"details":"Filename not provided"}), 400            

    # concat file name if needed
    filename = str(filename).replace(" ", "_")

    if "VnfDeveloper" in token_data['roles']: 
        data, status = fs_manager.get_uploaded_file(filename, token_data['email'])
        return data, status
    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Saves single file uploaded from request.form 
        - uses stream to read in by chunks
        @url_params: 
            - filename: name of the file
        @form_params:
            - file: file to be uploaded
        @NOTE:  When using direct access to flask.request.stream you cannot access request.file or request.form first,
                otherwise stream is already parsed and empty (internal bahaviour of wekzeug)
"""
@bp.route('/<filename>', methods=['POST'])
@token_required
def upload(token_data, filename=None):
    if filename is None or filename == '':
        return jsonify({"details":"Filename not provided"}), 400            

    # concat file name if needed
    filename = str(filename).replace(" ", "_")

    if "VnfDeveloper" in token_data['roles']:
        if "Content-Length" not in request.headers:
            return jsonify({"details":"Content-Length not in headers"}), 400
        
        data, status = fs_manager.upload_file(token_data, filename, request)
        return data, status

    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Removes an uploaded file 
        @params: 
            - filename: name of the file
"""
@bp.route('/<filename>', methods=['DELETE'])
@token_required
def delete_file(token_data, filename=None):
    if filename is None or filename == '':
        return jsonify({"details":"Filename not provided"}), 400            

    # concat file name if needed
    filename = str(filename).replace(" ", "_")

    if "VnfDeveloper" in token_data['roles']:        
        data, status = fs_manager.delete_uploaded_file(filename, token_data)
        return data, status

    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Downloads a specific file
        @url_params: 
            - filename: name of the file
"""
@bp.route('/<filename>/download', methods=['GET'])
@token_required
def download(token_data, filename=None):

    if filename is None or filename == '':
        return jsonify({"details":"Filename not provided"}), 400            

    # concat file name if needed
    filename = str(filename).replace(" ", "_")
    
    #if "SiteManager" in token_data['roles']:
    #    file_to_download = FileData.query.filter_by(filename=filename).first()
    #    user_folder_name = "{}/".format(str(file_to_download.creator).split('@')[0])

    if "VnfDeveloper" in token_data['roles']:
        user_folder_name = "{}/".format(str(token_data['email']).split('@')[0])

    else:
        return jsonify({"details": "Unauthorized"}), 401

    folder_path = os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))
    file_full_path = os.path.join(os.path.join(folder_path, filename))

    if not os.path.exists(file_full_path):
        return jsonify({"details":"File does not exist"}), 400

    #return send_from_directory(folder_path, filename)
    return send_file(file_full_path, mimetype="application/zip", as_attachment=True)

"""
Retrieves all deployment requests
"""
@bp.route('/dp_requests', methods=['GET'])
@token_required
def get_deployment_requests(token_data):
    if "VnfDeveloper" in token_data['roles']:
        data, status = fs_manager.get_created_deployment_requests(token_data)
        return data, status
    elif "SiteManager" in token_data['roles']:
        data, status = fs_manager.get_received_deployment_requests(token_data)
        return data, status        
    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Request for deployment of a file at specific sites. Only the owner of the file
is able to create the deployment requests
        @json_params:
            - filename: name of the file 
            - sites: sites where the specified file must be deployed
"""
@bp.route('/dp_requests', methods=['POST'])
@token_required
def create_deployment_requests(token_data):         

    if "VnfDeveloper" in token_data['roles']:
        if not request.is_json:
            return jsonify({"details": "No json provided"}), 400

        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({"details": "Provided JSON not correctly formatted"}), 400

        if "sites" not in data.keys() or "filename" not in data.keys():
            return jsonify({"details":"Sites or filename not provided"}), 400

        # concat file name if needed
        filename = str(data['filename']).replace(" ", "_")

        # Retrieve list of site managers for the specific sites        
        site_managers, status_code = kc_client.get_site_manager_users()

        if status_code == requests.codes.ok:
            sm_map = {}
            for site in data['sites']:
                sm_map[site] = []
                for sm in site_managers:
                    if "attributes" in sm.keys():
                        if "managed_sites" in sm['attributes'].keys():
                            if site in sm['attributes']['managed_sites']:
                                sm_map[site].append(sm['email'])
            
            # Store information about the site where the uploaded file must be deployed
            data, status = fs_manager.set_uploaded_file_sites(token_data, filename, data['sites'], sm_map, request)
            return data, status

        else:
            print('Error retrieving list of site managers', file=sys.stderr)
            return jsonify({"details": site_managers}), status_code
    else:
        return jsonify({"details": "Unauthorized"}), 401

"""
Method to remove a deployment request
        @url_params: 
            - request_id: id of the request          
"""
@bp.route('/dp_requests/<request_id>', methods=['DELETE'])
@token_required
def delete(token_data, request_id=None):

    if request_id is None or request_id == '':
        return jsonify({"details":"Request id not provided"}), 400            

    fs_manager.delete_file_2_site(request_id)

    return jsonify({"details": "request {} correctly removed".format(request_id)}), 200

"""
Updates the status of a deployment request
        @url_params: 
            - request_id: id of the request
        @json_params:
            - status: new status to be assigned
"""
@bp.route('/dp_requests/<request_id>', methods=['PUT'])
@token_required
def set_file_status(token_data, request_id=None):

    if request_id is None or request_id == '':
        return jsonify({"details":"Request ID not provided"}), 400            

    if not "SiteManager" in token_data['roles']:
        return jsonify({"details": "Unauthorized"}), 401

    if not request.is_json:
        return jsonify({"details": "No json provided"}), 400
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"details": "Provided JSON not correctly formatted"}), 400

    if "status" not in data.keys() or data['status'] not in ['PENDING', 'READY']:
        return jsonify({"details":"Status not provided or the value is not supported (PENDING and READY available)"}), 400

    data, status = fs_manager.update_file_2_site(request_id, data['status'], token_data, request)

    return data, status

"""
Downloads a specific file associated to a request
        @url_params: 
            - request_id: id of the request
"""
@bp.route('/dp_requests/<request_id>/download', methods=['GET'])
@token_required
def download_associated_file(token_data, request_id=None):

    if request_id is None or request_id == '':
        return jsonify({"details":"Request ID not provided"}), 400            
    
    if "VnfDeveloper" not in token_data['roles'] and "SiteManager" not in token_data['roles']:
        return jsonify({"details": "Unauthorized"}), 401
    print("Antes", file=sys.stderr)
    file_full_path = fs_manager.get_file_path_associated_file_2_site(request_id)
    print(file_full_path, file=sys.stderr)
    if not os.path.exists(file_full_path):
        return jsonify({"details":"File does not exist"}), 400

    #return send_from_directory(folder_path, filename)
    return send_file(file_full_path, mimetype="application/zip", as_attachment=True)

"""
Retrieves all the available site facilities where to deploy VNFs           
"""
@bp.route('/site-facilities', methods=['GET'])
@token_required
def get_site_facilities(token_data):

    site_facilities = SiteData.query.all()

    site_facilities_names = []
    for site in site_facilities:
        site_facilities_names.append(site.sitename)
    
    return jsonify({"details": { "site_facilities": site_facilities_names}}), 200
