import os

search_string = "AIzaSyAgKVVWGZweFCP5Z7bszIITB8FHPeE1no"
start_dir = "."
found_count = 0

print(f"--- Starting exhaustive search for 'ghost key' in all files. This may take time. ---")

for dirpath, dirnames, filenames in os.walk(start_dir):
    # Do not skip any directories, we are checking everywhere.
    if '.git' in dirnames:
        dirnames.remove('.git') # The only exception, not part of the project source.

    for filename in filenames:
        file_path = os.path.join(dirpath, filename)
        
        try:
            # Open as text, but use 'errors=ignore' to handle
            # binary files without crashing.
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if search_string in content:
                    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print(f"!!! GHOST KEY FOUND IN: {file_path} !!!")
                    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    found_count += 1
        except Exception as e:
            # Silently skip files we can't read (e.g., broken symlinks)
            pass 

print(f"--- Search complete. Found {found_count} total occurrences. ---")