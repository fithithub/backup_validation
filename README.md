# Overview

This repository provides code and instructions designed to verify the integrity of files in a directory by calculating and comparing SHA-256 hashes, alerting users of any new, missing, or changed files.

Useful for time-based checks (e.g., within a year) as well as between disks/backups with the same folder and file structure. It alerts you of any changes in the files, missing files, and new files.

Some prints and comments in the script are in spanish but these are not essential for the understanding or usage of the tool.

### Files:

- **`check_sha_simple.py`**: Contains the code for the executable. It either stores the SHA values or checks if these values match the files. The user must specify the name of the folder and one of the following options:
	- **g**: g for generate. Should be run in the root directory folder, shared with the folder with files to verify, e.g., 'Pictures'. When executed, it creates a *csv* file with a hash for each file.
	- **c**: c for check. Utilizes the *csv* file with file hashes to verify that none have changed. A log *JSON* file is generated with a list of modified/corrupt files and missing or new files and folders.
  
- **`check_sha_complete`**: Contains additional functionalities like loading paths from a `config.ini` file, multithreading, and a loading bar. However, the simple version seemed to be faster, so this was not continued.

### Instructions

Follow these steps when executing the `check_sha_simple.py`:

1. **If you already have the *csv* file and want to check**: run the check option (c), else jump to step 4.

2. **Issue Detection**: If it detects new files, missing or corrupt ones, resolve the issues. In case of corrupt files, verify if it's a false positive, else try to replace it ASAP from a backup.

3. **File Modification**: If files are modified, delete the *csv* file.

4. **Hash Saving**: Run the storing hash option (g).

### Performance:

On a "normal" laptop it took about a minute to run either the storing or checking option for 100GB.