from app import db, ma
from sqlalchemy.dialects.postgresql import UUID
from marshmallow import validates, fields, ValidationError
from uuid import uuid4

class SiteData(db.Model):
    __tablename__ = 'sitedata'
    _id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sitename = db.Column(db.String(2048), nullable=False, unique=True)


class SiteDataSchema(ma.ModelSchema):
    sitename = fields.Str(required=True)

    class Meta:
        model = SiteData