import cv2
import os

# Set the current folder and data folder paths
CurrentFolder = os.getcwd()
data_folder = os.path.join(CurrentFolder, 'data')

# Create the data folder if it does not exist
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Initialize the camera
cam_port = 0
cam = cv2.VideoCapture(cam_port)

# Read the person's name from input
inp = input('Enter person name: ')
file_path = os.path.join(data_folder, f"{inp}.png")

# Reading the input using the camera
while True: 
    result, image = cam.read()
    if result:
        # Display the captured image
        cv2.imshow(inp, image)
        
        # Wait for the user to press 's' to save the image
        if cv2.waitKey(1) & 0xFF == ord('s'):
            cv2.imwrite(file_path, image)
            print(f"Image taken and saved to {file_path}")
            break
    else:
        print("No image detected. Please try again.")
        break

# Release the camera and close any open windows
cam.release()
cv2.destroyAllWindows()
