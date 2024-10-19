from flask_marshmallow import Marshmallow

ma = Marshmallow()

from trainingmgr.schemas.trainingjob_schema import TrainingJobSchema
from trainingmgr.schemas.featuregroup_schema import FeatureGroupSchema

__all_ = ['TrainingJobSchema', 'FeatureGroupSchema']