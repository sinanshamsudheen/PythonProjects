#I made this to rename files in my local machine(especially for web series)
# for making the files compatible with Kodi

import os
import re

VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv', '.webm')

def clean_filename(filename):
    name, ext = os.path.splitext(filename)
    if ext.lower() not in VIDEO_EXTENSIONS:
        return None

    original_name = name

    # Replace S02 E07 or s01 e01 ➝ S02E07
    name = re.sub(r'(?i)(S\d{1,2})\s+(E\d{1,2})', r'\1\2', name)

    # Remove special characters that are problematic or not needed
    name = re.sub(r'[^\w\d\s.-]', '', name)

    # Replace multiple spaces or underscores with dot
    name = re.sub(r'[\s_]+', '.', name)

    # Remove multiple consecutive dots
    name = re.sub(r'\.{2,}', '.', name)

    # Strip leading/trailing dots
    name = name.strip('.')

    new_filename = f"{name}{ext}"
    return new_filename if new_filename != filename else None

def rename_files_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        print("❌ Invalid folder path.")
        return

    renamed_count = 0
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)
        if not os.path.isfile(old_path):
            continue

        new_filename = clean_filename(filename)
        if new_filename:
            new_path = os.path.join(folder_path, new_filename)
            print(f"Renaming:\n  {filename}\n→ {new_filename}\n")
            os.rename(old_path, new_path)
            renamed_count += 1

    print(f"✅ Finished. Renamed {renamed_count} files.")

# 🔧 Usage
if __name__ == "__main__":
    folder = input("Enter the full path to your folder: ").strip()
    rename_files_in_folder(folder)
