from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import os
from datetime import datetime, date
import base64
import io
import pickle
import random

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

class DemoFaceRecognitionSystem:
    """Demo version that simulates face recognition for testing purposes"""
    def __init__(self):
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
    
    def encode_face_from_image(self, image_data):
        """Demo: Generate a random face encoding"""
        try:
            # In a real system, this would extract actual face features
            # For demo purposes, we generate a random feature vector
            features = np.random.rand(128)  # 128-dimensional feature vector
            return features
            
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None
    
    def recognize_faces(self, image_data):
        """Demo: Simulate face recognition by randomly selecting registered students"""
        try:
            if not self.known_faces:
                return []
            
            # For demo purposes, randomly select 1-3 students from registered students
            # In a real system, this would use actual face recognition
            num_detected = random.randint(1, min(3, len(self.known_faces)))
            selected_students = random.sample(list(self.known_faces.keys()), num_detected)
            
            recognized_students = []
            for student_id in selected_students:
                student_data = self.known_faces[student_id]
                confidence = random.uniform(0.7, 0.95)  # Random confidence between 70-95%
                
                recognized_students.append({
                    'student_id': student_id,
                    'name': student_data['name'],
                    'class': student_data['class'],
                    'section': student_data['section'],
                    'confidence': float(confidence)
                })
            
            return recognized_students
            
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []

# Initialize demo face recognition system (will be done after app context is created)
face_system = None

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
    global face_system
    if face_system is None:
        face_system = DemoFaceRecognitionSystem()
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
                try:
                    from PIL import Image
                    image_data_clean = data['photo']
                    if image_data_clean.startswith('data:image'):
                        image_data_clean = image_data_clean.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data_clean)
                    image = Image.open(io.BytesIO(image_bytes))
                    image.save(photo_path)
                    student.photo_path = photo_path
                except ImportError:
                    # If PIL is not available, just store the encoding
                    pass
            else:
                return jsonify({'success': False, 'message': 'Error processing image. Please try again with good lighting.'})
        
        db.session.add(student)
        db.session.commit()
        
        # Reload known faces
        face_system.load_known_faces()
        
        return jsonify({'success': True, 'message': 'Student registered successfully! (Demo mode - face recognition simulated)'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    global face_system
    if face_system is None:
        face_system = DemoFaceRecognitionSystem()
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Recognize faces in the image (demo mode)
        recognized_students = face_system.recognize_faces(data['image'])
        
        if not recognized_students:
            return jsonify({'success': False, 'message': 'No students recognized. Please register students first. (Demo mode)'})
        
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
        
        message = f'Attendance marked for {len(marked_students)} students (Demo mode - simulated recognition)'
        return jsonify({
            'success': True,
            'message': message,
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
    print("=" * 60)
    print("RURAL SCHOOL ATTENDANCE SYSTEM - DEMO MODE")
    print("=" * 60)
    print("This is running in DEMO MODE for testing purposes.")
    print("Face recognition is simulated - it will randomly select")
    print("from registered students to demonstrate the system.")
    print("")
    print("To enable real face recognition:")
    print("1. Install OpenCV: pip install opencv-python")
    print("2. Install face_recognition: pip install face_recognition")
    print("3. Use app.py instead of app_demo.py")
    print("=" * 60)
    print("")
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
