from trainingmgr.schemas import ma
from trainingmgr.models import FeatureGroup

class FeatureGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FeatureGroup
        include_relationships = True
        load_instance = True
