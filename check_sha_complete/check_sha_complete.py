# para compilar el codigo en un ejecutable
# pyinstaller --onefile --noconfirm your_script.py

# usa el archivo config.ini para configurar el programa
# además muestra el tiempo restante con tqdm y usa ProcessPoolExecutor en vez de ThreadPoolExecutor, paraleliza
# sin embargo es mucho más lento que el _simple

import os
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import configparser


# Function to calculate SHA-256 hash of a file
def calculate_hash(file_path, hash_type='sha256'):
    hash_obj = hashlib.new(hash_type)
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

# Function to recursively get all files in a directory and its subdirectories
def get_all_files_in_dir(dir_path):
    file_paths = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

# Calculate and save hashes
def save_hashes(dir_path, save_file, hash_type='sha256'):
    folder_name_old = None
    all_files = get_all_files_in_dir(dir_path)
    hashes = {}

    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor() as executor:

        results = list(tqdm(executor.map(calculate_hash, all_files, [hash_type]*len(all_files)), total=len(all_files)))

    for file, result in zip(all_files, results):
        folder_name_new =  file.split("\\")[1:-1] # todas las carpetas sin el nombre fotos
        folder_name_new = "/".join(folder_name_new)
        if folder_name_new != folder_name_old:
            print(f'Creando hash. Analizando carpeta: {folder_name_new}. Por favor espere...')
            folder_name_old = folder_name_new

        try:
            hashes[file] = result
        except Exception as e:
            print(f"No se pudo crear el hash para {file}: {e}")

    with open(save_file, 'w') as f:
        json.dump(hashes, f)

def check_hashes(dir_path, save_file, hash_type='sha256'):
    folder_name_old = None
    all_files = get_all_files_in_dir(dir_path)
    corrupt_files = []

    try:
        with open(save_file, 'r') as f:
            saved_hashes = json.load(f)
    except Exception as e:
        print(f"No se pudieron cargar los hashes: {e}")
        return

    with ThreadPoolExecutor() as executor:
        results = list(tqdm(executor.map(calculate_hash, all_files, [hash_type]*len(all_files)), total=len(all_files)))
    
    for file, result in zip(all_files, results):
        folder_name_new =  file.split("\\")[1:-1] # todas las carpetas sin el nombre fotos
        folder_name_new = "/".join(folder_name_new)
        if folder_name_new != folder_name_old:
            print(f'Comprobando hash. Analizando carpeta: {folder_name_new}. Por favor espere...')
            folder_name_old = folder_name_new

        try:
            if file in saved_hashes:
                if result != saved_hashes[file]:
                    corrupt_files.append(file)
                    print(f'Archivo corrupto: {file}. REVISAR')
            else:
                print(f"Nuevo archivo detectado: {file}")
        except Exception as e:
            print(f"No se pudo comprobar el hash para archivo {file}: {e}")

    # Check for missing files whose hashes were saved but not calculated in the current run
    missing_files = set(saved_hashes.keys()) - set(all_files)
    if missing_files:
        print("Archivos faltantes detectados:")
        for missing in missing_files:
            print(missing)
            corrupt_files.append(missing)  # Optional: Add missing files to the corrupt_files list

    return corrupt_files


# Main program
if __name__ == "__main__":
    dir_to_check = "../FOTOS/"  # Replace with your directory path
    hash_save_file = "NO_BORRAR_saved_hashes_files.json"
    log_path = 'archivos_corruptos.txt'
    
    # Read the configuration file
    config = configparser.ConfigParser()
    config.read('config.ini')
    dir_to_check = config.get('Settings', 'dir_to_check', fallback=dir_to_check)
    hash_save_file = config.get('Settings', 'hash_save_file', fallback=hash_save_file)
    hash_type = config.get('Settings', 'hash_type', fallback='sha256')
    log_file_name = config.get('Settings', 'log_file_name', fallback=log_path)


    # # Un/comment the lines below to save hashes for the first time
    print('Guardando hashes...')
    save_hashes(dir_to_check, hash_save_file)
    print('Hashes guardados.')
    
    print('Comprobando hashes... Esto puede tardar unos minutos')
    # Check for file corruption
    corrupt_files = check_hashes(dir_to_check, hash_save_file)
    
    # log corrupt files
    log_files = []
    if corrupt_files:
        print("Archivos corruptos detectados:")
        for file in corrupt_files:
            log_files.append(file)
            print(file)
    else:
        print("No hay archivos corruptos :)")

    # log files
    if log_files:
        with open(log_file_name, 'w') as f:
            for item in log_files:
                f.write("%s\n" % item)


    # Pause before exiting
    input("Presione Enter para salir...")
