A small utility script to automate the process of data entry for DXA body composition data exported as a DICOM file. This was created to help avoid manually re-entering the data into a spreadsheet for subsequent analysis. The scanner used for the research projects I was involved with is the Hologic Discovery W (software ver 13.2). The script uses regular expressions to parse the information contained in the tags of the .dcm file, so it is unlikely to work outside of the specific .dcm type and format (i.e. any other scanners, and likely other scan types or software versions). The reporting tool in the build-in software provided by the manufacturer can be used to generate a report for each scan, which can be viewed on screen or exported as a DICOM file. 

## Installation

1. Download the project: either `git clone` or download the zip file for this project.

1. Install required packages:

   **Basic: **`pip install numpy pandas pydicom Pillow openpyxl`

   **Recommended: ** Create a project virtual environment and install `requirements.txt`.

## Instructions

### Simple:

Copy all the .dcm files into a directory named `data` which should be created in the same location where the script files are.

Use:

```python extract_dcm_data.py -A --no_xlsx -d data```

This will parse the `data` directory, and extract the infromation from any .dcm files found in that directory or in any subdirectories. The individualized reports behaviour is suppressed, so there will be a single .csv file. The file will be named `dxa_aggregate_results.csv` and it will be in the same directory where the script files and the data folder are found.

### Detailed:
```python extract_dcm_data.py file.dcm```

This will output an excel file that contains participant information and the date of the scan, as well as the body composition data. In this example the file is placed directly in the directory with the script, and the output will be created in the same folder. 

In order to extract a file that is located elsewhere an obsolute or relative path can also to be provided (i.e. `"c:\path\to\file.dcm"` or `path/to/file.dcm` depending on the OS). Multiple files can be listed back-to-back separated by a space. Bash wild-cards can also be used. The reports for each individual file are saved separately.

```python extract_dcm_data.py -A file1.dcm file2.dcm fileX.dcm```

The -A flag will collapse data from each report into a single row, and aggregate the data of all the files listed. These results will be saved in the directory where the script is called. `... extract data -A --no_xlsx ...` can be used to generate a single aggregate report, and suppress the creation of individual report using the --no_xlsx flag.

```python extract_dcm_data.py -F file.dcm```

The -F (full_report) flag will save a pdf of the original report (the report that is displayed in the archiving system), an image of the scan, a csv with participant information and scan data, and another csv with the body composition data.

```python extract_dcm_data.py -d dir_name```

Will recursively search through the directory (i.e. including all the subfolders) to locate all the *.dcm and extract those. Each report again will be saved in the same folder with the .dcm file.

```python extract_dcm_data.py -o dir_name```

The -o flag can be used to specify an output directory. Any of the reports will be saved at that location instead the directory where the original .dcm file is found.

