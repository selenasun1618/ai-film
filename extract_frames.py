import cv2
import os

def get_frames(video_path, timestamps, output_folder):
    
    # create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # open video file
    cap = cv2.VideoCapture(video_path)

    # opened successfully?
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second of the video

    for i, timestamp in enumerate(timestamps):
        frame_number = int(timestamp * fps)  # Calculate the frame number
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)  # Set the position of the video to the frame number

        ret, frame = cap.read()  # Read the frame
        if ret:
            cv2.imwrite(os.path.join(output_folder, f"frame_{i}.jpg"), frame)  # Save the frame as a JPEG file
        else:
            print(f"Error: Could not read frame at timestamp {timestamp}.")

    cap.release()

if __name__ == "__main__":
    video_path = 'movie.mov'
    timestamps = [3, 10, 50]
    output_folder = 'frame_screenshots'

    get_frames(video_path, timestamps, output_folder)
