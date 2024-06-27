import face_recognition
import cv2
import numpy as np
import os
import xlwt
from xlwt import Workbook
from datetime import date, datetime
import xlrd
from xlutils.copy import copy as xl_copy
import tkinter as tk

# Set the current folder and data folder paths
CurrentFolder = os.getcwd()
data_folder = os.path.join(CurrentFolder, 'data')

# Load all images from the data folder
known_face_encodings = []
known_face_names = []

# Loop through each image file in the data folder
for filename in os.listdir(data_folder):
    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
        # Load the image
        image_path = os.path.join(data_folder, filename)
        image = face_recognition.load_image_file(image_path)
        
        # Get the face encoding
        face_encoding = face_recognition.face_encodings(image)[0]
        
        # Get the name from the filename (assuming the filename is the person's name)
        name = os.path.splitext(filename)[0]
        
        # Append the encoding and name to the respective lists
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
stop_cam = False

# Workbook handling
try:
    rb = xlrd.open_workbook('attendence_excel.xls', formatting_info=True)
    wb = xl_copy(rb)
except PermissionError:
    print("Permission denied for the existing attendance file. Creating a new file.")
    rb = xlwt.Workbook()
    wb = rb

inp = input('Enter Subject: ')
sheet1 = wb.add_sheet(inp)
sheet1.write(0, 0, 'Name')
sheet1.write(0, 1, str(date.today()))
sheet1.write(0, 2, 'Time')
row = 1
col = 0
attendance_taken = {}

# Function to stop the webcam feed
def stop_webcam():
    global stop_cam
    stop_cam = True

# Tkinter setup
root = tk.Tk()
root.title("Smart Attendance System")

# Add a stop button
stop_button = tk.Button(root, text="Stop", command=stop_webcam)
stop_button.pack()

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

while True:
    if stop_cam:
        print("Data saved")
        break

    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)
            current_time = datetime.now().strftime('%H:%M:%S')
            if name != "Unknown":
                if name not in attendance_taken:
                    sheet1.write(row, col, name)
                    col = col + 1
                    sheet1.write(row, col, "Present")
                    col = col + 1
                    sheet1.write(row, col, current_time)
                    row = row + 1
                    col = 0
                    print(f"Attendance taken for: {name} at {current_time}")
                    try:
                        wb.save('attendence_excel.xls')
                    except PermissionError:
                        print("Permission denied for the existing attendance file. Saving to a new file.")
                        wb.save('attendence_excel_new.xls')
                    attendance_taken[name] = True
                else:
                    print(f"Attendance already taken for: {name}")
            else:
                print("Next student")

    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Process the Tkinter events
    root.update_idletasks()
    root.update()

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xff == ord('q'):
        print("Data saved")
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
root.destroy()