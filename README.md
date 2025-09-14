# 🎓 Rural School Attendance System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)

An automated attendance system designed specifically for rural schools using face detection and recognition technology. This system provides an easy-to-use web interface for teachers and administrators to manage student attendance without requiring manual roll calls.

![Rural School Attendance System](https://via.placeholder.com/800x400/667eea/ffffff?text=Rural+School+Attendance+System)

## 🌟 Live Demo

The system includes both a full-featured version with real face recognition and a demo version for testing purposes.

## Features

- **Face Detection & Recognition**: Automatic student identification using advanced computer vision
- **Student Registration**: Easy registration system with photo capture
- **Real-time Attendance**: Mark attendance for multiple students simultaneously
- **Comprehensive Reports**: Generate detailed attendance reports and analytics
- **Offline Capability**: Works without internet connectivity (perfect for rural areas)
- **User-friendly Interface**: Modern, responsive web interface
- **Export Functionality**: Export attendance data to CSV format

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (lightweight, no server required)
- **Computer Vision**: OpenCV, face_recognition library
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Camera Integration**: WebRTC for browser-based camera access

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Webcam or camera device
- Modern web browser with camera support

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rural-school-attendance-system.git
   cd rural-school-attendance-system
   ```

2. **Install dependencies**
   
   **Option A: Demo Version (Quick Start)**
   ```bash
   pip install Flask Flask-SQLAlchemy numpy
   python app_demo.py
   ```
   
   **Option B: Full Version (Real Face Recognition)**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

3. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Start registering students and marking attendance!

### 🎯 Demo vs Full Version

| Feature | Demo Version | Full Version |
|---------|-------------|--------------|
| Student Registration | ✅ | ✅ |
| Face Detection | Simulated | Real OpenCV |
| Attendance Marking | ✅ | ✅ |
| Reports & Analytics | ✅ | ✅ |
| Installation Complexity | Simple | Requires OpenCV |

## Usage Guide

### 1. Register Students

1. Click on "Register Student" in the navigation menu
2. Fill in student details (ID, Name, Class, Section)
3. Click "Start Camera" to activate the webcam
4. Position the student in front of the camera
5. Click "Capture Photo" to take their picture
6. Click "Register Student" to save the information

### 2. Mark Attendance

1. Go to "Mark Attendance" section
2. Click "Start Camera" to begin
3. Students should look at the camera (multiple students can be detected)
4. Click "Mark Attendance" to capture and process the image
5. The system will automatically identify and mark present students
6. View the detected students and today's summary

### 3. View Reports

1. Navigate to "Reports" section
2. Select a date using the date picker
3. Optionally filter by class
4. Click "Generate Report" to view attendance data
5. Export reports to CSV format for external use

## System Requirements

### Minimum Hardware
- **Processor**: Intel Core i3 or equivalent
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Camera**: Any USB webcam or built-in camera

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: Version 3.7 or higher
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## Database Schema

The system uses SQLite with the following main tables:

- **Students**: Store student information and face encodings
- **Attendance**: Record daily attendance with timestamps and confidence scores

## Security Features

- Face encodings are stored securely in the database
- No raw images are stored (only processed encodings)
- Local database ensures data privacy
- No internet connection required for operation

## Troubleshooting

### Common Issues

1. **Camera not working**
   - Check browser permissions for camera access
   - Ensure no other applications are using the camera
   - Try refreshing the page

2. **Face not detected**
   - Ensure good lighting conditions
   - Student should look directly at the camera
   - Remove glasses or face coverings if possible

3. **Low recognition accuracy**
   - Re-register the student with a clearer photo
   - Ensure consistent lighting during registration and attendance

### Performance Tips

- Use good lighting for better face detection
- Keep the camera at eye level
- Ensure students are 2-3 feet from the camera
- Register students with clear, front-facing photos

## Future Enhancements

- Mobile app for teachers
- Multi-camera support
- Advanced analytics and insights
- Integration with school management systems
- Automated report generation and email delivery

## Support

For technical support or feature requests, please refer to the documentation or contact the system administrator.

## License

This project is designed for educational institutions and rural schools. Please ensure compliance with local privacy laws and regulations when using face recognition technology.

---

**Note**: This system is designed to work offline and is perfect for rural schools with limited internet connectivity. All data is stored locally and no external services are required.
