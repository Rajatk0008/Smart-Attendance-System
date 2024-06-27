from flask import Flask, render_template, request, jsonify
import cv2
import face_recognition
import numpy as np
import os
import base64
import xlwt
from xlwt import Workbook
from datetime import date, datetime
import xlrd
from xlutils.copy import copy as xl_copy
import io
from PIL import Image

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialize a global dictionary to keep track of attendance taken in the current session
attendance_taken_global = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture_image')
def capture_image():
    return render_template('capture_image.html')

@app.route('/start_attendance')
def start_attendance():
    return render_template('attendance_feed.html')

@app.route('/save_image', methods=['POST'])
def save_image():
    data_url = request.form['image_data']
    name = request.form['name']
    data_folder = os.path.join(os.getcwd(), 'data')

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    image_data = base64.b64decode(data_url.split(',')[1])
    image_path = os.path.join(data_folder, f"{name}.png")
    
    with open(image_path, 'wb') as f:
        f.write(image_data)

    return jsonify(success=True)

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    data_url = request.form['image_data']
    subject = request.form['subject']
    data_folder = os.path.join(os.getcwd(), 'data')
    
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # Load known faces
    known_face_encodings = []
    known_face_names = []
    for filename in os.listdir(data_folder):
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            image_path = os.path.join(data_folder, filename)
            image = face_recognition.load_image_file(image_path)
            face_encoding = face_recognition.face_encodings(image)[0]
            name = os.path.splitext(filename)[0]
            known_face_encodings.append(face_encoding)
            known_face_names.append(name)

    # Decode the uploaded image
    image_data = base64.b64decode(data_url.split(',')[1])
    image = Image.open(io.BytesIO(image_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Initialize variables
    face_locations = []
    face_encodings = []
    face_names = []
    attendance_status = {}  # Dictionary to hold attendance status for each person
    process_this_frame = True

    # Workbook handling
    attendance_file = 'attendance_excel.xls'
    new_sheet = False


    if os.path.exists(attendance_file):
        rb = xlrd.open_workbook(attendance_file, formatting_info=True)
        wb = xl_copy(rb)
        if subject in rb.sheet_names():
            sheet = wb.get_sheet(subject)
            row = rb.sheet_by_name(subject).nrows
        else:
            sheet = wb.add_sheet(subject)
            row = 1
            new_sheet = True
    else:
        wb = Workbook()
        sheet = wb.add_sheet(subject)
        row = 1
        new_sheet = True

    if new_sheet:
        sheet.write(0, 0, 'Name')
        sheet.write(0, 1, str(date.today()))
        sheet.write(0, 2, 'Time')

    if name not in attendance_taken_global:
        attendance_taken_global[subject] = {}

    # Process the frame
    if process_this_frame:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)
            current_time = datetime.now().strftime('%H:%M:%S')
            if name != "Unknown":
                
                if name not in attendance_taken_global[subject]:
                    sheet.write(row, 0, name)
                    sheet.write(row, 1, "Present")
                    sheet.write(row, 2, current_time)
                    row += 1
                    attendance_taken_global[name] = True
                    attendance_status[name] = f"Attendance taken successfully for {name}"
                    try:
                        wb.save(attendance_file)
                    except PermissionError:
                        wb.save(f'attendance_excel_{subject}.xls')
                else:
                    attendance_status[name] = f"Attendance already taken for {name}"
            else:
                attendance_status[name] = "Next student"

    process_this_frame = not process_this_frame

    # Draw rectangles around faces
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    retval, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'image_data': jpg_as_text, 'attendance': attendance_status})


if __name__ == '__main__':
    app.run(debug=True)
