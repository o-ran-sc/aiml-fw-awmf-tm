from . import db

class FeatureGroup(db.Model):
    __tablename__ = "featuregroup_info_table"
    id = db.Column(db.Integer, primary_key=True)
    featuregroup_name = db.Column(db.String(128), nullable=False)
    feature_list = db.Column(db.String(1000), nullable=False)
    datalake_source = db.Column(db.String(20000), nullable=False)
    host = db.Column(db.String(128), nullable=False)
    port = db.Column(db.String(128), nullable=False)
    bucket = db.Column(db.String(1000), nullable=False)
    token = db.Column(db.String(1000), nullable=False)
    db_org = db.Column(db.String(128), nullable=False)
    measurement = db.Column(db.String(1000), nullable=False)
    enable_dme = db.Column(db.Boolean, nullable=False)
    measured_obj_class = db.Column(db.String(20000), nullable=False)
    dme_port = db.Column(db.String(128), nullable=False)
    source_name = db.Column(db.String(20000), nullable=False)

    def __repr__(self):
        return f'<featuregroup {self.featuregroup_name}>'