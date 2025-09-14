from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import cv2
import numpy as np
import os
from datetime import datetime, date
import base64
from PIL import Image
import io
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rural-school-attendance-system-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    photo_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Student {self.name}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False, default='Present')
    confidence = db.Column(db.Float, nullable=True)
    
    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date}>'

class SimpleFaceRecognitionSystem:
    def __init__(self):
        # Load OpenCV's pre-trained face detection model
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.known_faces = {}
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all student face data from database"""
        students = Student.query.filter(Student.face_encoding.isnot(None)).all()
        self.known_faces = {}
        
        for student in students:
            if student.face_encoding:
                try:
                    face_data = pickle.loads(student.face_encoding)
                    self.known_faces[student.student_id] = {
                        'face_data': face_data,
                        'name': student.name,
                        'class': student.class_name,
                        'section': student.section
                    }
                except:
                    continue
    
    def extract_face_features(self, image_array):
        """Extract simple face features using OpenCV"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                # Get the largest face
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = largest_face
                
                # Extract face region
                face_roi = gray[y:y+h, x:x+w]
                
                # Resize to standard size
                face_roi = cv2.resize(face_roi, (100, 100))
                
                # Calculate histogram as a simple feature
                hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
                hist = hist.flatten()
                
                # Normalize
                hist = hist / (hist.sum() + 1e-7)
                
                return hist
            else:
                return None
        except Exception as e:
            print(f"Error extracting face features: {e}")
            return None
    
    def encode_face_from_image(self, image_data):
        """Extract face encoding from image data"""
        try:
            # Convert base64 to image
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Extract features
            features = self.extract_face_features(image_array)
            return features
            
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None
    
    def compare_faces(self, face1, face2, threshold=0.7):
        """Compare two face feature vectors"""
        try:
            # Calculate correlation coefficient
            correlation = np.corrcoef(face1, face2)[0, 1]
            return correlation > threshold, correlation
        except:
            return False, 0.0
    
    def recognize_faces(self, image_data):
        """Recognize faces in the given image using simple OpenCV detection"""
        try:
            # Convert base64 to image
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Detect faces
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            recognized_students = []
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))
                
                # Calculate histogram features
                hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
                hist = hist.flatten()
                hist = hist / (hist.sum() + 1e-7)
                
                # Compare with known faces
                best_match = None
                best_confidence = 0.0
                
                for student_id, student_data in self.known_faces.items():
                    is_match, confidence = self.compare_faces(hist, student_data['face_data'])
                    
                    if is_match and confidence > best_confidence:
                        best_match = student_id
                        best_confidence = confidence
                
                if best_match and best_confidence > 0.6:  # Minimum confidence threshold
                    student_data = self.known_faces[best_match]
                    recognized_students.append({
                        'student_id': best_match,
                        'name': student_data['name'],
                        'class': student_data['class'],
                        'section': student_data['section'],
                        'confidence': float(best_confidence)
                    })
            
            return recognized_students
            
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []

# Initialize face recognition system
face_system = SimpleFaceRecognitionSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/reports')
def reports():
    students = Student.query.all()
    return render_template('reports.html', students=students)

@app.route('/api/register_student', methods=['POST'])
def register_student():
    try:
        data = request.get_json()
        
        # Check if student already exists
        existing_student = Student.query.filter_by(student_id=data['student_id']).first()
        if existing_student:
            return jsonify({'success': False, 'message': 'Student ID already exists'})
        
        # Create new student
        student = Student(
            student_id=data['student_id'],
            name=data['name'],
            class_name=data['class_name'],
            section=data['section']
        )
        
        # Process face image if provided
        if 'photo' in data and data['photo']:
            face_encoding = face_system.encode_face_from_image(data['photo'])
            if face_encoding is not None:
                student.face_encoding = pickle.dumps(face_encoding)
                
                # Save photo
                os.makedirs('static/photos', exist_ok=True)
                photo_filename = f"{data['student_id']}.jpg"
                photo_path = os.path.join('static/photos', photo_filename)
                
                # Convert base64 to image and save
                image_data = data['photo']
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                image.save(photo_path)
                student.photo_path = photo_path
            else:
                return jsonify({'success': False, 'message': 'No face detected in the image. Please ensure good lighting and face the camera directly.'})
        
        db.session.add(student)
        db.session.commit()
        
        # Reload known faces
        face_system.load_known_faces()
        
        return jsonify({'success': True, 'message': 'Student registered successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Recognize faces in the image
        recognized_students = face_system.recognize_faces(data['image'])
        
        if not recognized_students:
            return jsonify({'success': False, 'message': 'No students recognized. Please ensure students are facing the camera with good lighting.'})
        
        marked_students = []
        today = date.today()
        
        for student_data in recognized_students:
            student_id = student_data['student_id']
            
            # Check if attendance already marked today
            existing_attendance = Attendance.query.filter_by(
                student_id=student_id,
                date=today
            ).first()
            
            if not existing_attendance:
                # Mark attendance
                attendance = Attendance(
                    student_id=student_id,
                    date=today,
                    time_in=datetime.utcnow(),
                    status='Present',
                    confidence=student_data['confidence']
                )
                db.session.add(attendance)
                marked_students.append(student_data)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {len(marked_students)} students',
            'students': marked_students
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/attendance_report')
def attendance_report():
    try:
        date_str = request.args.get('date', str(date.today()))
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all students
        all_students = Student.query.all()
        
        # Get attendance for the specified date
        attendance_records = Attendance.query.filter_by(date=report_date).all()
        attendance_dict = {record.student_id: record for record in attendance_records}
        
        report_data = []
        for student in all_students:
            attendance = attendance_dict.get(student.student_id)
            report_data.append({
                'student_id': student.student_id,
                'name': student.name,
                'class': student.class_name,
                'section': student.section,
                'status': attendance.status if attendance else 'Absent',
                'time_in': attendance.time_in.strftime('%H:%M:%S') if attendance else None,
                'confidence': attendance.confidence if attendance else None
            })
        
        return jsonify({'success': True, 'data': report_data, 'date': date_str})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/students')
def get_students():
    students = Student.query.all()
    students_data = []
    for student in students:
        students_data.append({
            'student_id': student.student_id,
            'name': student.name,
            'class': student.class_name,
            'section': student.section,
            'photo_path': student.photo_path,
            'created_at': student.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'success': True, 'students': students_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
