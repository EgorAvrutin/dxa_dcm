#!/usr/bin/env python

import argparse
import os
import pandas as pd
from dxa_dcm_utils import *

EXCEL_REPORT = True
FULL_REPORT = False
AGGREGATE_REPORTS = False

def _init_cmd_parser ():
    parser = argparse.ArgumentParser(prog="Extract DXA DICOM Data",
                                     description="""\
                                         This script parses the DICOM files 
                                         exported by the scanner archiving 
                                         software and extracts the relevant 
                                         information""")
    
    parser.add_argument('files', nargs='*',
                        help='List of DICOM files')
    
    parser.add_argument("-d",
                        "--directory",
                        help="""\
                            Locate all the .dcm files in a directory. 
                            Parses a directory recursively 
                            (i.e. including all subdirectories)""",
                        nargs=1,
                        action="store")
        
    parser.add_argument("-o",
                        "--output_dir",
                        help="""\
                            path to directory for output files. 
                            By default all output is in the same directory 
                            where the .dcm file is.""",
                        nargs=1,
                        action="store")
    
    parser.add_argument("-F",
                        "--full_report",
                        help="output",
                        action="store_true")

    parser.add_argument("-A",
                        "--aggregate",
                        help="collapse and aggregate results into a single csv file",
                        action="store_true")
    
    parser.add_argument("--no_xlsx",
                        help="deactivate the generation of default excel output",
                        action="store_false")    
    
    _verify_args (parser)
    
    return parser.parse_args()

def _verify_args (parser):
    args = parser.parse_args()
    
    if args.output_dir:
        if not os.path.isdir (args.output_dir[0]): 
            parser.error("Output directory does not exist! Verify path")
        
    if args.directory:
        if not os.path.isdir (args.directory[0]): 
            parser.error("Data directory does not exist! Verify path")
    
    if args.files:
        for f in args.files:
            if not os.path.isfile (f): 
                parser.error(f"File {f} does not exist!")
            elif ".dcm" not in f.lower() :
                parser.error(f"File {f} is not a .dcm file!")
            
    # if args.files and args.directory: parser.error('The files and directory arguments are mutually exclusive, please only use one')

def parse_directory (dir_path):
    dicom_files = []
    for dir_name, _, files in os.walk(dir_path):
        dicom_files.extend ([os.path.join(dir_name,f) for f in files if ".dcm" in f.lower()])
    return dicom_files

def save_full_report(save_dir, dcm, pt_info, pt_data):
    pt_id = pt_info["pt_id"]
    save_dir = os.path.join (save_dir, pt_id)
    
    if not os.path.exists (save_dir): os.mkdir (save_dir)
    
    save_report_pdf (dcm, save_dir)
    save_scan_image (dcm, save_dir)
    
    pt_data.to_csv (os.path.join(save_dir, "results_summary.csv"))
    pt_info.to_csv (os.path.join(save_dir, "pt_info.csv"), header=True)


def save_excel_report (save_dir, pt_info, pt_data):
    pt_id = pt_info["pt_id"]
    
    # print (save_dir)
    
    with pd.ExcelWriter(os.path.join(save_dir, "_".join ([pt_id, "dxa_summary.xlsx"]))) as writer:
        pt_info.to_frame(name="Values").to_excel(writer, sheet_name='pt_info')
        pt_data.to_excel(writer, sheet_name='dxa_data')

def main (dcm_files, output_dir = None):
    if AGGREGATE_REPORTS:
        df = pd.DataFrame()
        
    dcm_save_dir = output_dir
    for f in dcm_files:
        if not output_dir: dcm_save_dir = os.path.dirname(f)     
        dcm = read_dcm_file (f)

        pt_info = extract_pt_info (dcm)  
        pt_data = generate_report_df (dcm)
        
        if FULL_REPORT: save_full_report(dcm_save_dir, dcm, pt_info, pt_data)
        
        if EXCEL_REPORT: save_excel_report (dcm_save_dir, pt_info, pt_data)
        
        if AGGREGATE_REPORTS:
            df = df.append (pt_info.append (collapse_report_df (pt_data))\
                            .to_frame ()\
                                .transpose(), 
                                ignore_index=True
                                )
    if AGGREGATE_REPORTS:
        if not output_dir: report_save_dir = os.getcwd()
        df.to_csv (os.path.join(report_save_dir, "dxa_aggregate_results.csv"), index=False)


if __name__ == "__main__":
    args = _init_cmd_parser()

    EXCEL_REPORT = args.no_xlsx
    FULL_REPORT = args.full_report
    AGGREGATE_REPORTS = args.aggregate
    
    if args.output_dir:
        output_dir = args.output_dir[0]
    else:
        output_dir = None
    
    dcm_files =  args.files    
    if args.directory:
        dicoms_in_dir = parse_directory(args.directory[0])
        dcm_files.extend(dicoms_in_dir)
        
    dcm_files = set (dcm_files)

    main (dcm_files, output_dir)

