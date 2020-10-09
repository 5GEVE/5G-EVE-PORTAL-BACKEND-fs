from app import db, ma
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import validates, fields, ValidationError
from uuid import uuid4
import datetime

class FileData(db.Model):
    __tablename__ = 'filedata'
    _id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = db.Column(db.String(2048), nullable=False)
    creator = db.Column(db.String(2048), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class FileDataSchema(ma.ModelSchema):
    filename = fields.Str(required=True)
    creator = fields.Email(required=True)

    class Meta:
        model = FileData