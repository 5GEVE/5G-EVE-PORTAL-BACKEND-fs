from app import db, ma
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import validates, fields, ValidationError
from uuid import uuid4

class User(db.Model):
    __tablename__ = 'user'
    _id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    roles = db.Column(db.ARRAY(db.String(120)))
    groups = db.Column(db.ARRAY(db.String(120)))

class UserSchema(ma.ModelSchema):
    email = fields.String(required=True)

    class Meta:
        model = User


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_file'
    _id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(120), nullable=False)
    sites = db.Column(db.ARRAY(db.String(120)))
    user_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)  
 
class UploadedFileSchema(ma.ModelSchema):
    name = fields.String(required=True)
    sites = fields.List(fields.String(), required=True)
    user_email = fields.String(required=True)

    class Meta:
        model = UploadedFile