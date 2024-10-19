from trainingmgr.schemas import ma
from trainingmgr.models import TrainingJob

class TrainingJobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingJob
        include_relationships = True
        load_instance = True