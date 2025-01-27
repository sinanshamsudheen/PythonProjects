import os
import shutil

def copy_files(source_folder, destination_folder):
    # Ensure the source folder exists
    if not os.path.exists(source_folder):
        print(f"Source folder does not exist: {source_folder}")
        return
    
    # Create the destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)
    
    # Walk through the source folder and copy files
    for root, _, files in os.walk(source_folder):
        for file in files:
            source_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, source_folder)
            dest_path = os.path.join(destination_folder, relative_path)
            dest_file_path = os.path.join(dest_path, file)
            
            # Skip files that already exist
            if os.path.exists(dest_file_path):
                # Optional: Compare file sizes or modification times to ensure equality
                if os.path.getsize(source_path) == os.path.getsize(dest_file_path):
                    print(f"Skipped (already exists): {source_path}")
                    continue
            
            # Ensure destination subfolder exists
            os.makedirs(dest_path, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, dest_file_path)
            print(f"Copied: {source_path} -> {dest_file_path}")
    
    print(f"File transfer complete. All new files copied to {destination_folder}")

# Define the source and destination folders
source = r"C:\Users\zero\CrossDevice\Nothing Phone (2a)\storage\DCIM\Camera"
destination = r"D:\DCIM_N2A"

# Run the copy operation
copy_files(source, destination)
