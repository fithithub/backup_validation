import csv
import pandas as pd
import os
import hashlib
import json

# Function to calculate SHA-256 hash of a file
def calculate_hash(file_path, hash_type='sha256'):
    hash_obj = hashlib.new(hash_type)
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_all_files_in_dir(dir_path):
    # Using generator expression for more efficient file path construction
    return [os.path.normpath(os.path.join(root, file))
            for root, _, files in os.walk(dir_path) for file in files]

def split_into_batches(lst, batch_size=500):
    # List comprehension for more pythonic batch creation
    return (lst[i:i + batch_size] for i in range(0, len(lst), batch_size))

def save_hashes(dir_path, save_file):
    all_files = get_all_files_in_dir(dir_path)
    # Filter out directories without files directly inside them
    folders_with_files = {os.path.dirname(file) for file in all_files}
    num_folders_with_files = len(folders_with_files)
    counter = 0
    
    with open(save_file, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        folder_name_old = None
        for batch in split_into_batches(all_files):
            rows_to_write = []
            for file in batch:
                folder_name = os.path.dirname(file)
                if folder_name not in folders_with_files:
                    continue  # Skip folders that are not in the set of folders with files
                if folder_name != folder_name_old:
                    counter += 1
                    print(f'Carpeta {counter}/{num_folders_with_files}: {folder_name}')
                    folder_name_old = folder_name
                    folders_with_files.remove(folder_name)  # Remove to prevent re-counting
                try:
                    rows_to_write.append([file, calculate_hash(file)])
                except Exception as e:
                    print(f"No se pudo crear el hash para {file}: {e}")
            csvwriter.writerows(rows_to_write)

def load_saved_hashes(save_file, chunk_size=500):
    saved_hashes = {}
    seen_folders = set()
    for chunk in pd.read_csv(save_file, chunksize=chunk_size):
        for index, row in chunk.iterrows():
            saved_hashes[row[0]] = row[1]
            seen_folders.add(os.path.dirname(row[0]))
    return saved_hashes, seen_folders

def compare_hashes(all_files_set, saved_hashes):
    corrupt_files = []
    new_files = []
    processed_folders = set()  # Set to track folders processed
    folder_name_old = None
    counter = 0  # Counter for folders
    # Get all unique folders from all_files_set for progress reporting
    folders_with_files = {os.path.dirname(file) for file in all_files_set}
    num_folders_with_files = len(folders_with_files)
    for file in list(saved_hashes):
        folder_name = os.path.dirname(file)
        if folder_name not in processed_folders:
            if folder_name != folder_name_old:
                counter += 1
                print(f'Checking folder {counter}/{num_folders_with_files}: {folder_name}')
                folder_name_old = folder_name
            processed_folders.add(folder_name)  # Add to processed folders
        if file in all_files_set:
            current_hash = calculate_hash(file)
            if current_hash != saved_hashes.pop(file, None):  # Combines check and deletion
                corrupt_files.append(file)
        else:
            # File is not in the current set, therefore it's considered a new file.
            new_files.append(file)
        # Any remaining keys in saved_hashes are files that were not in the all_files_set
    remaining_files = set(saved_hashes.keys())
    return corrupt_files, new_files, remaining_files

def find_new_and_missing_folders(current_folders, seen_folders):
    new_folders = current_folders - seen_folders
    missing_folders = seen_folders - current_folders
    return new_folders, missing_folders

def check_hashes(dir_path, save_file,report_file):
    all_files_set = set(get_all_files_in_dir(dir_path))
    current_folders = {os.path.dirname(file) for file in all_files_set}
    
    try:
        saved_hashes, seen_folders = load_saved_hashes(save_file)
        corrupt_files, new_files, missing_files = compare_hashes(all_files_set, saved_hashes)
        new_folders, missing_folders = find_new_and_missing_folders(current_folders, seen_folders)
        
        for new_folder in new_folders:
            print(f'Nueva carpeta detectada: {new_folder}')
        for missing_folder in missing_folders:
            print(f'Carpeta faltante: {missing_folder}')
        for file in corrupt_files:
            print(f'Archivo corrupto: {file}')
        for file in new_files:
            print(f'Nuevo archivo detectado: {file}')
        for file in missing_files:
            print(f'Archivo faltante: {file}')
        
    except Exception as e:
        print(f"Error al procesar los hashes: {e}")
        return
    
    report = {
        'corrupt_files': corrupt_files,
        'new_files': new_files,
        'missing_files': list(missing_files),
        'new_folders': list(new_folders),
        'missing_folders': list(missing_folders)
    }

    # Save the report to a JSON file
    try:
        with open(report_file, 'w',encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f'Report saved to {report_file}')
    except Exception as e:
        print(f"Error al guardar el reporte: {e}")
    
    return report

# Main program
if __name__ == "__main__":

    # input_folder is the name of the folder to be checked, we ask the user
    input_folder = input("Ingrese el nombre de la carpeta a comprobar: ")
    dir_to_check = f"../{input_folder}/"  # Replace with your directory path
    hash_save_file = "saved_sha_values.csv"
    report_file = 'log_checked_files.json'

    # comprobamos en que dir estamos
    print(os.getcwd())
    opt = None
    while opt != 'c' and opt != 'g':
        opt = input("¿Desea comprobar hashes (c) o guardarlos (g)? ")
        if opt == 'g':
            print('Guardando hashes...')
            save_hashes(dir_to_check, hash_save_file)
            print('Hashes guardados.')
        elif opt == 'c':
            print('Comprobando hashes...')   
            # Call the function and print the report
            report = check_hashes(dir_to_check, hash_save_file, report_file)
        else:
            print('Opción no válida')

    # Pause before exiting
    input("Presione Enter para salir...")
