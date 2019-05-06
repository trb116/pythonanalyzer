from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db

from .constants import ROLES, PERMISSIONS


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.SmallInteger, default=ROLES['USER'])
    # Relations
    deployments = db.relationship("Deployment", backref="user")
    notifications = db.relationship("Notification", backref="user")

    def __init__(self, username=None, password=None, email=None, role=None):
        self.username = username

        if password:
            self.set_password(password)

        self.email = email
        self.role = role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def can(self, action):
        return action in PERMISSIONS[self.role]

    def show_role(self):
        for role, number in ROLES.iteritems():
            if number == self.role:
                return role

    @classmethod
    def authenticate(self, email, password):
        """
        Returns user and authentication status.
        """
        user = User.query.filter_by(email=email).first()
        if user is not None:
            if user.check_password(password):
                return user, True

        return user, False


    def __repr__(self):
        return u'<User {0}>'.format(self.username)
