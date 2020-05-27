from app import db, ma
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import validates, fields, ValidationError
from uuid import uuid4

class FileToSiteData(db.Model):
    __tablename__ = 'filetosite'
    _id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_id = db.Column(UUID(as_uuid=True), nullable=False)
    site_id = db.Column(UUID(as_uuid=True), nullable=False)
    _status = db.Column(db.String(2048), nullable=False)


class FileToSiteSchema(ma.ModelSchema):
    file_id = fields.UUID(required=True)
    site_id = fields.UUID(required=True)
    _status = fields.Str(required=True)

    class Meta:
        model = FileToSiteData