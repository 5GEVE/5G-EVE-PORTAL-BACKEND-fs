from flask import current_app
from flask import ( jsonify )
import os, requests, json, sys

from app.models.file_data import *
from app.models.file_to_site import *
from app.models.site_data import *
from threading import Thread

class FilesManager:

    def __init__(self):
        pass

    def get_folder_path(self, token_data):
        user_folder_name = "{}/".format(str(token_data['email']).split('@')[0])
        return os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name))

    """
    Checks whether a file exists or not
        @params:
            - filename: Owner of the files
            - creator: Owner of the files
    """
    def get_uploaded_file(self, filename, creator):
        uploaded_file = FileData.query.filter_by(creator=creator,filename=filename).first()
        if uploaded_file:
            file_rep = {
                "filename": uploaded_file.filename, 
                "creator": uploaded_file.creator, 
                "created_at": uploaded_file.created_at,
                "updated_at": uploaded_file.updated_at
            }
            return jsonify({"details": file_rep}), 200
        
        return jsonify({"details": {}}), 200

    """
    Method to retrieve all uploaded files
        @params:
            - creator: Owner of the files
    """
    def get_uploaded_files(self, creator):
        files = FileData.query.filter_by(creator=creator)
        available_files = []
        for uploaded_file in files:
            file_rep = {
                "filename": uploaded_file.filename, 
                "creator": uploaded_file.creator, 
                "created_at": uploaded_file.created_at,
                "updated_at": uploaded_file.updated_at
            }
            available_files.append(file_rep)
        return jsonify({"files": available_files}), 200
    
    """
    Method to delete a specific file
        @params:
            - creator: Owner of the files
    """
    def delete_uploaded_file(self, filename, token_data):
        folder_path = self.get_folder_path(token_data)
        file_full_path = os.path.join(os.path.join(folder_path, filename))

        if not os.path.exists(file_full_path):
            return jsonify({"details":"File not found"}), 404

        file_to_remove = FileData.query.filter_by(filename=filename, creator=token_data['email']).first()
        if not file_to_remove:
            return jsonify({"details":"File not found at the database"}), 404

        # Delete all deployment requests associated with the file
        FileToSiteData.query.filter_by(file_id=file_to_remove._id).delete()
        FileData.query.filter_by(filename=filename, creator=token_data['email']).delete()
        os.remove(file_full_path)
        db.session.commit()

        return jsonify({"details":"File {} correctly removed".format(filename)}), 200

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
            request_data = request.data
            return jsonify({"details":"File exists with the same filename"}), 409

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

        return jsonify({"details":"File successfully uploaded"}), 201

    """ 
        Method to create all assignment requests for files deployment at different sites
            @params:
                - token_data: user information extracted from the token
                - filename: name of the file to be uploaded
                - sites: sites to be assigned
                - site_managers: list of site managers that manages these sites
                - request: main request
    """
    def set_uploaded_file_sites(self, token_data, filename, sites, site_managers, request):

        # Check whether the file is stored at the server or not
        folder_path = self.get_folder_path(token_data)
        file_full_path = os.path.join(os.path.join(folder_path, filename))
        if not os.path.exists(file_full_path):
            return jsonify({"details":"File not stored at the server"}), 404

        file_data = FileData.query.filter_by(filename=filename, creator=token_data['email']).first()
        if not file_data:
            return jsonify({"details": "File not found at the database"}), 404
        
        requested_sites_to_deploy = []
        for site in sites:
            reply, status = self.create_file_2_site(filename, token_data['email'], site)

            if status == 201:
                requested_sites_to_deploy.append(site)

                # Create a ticket if file correctly uploaded
                if site in site_managers.keys() and len(site_managers[site]) > 0:
                    site_data = SiteData.query.filter_by(sitename=site).first()
                    file_data = FileData.query.filter_by(filename=filename, creator=token_data['email']).first()
                    f2s = FileToSiteData.query.filter_by(site_id=site_data._id, file_id=file_data._id).first()

                    bz_trusted_url = "{}{}".format(current_app.config['BZ_SERVICE_URL'], "portal/tsb/tickets/trusted")
                    bz_trusted_data = {
                        'reporter': token_data['email'], 
                        'product': current_app.config['BZ_SERVICE_PROD'], 
                        'component': current_app.config['BZ_SERVICE_COMP'], 
                        'summary': "File {} correctly uploaded".format(filename), 
                        'description': "Requested file upload: filename {}. Request ID: {}".format(filename, f2s._id),
                        'assigned_to': site_managers[site][0],
                        'cc': site_managers[site]
                        }
                    bz_ticket_reply = requests.post(bz_trusted_url, headers=request.headers, data=json.dumps(bz_trusted_data))
                    
                    if bz_ticket_reply.status_code != requests.codes.ok:
                        print("[ERROR] error creating ticket {} - {} - {}".format(filename, token_data['email'], site), file=sys.stderr)
                        print("[ERROR] {}".format(bz_ticket_reply.json()), file=sys.stderr)
                        #return jsonify({"details": "Error creating ticket"}), 500
                    else:
                        # Update ticket info at the database
                        f2s.ticket_id =  int(bz_ticket_reply.json()['details']['id'])
                        db.session.commit()
                else:
                    print("[ERROR] Cannot create ticket, no site managers available for that site", file=sys.stderr)

        return jsonify({"details": {"deployment_requested_on": requested_sites_to_deploy}}), 200

    """
    Method to retreive deployment requests received by a specific SiteManager
        @params:
            - token_data: user information extracted from the token
    """
    def get_received_deployment_requests(self, token_data):
        headers = {'Authorization': 'Bearer {}'.format(token_data['access_token'])}
        reply = requests.get(current_app.config['RBAC_MANAGED_SITES_URL'], headers=headers)

        if reply.status_code == 200:
            available_deployment_requests = {}
            managed_sites = reply.json()['details']
            for site in managed_sites:
                files_per_site = []
                site_details = SiteData.query.filter_by(sitename=site).first()
                if site_details:
                    file_2_site = FileToSiteData.query.filter_by(site_id=site_details._id)

                    for f in file_2_site:
                        file_data = FileData.query.filter_by(_id=f.file_id).first()
                        file_rep = {
                            "request_id": f._id,
                            "filename": file_data.filename, 
                            "creator": file_data.creator, 
                            "site": site,
                            "status": f._status, 
                            "created_at": file_data.created_at,
                            "updated_at": file_data.updated_at
                        }
                        files_per_site.append(file_rep)
            
                available_deployment_requests[site] = files_per_site

            return available_deployment_requests, 200

        else:
            return reply.json(), reply.status_code 

    """
    Method to retreive generated deployment requests by a VnfDeveloper
        @params:
            - token_data: user information extracted from the token
    """
    def get_created_deployment_requests(self, token_data):
        
        folder_path = self.get_folder_path(token_data)
        if not os.path.exists(folder_path):
            return jsonify({"files":[]}), 200
        
        uploaded_files = FileData.query.filter_by(creator=token_data['email'])
        
        av_files = {}
        for uploaded_file in uploaded_files:
            file_to_sites = FileToSiteData.query.filter_by(file_id=uploaded_file._id)
            if file_to_sites:
                for f2s in file_to_sites:
                    site = SiteData.query.filter_by(_id=f2s.site_id).first()
                    if site:
                        if not site.sitename in av_files.keys():
                            av_files[site.sitename] = []

                        f_rep = {
                            "request_id": f2s._id, 
                            "filename": uploaded_file.filename, 
                            "creator": uploaded_file.creator,
                            "site": site.sitename,
                            "status": f2s._status,  
                            "created_at": uploaded_file.created_at,
                            "updated_at": uploaded_file.updated_at
                        }
                        av_files[site.sitename].append(f_rep)

        return av_files, 200

    """ 
        Method to create a request of deployment for a specific file at a specific site
            @params:
                - filename: name of the file
                - creator: the owner of the file
                - site: sitename where the file must be deployed
    """
    def create_file_2_site(self, filename, creator, site):
        site_data = SiteData.query.filter_by(sitename=site).first()
        if not site_data:
            return jsonify({"details": "Site - {} - not found".format(site)}), 404

        file_data = FileData.query.filter_by(filename=filename, creator=creator).first()
        if not file_data:
            return jsonify({"details": "File - {} - owned by {} not found".format(site, creator)}), 404        
              
        f2s = FileToSiteData.query.filter_by(site_id=site_data._id, file_id=file_data._id).first()
        if not f2s:
            f2s_schema = FileToSiteSchema()
            f2s_data = {"file_id": file_data._id, "site_id": site_data._id, "_status": "PENDING"}
            new_f2s_data = f2s_schema.load(f2s_data)
            db.session.add(new_f2s_data)
            db.session.commit()
            return jsonify({"details": "created"}), 201
        
        return jsonify({"details": "Request already created"}), 409

    """ 
        Method to remove the deployment request for a specific file at a specific site
            @params:
                - request_id: identifier of the deployment request
    """
    def delete_file_2_site(self, request_id):
        f2s = FileToSiteData.query.filter_by(_id=request_id).first()
        if not f2s:
            return jsonify({"details": "No request found with id {}".format(request_id)}), 404 

        # Delete and update session
        FileToSiteData.query.filter_by(_id=request_id).delete()
        db.session.commit()

        return jsonify({"details": "Request {} correctly removed".format(request_id)}), 200

    """ 
        Method to update the status of a deployment request
            @params:
                - request_id: identifier of the deployment request
                - status: new status of the request
    """
    def update_file_2_site(self, request_id, status, token_data, request):
        f2s = FileToSiteData.query.filter_by(_id=request_id).first()
        if not f2s:
            return jsonify({"details": "No request found with id {}".format(request_id)}), 404 

        if f2s.ticket_id:
            file_data = FileData.query.filter_by(_id=f2s.file_id).first()
            site_data = SiteData.query.filter_by(_id=f2s.site_id).first()
            if file_data and site_data:
                bz_trusted_url = "{}{}".format(current_app.config['BZ_SERVICE_URL'], "portal/tsb/tickets/{}/comments/trusted".format(f2s.ticket_id))
                bz_trusted_data = {
                    'reporter': token_data['email'], 
                    'comment': 'Deployment request of file {} at {} updated to status {}'.format(file_data.filename, site_data.sitename, status)
                    }
                bz_ticket_reply = requests.post(bz_trusted_url, headers=request.headers, data=json.dumps(bz_trusted_data))
                print("Comment reply: {}".format(bz_ticket_reply.content), file=sys.stderr)

        # Update the status of the deployment request
        f2s = FileToSiteData.query.filter_by(_id=request_id).first()
        f2s._status = status
        db.session.commit()

        return jsonify({"details": "Request {} correctly updated".format(request_id)}), 200

    """
        Returns the path where the file associated to the request is stored
    """
    def get_file_path_associated_file_2_site(self, request_id):
        f2s = FileToSiteData.query.filter_by(_id=request_id).first()
        file_data = FileData.query.filter_by(_id=f2s.file_id).first()

        user_folder_name = "{}".format(str(file_data.creator).split('@')[0])
        folder_full_path = os.path.join(os.path.join(current_app.config['UPLOAD_FOLDER'], user_folder_name)) 
        file_full_path = "{}/{}".format(folder_full_path, file_data.filename)

        return file_full_path

