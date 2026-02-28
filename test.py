import os
import numpy as np

# Original path with folders of individual frames
DATA_PATH = '.'  # Set this to current directory since 'Valid' is right here
# New path to drop the combined sequences
COMPRESSED_PATH = 'Compressed_Squat_Data'

actions = ['Valid']  # Only process the 'Valid' action
no_of_vids = 120

for action in actions:
    # Create the new directory for the action if it doesn't exist
    os.makedirs(os.path.join(COMPRESSED_PATH, action), exist_ok=True)
    
    for sequence in range(no_of_vids):
        sequence_folder = os.path.join(DATA_PATH, action, str(sequence))
        
        frames = []
        frame_no = 0
        
        # Load frames sequentially to maintain the correct time order
        while True:
            frame_path = os.path.join(sequence_folder, "{}.npy".format(frame_no))
            
            # If the frame file exists, add it to our list, else break the loop
            if os.path.exists(frame_path):
                frames.append(np.load(frame_path))
                frame_no += 1
            else:
                break
                
        # If we successfully loaded frames for this sequence, compress and save
        if len(frames) > 0:
            # Convert the list of 1D arrays into a single 2D array 
            # Output Shape: (number_of_frames, 132)
            rep_array = np.vstack(frames) 
            
            # Save the sequence as a single file: e.g. Compressed_Squat_Data/Valid/0.npy
            save_path = os.path.join(COMPRESSED_PATH, action, "{}.npy".format(sequence))
            np.save(save_path, rep_array)
            
print("Compression complete! Each rep is now a single 2D numpy array.")