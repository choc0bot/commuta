from app import db

class commutra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), index=True, unique=True)
    commute_tag = db.Column(db.Integer, index=True)
    commute_string = db.Column(db.String(128), index=True)
    goal_name = db.Column(db.String(128), index=True)
    goal_value = db.Column(db.Integer)
    goal_savings = db.Column(db.Integer)
    carbon_number = db.Column(db.Integer)
    latitude = db.Column(db.Integer)
    longitude = db.Column(db.Integer)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3