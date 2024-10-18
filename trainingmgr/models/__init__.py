from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from trainingmgr.models.trainingjob import TrainingJob
from trainingmgr.models.featuregroup import FeatureGroup

__all_ = ['TrainingJob', 'FeatureGroup']