from flask import current_app
from flask import ( jsonify )
import os, requests, json

from app.models.file_data import *
from app.models.file_to_site import *
from app.models.site_data import *

class FilesManager:

    def __init__(self):
        pass

    def get_folder_path(self, token_data):
        user_folder_name = "{}/".format(str(token_data['email']).split('@')[0])
        return os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))

    """ 
        Retrieves files uploaded by a specific user 
    """
    def get_uploaded_files(self, token_data):
        
        folder_path = self.get_folder_path(token_data)

        if not os.path.exists(folder_path):
            return jsonify({"files":[]}), 200
        
        files = FileData.query.filter_by(creator=token_data['email'])
        
        av_files = {}
        for f in files:
            f2s = FileToSiteData.query.filter_by(file_id=f._id)
            
            if f2s:
                for item in f2s:
                    site = SiteData.query.filter_by(_id=item.site_id).first()

                    if site:
                        if not site.sitename in av_files.keys():
                            av_files[site.sitename] = []

                        f_rep = {
                            "filename": f.filename, 
                            "status": item._status, 
                            "creator": f.creator, 
                            "created_at": f.created_at,
                            "updated_at": f.updated_at
                        }
                        av_files[site.sitename].append(f_rep)

        return jsonify({"files": av_files}), 200

    """ 
        Retrieves all files to be deployed by a specific SiteManger
    """
    def get_files_to_deploy(self, token_data):

        headers = {'Authorization': 'Bearer {}'.format(token_data['access_token'])}
        reply = requests.get(current_app.config['RBAC_MANAGED_SITES_URL'], headers=headers)

        if reply.status_code == 200:
            av_files = {}
            data = reply.json()

            for site in data['details']:
                files_at_site = []
                site_details = SiteData.query.filter_by(sitename=site).first()
            
                if site_details:
                    # Retrieve all files to be deployed at a specific site
                    file_to_site = FileToSiteData.query.filter_by(site_id=site_details._id)

                    for f in file_to_site:
                        # For each file
                        f_data = FileData.query.filter_by(_id=f.file_id).first()
                        f_rep = {
                            "filename": f_data.filename, 
                            "status": f._status, 
                            "creator": f_data.creator, 
                            "created_at": f_data.created_at,
                            "updated_at": f_data.updated_at
                        }
                        files_at_site.append(f_rep)
                
                av_files[site] = files_at_site

            return jsonify({"files": av_files}), 200

        else:
            return reply.json(), reply.status_code

    """ 
        Method to receive the uploaded file by chunks
            @params:
                - token_data: user information extracted from the token
                - filename: name of the file to be uploaded
                - request: request from which we will "extract" the chunks of the file
    """
    def upload_file(self, token_data, filename, request):

        folder_path = self.get_folder_path(token_data)

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        file_full_path = os.path.join(os.path.join(folder_path, filename))

        if os.path.exists(file_full_path):
            return jsonify({"details":"File exists with the same filename"}), 400

        chunk_size = current_app.config['CHUNK_SIZE']
        try:
            with open(file_full_path, "wb") as f:
                reached_end = False
                while not reached_end:
                    chunk = request.stream.read(chunk_size)

                    if len(chunk) == 0:
                        reached_end = True
                    else:
                        f.write(chunk)
                        f.flush()

        except OSError as e:
            print("[ERROR] cannot write file " + filename + " to disk: " + StringIO(str(e)).getvalue())
            return jsonify({"details":"Error writing file to disk"}), 500

        schema = FileDataSchema()
        data = {"filename": filename, "creator": token_data['email']}
        errors = schema.validate(data)
        
        if errors:
            os.remove(file_full_path)
            return jsonify({"details": errors}), 400

        # Store new file details on db
        new_file_data = schema.load(data)
        db.session.add(new_file_data)
        db.session.commit()

        return jsonify({"details":"File succesfully uploaded"}), 201

    """ 
        Method to assign sites to the uploaded files
            @params:
                - token_data: user information extracted from the token
                - filename: name of the file to be uploaded
                - sites: sites to be assigned
                - site_managers: list of site managers that manages these sites
                - request: main request
    """
    def set_uploaded_file_sites(self, token_data, filename, sites, site_managers, request):
        folder_path = self.get_folder_path(token_data)

        file_full_path = os.path.join(os.path.join(folder_path, filename))

        if not os.path.exists(file_full_path):
            return jsonify({"details":"File does not exist"}), 400

        filedata = FileData.query.filter_by(filename=filename).first()
        if not filedata:
            return jsonify({"details": "Bad Request"}), 400
        
        if filedata.creator != token_data['email']:
            return jsonify({"details": "Unauthorized"}), 401

        sd_schema = SiteDataSchema()
        f2s_schema = FileToSiteSchema()

        requested_sites_to_deploy = []
        for site in sites:
            site_data = SiteData.query.filter_by(sitename=site).first()
            if site_data:
                requested_sites_to_deploy.append(site)
                file_data = FileData.query.filter_by(filename=filename).first()
                site_data = SiteData.query.filter_by(sitename=site).first()

                f2s = FileToSiteData.query.filter_by(site_id=site_data._id, file_id=file_data._id).first()
                if not f2s:
                    f2s_data = {"file_id": file_data._id, "site_id": site_data._id, "_status": "PENDING"}
                    new_f2s_data = f2s_schema.load(f2s_data)
                    db.session.add(new_f2s_data)
                    db.session.commit()

                    # Create a ticket if file correctly uploaded
                    if site in site_managers.keys() and len(site_managers[site]) > 0:
                        bz_trusted_url = "{}{}".format(current_app.config['BZ_SERVICE_URL'], "portal/tsb/tickets/trusted")
                        bz_trusted_data = {
                            'reporter': token_data['email'], 
                            'product': current_app.config['BZ_SERVICE_PROD'], 
                            'component': current_app.config['BZ_SERVICE_COMP'], 
                            'summary': "File {} correctly uploaded".format(filename), 
                            'description': "File {} should be uploaded to the infrastructure".format(filename),
                            'assigned_to': site_managers[site][0],
                            'cc': site_managers[site]
                            }
                        bz_ticket_reply = requests.post(bz_trusted_url, headers=request.headers, data=json.dumps(bz_trusted_data))

                        if bz_ticket_reply.status_code != requests.codes.ok:
                            print("[ERROR] Cannot create a ticket when uploading VNF")
                    else:
                        print("[ERROR] Cannot create ticket, no site managers available for that site")

        return jsonify({"details": {"deployment_requested_on": requested_sites_to_deploy}}), 200

    """ 
        Method to update the status of a file
            @params:
                - token_data: user information extracted from the token
                - filename: name of the file to be uploaded
                - site: site at which the file status has changed
                - status: new status of the file
    """
    def set_file_status(self, token_data, filename, site, status):
        file_to_download = FileData.query.filter_by(filename=filename).first()
        user_folder_name = "{}/".format(str(file_to_download.creator).split('@')[0])
        user_folder_path = os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))
        file_full_path = os.path.join(os.path.join(user_folder_path, filename))

        if not os.path.exists(file_full_path):
            return jsonify({"details":"File does not exist"}), 400

        file_data = FileData.query.filter_by(filename=filename).first()
        if not file_data:
            return jsonify({"details": "File not found at the repository"}), 400

        
        site_data = SiteData.query.filter_by(sitename=site).first()
        if not site_data:
            return jsonify({"details": "Site not found"}), 400
        
        f2s_data = FileToSiteData.query.filter_by(file_id=file_data._id, site_id=site_data._id).first()
        if not f2s_data:
            return jsonify({"details": "No deployment request for that file-site pair"}), 400

        f2s_data._status = status
        db.session.commit()

        return jsonify({"details": "{}-{} status updated to {}".format(filename, site, status)}), 200

    """ 
        Method to remove a file
            @params:
                - file_full_path: Path where the file is stored
                - filename: name of the file
                - sitename: site where the file is supposed to be deployed
    """
    def delete_file(self, file_full_path, filename, sitename):
        file_to_remove = FileData.query.filter_by(filename=filename).first()

        f2s_to_remove = FileToSiteData.query.filter_by(file_id=file_to_remove._id)

        if f2s_to_remove.count() > 1:
            site = SiteData.query.filter_by(sitename=sitename).first()
            FileToSiteData.query.filter_by(file_id=file_to_remove._id, site_id=site._id).delete()

        else:
            FileToSiteData.query.filter_by(file_id=file_to_remove._id).delete()
            FileData.query.filter_by(_id=file_to_remove._id).delete()
            os.remove(file_full_path)

        db.session.commit()
