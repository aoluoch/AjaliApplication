from flask import Flask, request, jsonify, session, make_response
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models.extensions import db
from models.user import User
from models.incident_report import IncidentReport
from models.incident_image import IncidentImage
from models.incident_video import IncidentVideo
from models.incident_comment import IncidentComment
from models.incident_reaction import IncidentReaction
from models.incident_review import IncidentReview
from models.notification import Notification
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
import os

# Create Flask app
app = Flask(__name__)

# Basic configuration
app.config.update( 
    SECRET_KEY='ajali-2',
    SQLALCHEMY_DATABASE_URI='postgresql://ajali_6n24_user:dmRedk3XcIbfm1QEDT7RWoOh4fuI0jfp@dpg-ct0d4ci3esus7389uu00-a.oregon-postgres.render.com/ajali_6n24',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    UPLOAD_FOLDER='uploads',
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB max file size
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'},
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),  # Session lasts 1 day
    SESSION_PERMANENT=True
)

# Configure CORS
CORS(app,
    resources={
        r"/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Create uploads folder
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize API
api = Api(app)

# Decorators
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return {'message': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return {'message': 'Authentication required'}, 401
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return {'message': 'Admin privileges required'}, 403
        return f(*args, **kwargs)
    return decorated

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_email = 'admin@ajali.com'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            username='admin',
            email=admin_email,
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# Resources
class AuthResource(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            return {'user': user.to_dict()}, 200
        
        return {'message': 'Invalid credentials'}, 401

class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already registered'}, 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return {'message': 'Registration successful'}, 201

class LogoutResource(Resource):
    def post(self):
        session.clear()
        return {'message': 'Logged out successfully'}, 200

class IncidentListResource(Resource):
    @login_required
    def post(self):
        files = request.files.getlist('files')
        data = request.form

        incident = IncidentReport(
            description=data['description'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            user_id=session['user_id'],
            status='pending'  # Set initial status to pending
        )
        db.session.add(incident)
        db.session.commit()

        # Handle file uploads
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                if file.content_type.startswith('image/'):
                    image = IncidentImage(image_url=filename, report_id=incident.id)
                    db.session.add(image)
                elif file.content_type.startswith('video/'):
                    video = IncidentVideo(video_url=filename, report_id=incident.id)
                    db.session.add(video)

        db.session.commit()

        # Create notification for admin
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                message=f"New incident reported by {incident.user.username} requires review",
                type='warning'
            )
            db.session.add(notification)
        db.session.commit()

        return incident.to_dict(), 201
    
    @login_required
    def get(self):
        """Get all incidents"""
        try:
            incidents = IncidentReport.query.order_by(IncidentReport.created_at.desc()).all()
            return jsonify([incident.to_dict() for incident in incidents])    
        except Exception as e:
            print(f"Error fetching incidents: {str(e)}")  # Debug log
            return {'message': 'Internal server error'}, 500

class IncidentResource(Resource):
    @login_required
    def get(self, incident_id):
        incident = IncidentReport.query.get_or_404(incident_id)
        return incident.to_dict()

    @login_required
    def put(self, incident_id):
        try:
            incident = IncidentReport.query.get_or_404(incident_id)
            
            # Check if user owns the incident
            if incident.user_id != session['user_id'] and not User.query.get(session['user_id']).is_admin:
                return {'message': 'Unauthorized'}, 403

            data = request.get_json()
            
            # Update basic fields
            if 'description' in data:
                incident.description = data['description']
            if 'latitude' in data:
                incident.latitude = float(data['latitude'])
            if 'longitude' in data:
                incident.longitude = float(data['longitude'])
            
            # Only admin can update status
            if User.query.get(session['user_id']).is_admin and 'status' in data:
                incident.status = data['status']

            db.session.commit()
            return incident.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500

    @login_required
    def delete(self, incident_id):
        try:
            incident = IncidentReport.query.get_or_404(incident_id)
            
            # Check if user owns the incident or is admin
            if incident.user_id != session['user_id'] and not User.query.get(session['user_id']).is_admin:
                return {'message': 'Unauthorized'}, 403

            # Delete associated media files
            for image in incident.images:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.image_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(image)

            for video in incident.videos:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], video.video_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(video)

            db.session.delete(incident)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500

    @login_required
    def delete(self, incident_id):
        incident = IncidentReport.query.get_or_404(incident_id)
        
        if not (session['user_id'] == incident.user_id or 
                User.query.get(session['user_id']).is_admin):
            return {'message': 'Unauthorized'}, 403

        db.session.delete(incident)
        db.session.commit()
        return '', 204

class CommentResource(Resource):
    @login_required
    def post(self, incident_id):
        data = request.get_json()
        comment = IncidentComment(
            content=data['content'],
            user_id=session['user_id'],
            incident_id=incident_id
        )
        db.session.add(comment)
        db.session.commit()
        return comment.to_dict(), 201

class ReactionResource(Resource):
    @login_required
    def post(self, incident_id):
        data = request.get_json()
        reaction = IncidentReaction(
            reaction_type=data['reaction_type'],
            user_id=session['user_id'],
            incident_id=incident_id
        )
        db.session.add(reaction)
        db.session.commit()
        return reaction.to_dict(), 201

class ReviewResource(Resource):
    @login_required
    def post(self, incident_id):
        data = request.get_json()
        review = IncidentReview(
            rating=data['rating'],
            content=data['content'],
            user_id=session['user_id'],
            incident_id=incident_id
        )
        db.session.add(review)
        db.session.commit()
        return review.to_dict(), 201

class NotificationResource(Resource):
    @login_required
    def get(self):
        notifications = Notification.query.filter_by(
            user_id=session['user_id']
        ).order_by(Notification.created_at.desc()).all()
        return jsonify([n.to_dict() for n in notifications])

    @login_required
    def put(self, notification_id):
        notification = Notification.query.get_or_404(notification_id)
        if notification.user_id != session['user_id']:
            return {'message': 'Unauthorized'}, 403
        notification.read = True
        db.session.commit()
        return notification.to_dict()

class UserResource(Resource):
    @admin_required
    def get(self):
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])

class UserDetailResource(Resource):    
    @admin_required
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        user.is_admin = data.get('is_admin', user.is_admin)
        db.session.commit()
        return user.to_dict()

    @admin_required
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return '', 204

# API Endpoints
api.add_resource(AuthResource, '/login')
api.add_resource(RegisterResource, '/register')
api.add_resource(LogoutResource, '/logout')
api.add_resource(IncidentListResource, '/incidents')
api.add_resource(IncidentResource, '/incidents/<int:incident_id>')
api.add_resource(CommentResource, '/incidents/<int:incident_id>/comments')
api.add_resource(ReactionResource, '/incidents/<int:incident_id>/reactions')
api.add_resource(ReviewResource, '/incidents/<int:incident_id>/reviews')
api.add_resource(NotificationResource, '/notifications')
api.add_resource(UserResource, '/users')
api.add_resource(UserDetailResource, '/users/<int:user_id>')

@app.after_request
def after_request(response):
    """Add CORS headers after each request"""
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:5174']:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Vary'] = 'Origin'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(debug=True, port=5000)
