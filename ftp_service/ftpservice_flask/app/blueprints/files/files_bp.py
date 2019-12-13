from flask import ( Blueprint, jsonify, request, make_response )
from app import db, bcrypt, kc_client
import app
from werkzeug.utils import secure_filename
import requests, os, json

from app.models.user import *

from app.keycloak.keycloak_client import Keycloak

# Path to stored files
PATH_TO_STORE = './uploaded_files'

# BLUEPRINT CREATION
bp = Blueprint('files', __name__, url_prefix='/files')

# ROUTES DEFINITION

@bp.route('', methods=['GET'])
#@oidc.accept_token(require_token=True)
def get_files():
    msg = {}
    msg['email'] = "ggarcia@mail.com"
    msg['roles'] = ['role1', 'role2']
    msg['groups'] = ['group1']
    #token = str(request.headers['authorization']).split(" ")[1]
    #status_code, msg = kc_client.token_to_user(token)

    #if status_code == requests.codes.ok: 
    files = UploadedFile.query.filter_by(user_email=msg['email'])
    stored_files = []
    for i,f in enumerate(files):
        #stored_files[i] = {'name': f.name, 'sites': f.sites, 'creator': msg['email']}
        stored_files.append({'name': f.name, 'sites': f.sites, 'creator': msg['email']})
    return jsonify({'details': stored_files}), 200

@bp.route('', methods=['POST'])
#@oidc.accept_token(require_token=True)
def upload_files():
    # Check if request contains associated sites
    #if not 'sites' in request.form.keys():
    #    return jsonify({'details' : 'No target sites to deploy in the request'}), 400
    # Check if the request contains a file to upload
    print(request.form.keys())
    if 'file' not in request.files:
        return jsonify({'details' : 'No file part in the request'}), 400
    _file = request.files['file']
    if _file.filename == '':
        return jsonify({'details' : 'No file selected for uploading'}), 400

    # Check if there is already a file with the same name
    filename = secure_filename(_file.filename)
    save_path = PATH_TO_STORE + "/" + filename
    current_chunk = int(request.form['dzchunkindex'])
    if os.path.exists(save_path) and current_chunk == 0:
        return jsonify({'details': 'File already exists'}), 400

    msg = {}
    msg['email'] = "ggarcia@mail.com"
    msg['roles'] = ['role1', 'role2']
    msg['groups'] = ['group1']
    #token = str(request.headers['authorization']).split(" ")[1]
    #status_code, msg = kc_client.token_to_user(token)

    #if status_code == requests.codes.ok:
    #file_data = {'name': _file.filename, 'sites': str(request.form['sites']).split(" "), 'user_email': msg['email']}
    sites = ['site1']
    file_data = {'name': _file.filename, 'sites': sites, 'user_email': msg['email']}
    schema = UploadedFileSchema()
    errors = schema.validate(file_data)
    if errors:
        return jsonify({"details": errors}), 400

    try:
        with open(save_path, 'ab') as f:
            #TODO: fixed chunk size
            chunk_size = int(1024*1024)
            f.seek(chunk_size)
            f.write(_file.stream.read())
    except OSError:
        return jsonify({'details': 'Imposible to write file on disk'}), 500
        return make_response(("", 500))

    total_chunks = int(request.form['dztotalchunkcount'])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        #if os.path.getsize(save_path) != int(total_chunks*chunk_size):
        #    return make_response(('Size mismatch', 500))
        #else:
        user = User.query.filter_by(email=msg['email']).first()
        # if there is no local info about the user
        if not user:
            user_schema = UserSchema()
            user_data = {'email': msg['email'], 'roles': msg['roles'], 'groups': msg['groups']}
            user = user_schema.load(user_data)
            db.session.add(user)
            db.session.commit()

        # store uploaded file related meta-data
        new_file = schema.load(file_data)
        db.session.add(new_file)
        db.session.commit()
        return jsonify({'details': 'File {} has been uploaded successfully'.format(_file.filename)}), 200
    else:
        print('\t[SERVER] Chunk {} of {} for file {} complete'.format(current_chunk + 1, total_chunks, _file.filename))

    return jsonify({'details': 'Chunk upload successful'}), 200

'''
@bp.route('/register', methods=['POST'])
def registration():
    if not request.is_json:
        return jsonify({"details": "No json provided"}), 400

    data = request.get_json()

    schema = BugzillaUserSchema()
    errors = schema.validate(data)

    if errors:
        return jsonify({"details": errors}), 400

    # check uniqueness of the username and email in local database
    if not BugzillaUser.query.filter_by(email=data['email']).first() == None:
        return jsonify({"details": "Username already registered"}), 400

    # Create user in bugzilla
    status, msg = bz_client.create_user(data)

    if status in [200, 201]:
        # Hash password
        data['password'] = bcrypt.generate_password_hash(data['password'].encode('utf-8'))
        
        # Store new user in local database
        new_user = schema.load(data)
        db.session.add(new_user)
        db.session.commit()

    return jsonify({'details': msg}), status



@bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"details": "No json provided"}), 400

    data = request.get_json()
    if 'email' not in data.keys() or 'password' not in data.keys():
        return jsonify({"details": "Email or password not provided"}), 400
    
    status, msg = bz_client.login(data)
    
    if status == requests.codes.ok:
        user = BugzillaUser.query.filter_by(email=data['email']).first()
        if user:
            # Request user details and store bugzilla user id
            #TODO: lo ideal es guardar el user_id de keycloak cuando se registre
            #token_to_user_status, token_to_user_msg = kc_client.token_to_user(msg['token'])
            #if token_to_user_status == requests.codes.ok:
                #user.bz_user_id = token_to_user_msg['id']
            user.apikey = msg['token']
            db.session.commit()

            return jsonify({"details": "User correctly logged in", "token": msg['token']}), 200

        else:
            schema = BugzillaUserSchema()

            data['password'] = bcrypt.generate_password_hash(data['password'].encode('utf-8'))
            data['apikey'] = msg['token']
            data['full_name'] = data['email']

            # Store user in local database
            new_user = schema.load(data)
            db.session.add(new_user)
            db.session.commit()

            return jsonify({"details": "User correctly logged in", "token": msg['token']}), 200

        print("[AUTH_BP][ERROR] > User correctly logged in at bugzilla but not found at local database")
        return jsonify({"details": "Internal server error"}), 500

    return jsonify({"details": msg}), status

#TODO: oidc
@bp.route('/logout', methods=['GET'])
def logout():
    token = str(request.headers['authorization']).split(" ")[1]
    user_email = kc_client.get_user_email(token)
    
    user = BugzillaUser.query.filter_by(email=user_email).first()

    if user:
        status, msg = bz_client.logout(user.apikey)

        if status == requests.codes.ok:
            user.apikey = ""
            db.session.commit()

            return jsonify({"details": "User session corretly closed"}), 200
        else:
            return jsonify({"details": msg}), status
    else:
        print("[AUTH_BP][ERROR] > User correctly logged in at keycloak but not found at local database")
        return jsonify({"details": "Internal server error"}), 500
'''