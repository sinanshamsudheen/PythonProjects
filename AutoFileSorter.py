import os
import shutil
import sys

source_dir = "/home/zero/Downloads"
base_dir = "/home/zero"

extension_mapping = {
    # 📄 Documents
    ('.pdf', '.doc', '.txt', '.rtf', '.odt', '.md'): "Documents",
    ('.ppt','.docx', '.pptx', '.xls', '.xlsx', '.xlsm', '.xltx', '.xlam', '.csv', '.tsv'): "Documents/Office",
    ('.srt', '.vtt', '.sub'): "Documents/Subtitles",
    ('.epub', '.mobi', '.azw3'): "Documents/Books",

    # 🎵 Music & Audio
    ('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma'): "Music",

    # 🎬 Videos
    ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.mpeg'): "Videos",

    # 📦 Archives & Compressed Files
    ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'): "Compressed",

    # 🖼️ Images
    ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'): "Pictures",

    # 💻 Programs & Installers
    ('.AppImage', '.deb', '.rpm', '.exe', '.msi', '.sh', '.bin', '.run'): "Programs"
}

file_names = os.listdir(source_dir)
created_dirs = set()

def create_folder(path):
    if path not in created_dirs:
        os.makedirs(path, exist_ok=True)
        print(f"Ensured folder exists: {path}")
        created_dirs.add(path)

# Organize files
for file in file_names:
    file_path = os.path.join(source_dir, file)
    if not os.path.isfile(file_path):
        continue

    file_ext = os.path.splitext(file)[1].lower()

    dest_folder = None
    for extensions, folder in extension_mapping.items():
        if file_ext in extensions:
            dest_folder = os.path.join(base_dir, folder)
            break

    if dest_folder:
        create_folder(dest_folder)
        dest_path = os.path.join(dest_folder, file)
        if not os.path.exists(dest_path):
            shutil.move(file_path, dest_path)
            print(f"Moved: {file} → {dest_folder}")
    # Uncomment to move unknowns
    # else:
    #     others_folder = os.path.join(base_dir, "Others")
    #     create_folder(others_folder)
    #     shutil.move(file_path, os.path.join(others_folder, file))

print("✅ Files have been fully organized.")
sys.exit()
