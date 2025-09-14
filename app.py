from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import cv2
import face_recognition
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

class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all student face encodings from database"""
        students = Student.query.filter(Student.face_encoding.isnot(None)).all()
        self.known_face_encodings = []
        self.known_face_names = []
        
        for student in students:
            if student.face_encoding:
                face_encoding = pickle.loads(student.face_encoding)
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(student.student_id)
    
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
            
            # Find face encodings
            face_encodings = face_recognition.face_encodings(image_array)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                return None
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None
    
    def recognize_faces(self, image_data):
        """Recognize faces in the given image"""
        try:
            # Convert base64 to image
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            # Find faces in the image
            face_locations = face_recognition.face_locations(image_array)
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            recognized_students = []
            
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        student_id = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        student = Student.query.filter_by(student_id=student_id).first()
                        if student:
                            recognized_students.append({
                                'student_id': student_id,
                                'name': student.name,
                                'class': student.class_name,
                                'section': student.section,
                                'confidence': float(confidence)
                            })
            
            return recognized_students
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []

# Initialize face recognition system
face_system = FaceRecognitionSystem()

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
                return jsonify({'success': False, 'message': 'No face detected in the image'})
        
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
            return jsonify({'success': False, 'message': 'No students recognized'})
        
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
