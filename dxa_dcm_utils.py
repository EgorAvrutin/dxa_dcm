from datetime import datetime
import os
import re
import pydicom
import numpy as np
import pandas as pd
from PIL import Image


def read_dcm_file (file_path):
    if not os.path.exists (file_path):
        print ("ERROR: INVALID FILE PATH: ", file_path)
        return None
    
    try:
        dcm = pydicom.dcmread(file_path)
    except:
        print ("ERROR: UNABLE TO LOAD DICOM: ", file_path)
        return None
    
    if dcm.Manufacturer != "HOLOGIC" and dcm.ManufacturerModelName[:11] != 'Discovery W':
        print ("ERROR: THE DICOM FILE DOES NOT CONTAIN HOLOGIC DISCOVERY W BASED DATA: ", file_path)
        return None
    
    if dcm.SoftwareVersions != "13.2":
        print ("WARNING: The DICOM was created using an a software version this scripts was not tested on. CHECK THE RESULTS!", file_path)
        
    return dcm


def extract_report_details (dcm):
    dmc_contents = dcm._dict
    
    tag_list = []
    for i, tag in enumerate (dmc_contents):
        tag_list.append(tag)
    
    table_script = str(dmc_contents[tag_list[28]].value)
    
    
    str_list = table_script.split (r"\r\n")
    
    return str_list


def generate_report_df (dcm):
    
    str_list = extract_report_details(dcm)
    
    table_vars = [var for var in str_list if "ResultsTable" in var]
              
    pattern = re.compile(r'\[ \d+\]\[ \d+\]')
    index = re.compile(r'\d+')
    value = re.compile(r'".*"')
    
    all_matches = []
    for line in table_vars:
        matches = pattern.finditer (line)
        for m in matches:
            idx = index.findall(m.group(0))
            var = value.findall(m.string)
            all_matches.append((int (idx[0]),int (idx[1]), var[0][1:-1]))
    
    cols = {}
    col_names = [match[2] for match in all_matches if match[1]==0]
    for col in col_names:
        cols[col]= []
    #col_idx = set([match[1] for match in all_matches])
    
    
    for match in all_matches:
        for i, col in enumerate (col_names):
            if match[0] == i and match[1] != 0:
                if match[2] == " ":
                    cols[col].append (np.NaN)
                else:
                    cols[col].append (match[2])
            
            
                
    df = pd.DataFrame.from_dict (cols)
    df.set_index("Region", inplace=True)
    df = df.apply(pd.to_numeric)
    
    df.rename(index={'Area[cm<sup><small>2</small></sup>]':'Area[(cm^2)]',
                     'BMD[g/cm<sup><small>2</small></sup>]':"BMD[(g/cm^2)]"},
              inplace=True)

    return df

def collapse_report_df (df, var_names = ['Area[(cm^2)]', 'BMC[(g)]', 
                                         'BMD[(g/cm^2)]', 'Fat[(g)]', 
                                         'Lean[(g)]', 'Total[(g)]', '% Fat[(%)]']):
    output = pd.Series(dtype = float)
    for c in df.columns:
        for v in var_names:
            #This cleans up the variable name so its compatible with R.
            key = "_".join ([c, v.split("[")[0]])\
                .replace(" ", "_")\
                    .replace("%", "pct")\
                        .replace("-", "")\
                            .replace("+", "and").lower()
            value = df[c][v]
            output[key] = value
    return output

def get_pixel_array (dcm):
    return dcm.pixel_array

def extract_scan_image (dcm):
    results_list = extract_report_details (dcm)  
    
    number_re = re.compile(r'\d+')
    image_details = {}
    
    for line in results_list:   
        if "ImageXPos" in line:
            var = number_re.findall(line)
            image_details["ImageXPos"] = int(var[0])
        elif "ImageYPos" in line:
            var = number_re.findall(line)
            image_details["ImageYPos"] = int(var[0])  
        elif "ImageXSize" in line:
            var = number_re.findall(line)
            image_details["ImageXSize"] = int(var[0]) 
        elif "ImageYSize" in line:
            var = number_re.findall(line)
            image_details["ImageYSize"] = int(var[0])
    
        
    image_array = dcm.pixel_array
    
    scan_image = image_array[image_details["ImageYPos"]:image_details["ImageYPos"]+image_details["ImageYSize"], 
                             image_details["ImageXPos"]:image_details["ImageXPos"]+image_details["ImageXSize"]]
    
    return scan_image


def parse_scan_info (scan_info):
    date, scan_id = scan_info.replace(" ", "").split ("-")
    date = datetime.strptime(date, "%d%B%Y").date().isoformat()
    return (date, scan_id)


def parse_ptid (name):
    return "".join ([x for x in name if x.isalnum()])

def strip_num (string):
    r = re.search(r'\d+\.*\d*',string)
    if r:
        return float(r.group())
    else:
        return None
    
def parse_DOB (dob_string):
    return datetime.strptime(dob_string, "%d.%m.%Y").date().isoformat()


def parse_pt_info (pt_chars):
    srs = pd.Series()
    srs["pt_id"] = parse_ptid (pt_chars["PatientName"])
    srs["scan_date"] = parse_scan_info(pt_chars["Scan"])[0]
    srs["sex"] = pt_chars["PatientSex"]
    srs["dob"] = parse_DOB (pt_chars["DOB"])
    srs["age"] = pt_chars["Age"]
    srs["height"] = strip_num (pt_chars["Height"]) / 100
    srs["weight"] = strip_num (pt_chars["Weight"])
    srs["bmi"] = srs["weight"]/(srs["height"] ** 2)
    srs["ethinicity"] = pt_chars["Ethnicity"]
    srs["scan_id"] = parse_scan_info(pt_chars["Scan"])[1]
    return srs

def extract_pt_info (dcm):
    scan_details_keys = ["Scan", "PatientName", "PatientSex", "Ethnicity", "Height", "Weight", "DOB", "Age"]
    str_list = extract_report_details(dcm)

    pt_chars = {}
    for line in str_list:
        for k in scan_details_keys:
            r = re.compile(f'{k} = "(.*)";')
            result = r.match(line)
            if result:
                pt_chars[k] = result.group(1)
                
    return parse_pt_info (pt_chars)


def save_report_pdf (dcm, save_dir, report_name = "DXA_Report.pdf"):
    img_array = get_pixel_array (dcm)
    pdf_path = os.path.join(save_dir, report_name)
    Image.fromarray (img_array).save (pdf_path, "PDF", resolution = 100.0)

def save_scan_image (dcm, save_dir, image_file_name = "scan_image.bmp"):
    scan_image = extract_scan_image (dcm)
    bmp_path = os.path.join(save_dir, "scan_image.bmp")
    Image.fromarray (scan_image).save (bmp_path, "BMP", resolution = 100.0)   

