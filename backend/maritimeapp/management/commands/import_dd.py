import csv
import datetime
import glob
import io
import os
import re
import subprocess
import tarfile
from datetime import datetime
from functools import partial
from multiprocessing import Pool
from time import sleep

import pandas as pd
import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from maritimeapp.models import *

download_folder_path = os.path.join(".", "src")
csv_dir = os.path.join(".", "src_csvs")
number_of_files = 0
download_folder_path = os.path.join(".", "src")
csv_dir = os.path.join(".", "src_csvs")
number_of_files = 0
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
log_filename = f"log_dbpush_{timestamp}.txt"


def get_single_match(directory_path, pattern):
    matching_files = glob.glob(os.path.join(directory_path, pattern))
    return matching_files[0] if matching_files else None


def correct_date(value):
    try:
        date_str = value.split(":")
        return f"{date_str[2]}-{date_str[1]}-{date_str[0]}"
    except ValueError:
        print("debug value err")


class Command(BaseCommand):
    help = "Migrate man data tar to database."

    site_cols = ["name", "aeronet_number", "description", "span_date"]
    site_df = pd.DataFrame(columns=site_cols)

    @classmethod
    def setup(self):
        if os.path.exists(download_folder_path):
            print("Folder exists -> moving to creating threaded processes.")
        else:
            print("Folder does not exist -> creating folder and downloading man data.")
            os.makedirs(download_folder_path)

            # Download the MAN file from the static url
            url = "https://aeronet.gsfc.nasa.gov/new_web/All_MAN_Data_V3.tar.gz"
            response = requests.get(url)

            if not response.ok:
                print("Server Offline. Attempt again Later.")
                return

            tar_contents = response.content
            with tarfile.open(fileobj=io.BytesIO(tar_contents), mode="r:gz") as tar:
                tar.extractall(path=download_folder_path)
            print(
                f"MAN Data extracted to {download_folder_path} moving to extract and build."
            )

        to_be_csv_files = glob.glob(
            os.path.join(download_folder_path, "**", "*/*"), recursive=True
        )
        subprocess.run(["mkdir", "-p", csv_dir])
        subprocess.run(["cp", "-fr"] + to_be_csv_files + [csv_dir], check=True)
        print(f"Folders copied to csv_directory moving to processing.")

    def csv(self):

        files_csv = glob.glob("./src_csvs/*")
        aod_dict = {
            "Date(dd:mm:yyyy)": "date_DD_MM_YYYY",
            "Time(hh:mm:ss)": "time_HH_MM_SS",
            "Air Mass": "air_mass",
            "AOD_340nm": "aod_340nm",
            "AOD_380nm": "aod_380nm",
            "AOD_440nm": "aod_440nm",
            "AOD_500nm": "aod_500nm",
            "AOD_675nm": "aod_675nm",
            "AOD_870nm": "aod_870nm",
            "AOD_1020nm": "aod_1020nm",
            "AOD_1640nm": "aod_1640nm",
            "Water Vapor(cm)": "water_vapor_CM",
            "440-870nm_Angstrom_Exponent": "angstrom_exponent_440_870",
            "STD_340nm": "std_340nm",
            "STD_380nm": "std_380nm",
            "STD_440nm": "std_440nm",
            "STD_500nm": "std_500nm",
            "STD_675nm": "std_675nm",
            "STD_870nm": "std_870nm",
            "STD_1020nm": "std_1020nm",
            "STD_1640nm": "std_1640nm",
            "STD_Water_Vapor(cm)": "std_water_vapor_CM",
            "STD_440-870nm_Angstrom_Exponent": "std_angstrom_exponent_440_870",
            "Number_of_Observations": "number_of_observations",
            "Last_Processing_Date(dd:mm:yyyy)": "last_processing_date_DD_MM_YYYY",
            "AERONET_Number": "aeronet_number",
            "Microtops_Number": "microtops_number",
        }

        sda_dict = {
            "Date(dd:mm:yyyy)": "date_DD_MM_YYYY",
            "Time(hh:mm:ss)": "time_HH_MM_SS",
            "Julian_Day": "julian_day",
            "Air_Mass": "air_mass",
            "Total_AOD_500nm(tau_a)": "total_aod_500nm",
            "Fine_Mode_AOD_500nm(tau_f)": "fine_mode_aod_500nm",
            "Coarse_Mode_AOD_500nm(tau_c)": "coarse_mode_aod_500nm",
            "FineModeFraction_500nm(eta)": "fine_mode_fraction_500nm",
            "CoarseModeFraction_500nm(1_eta)": "coarse_mode_fraction_500nm",
            "2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)": "regression_dtau_a",
            "RMSE_Fine_Mode_AOD_500nm(Dtau_f)": "rmse_fine_mode_aod_500nm",
            "RMSE_Coarse_Mode_AOD_500nm(Dtau_c)": "rmse_coarse_mode_aod_500nm",
            "RMSE_FMF_and_CMF_Fractions_500nm(Deta)": "rmse_fmf_and_cmf_fractions_500nm",
            "Angstrom_Exponent(AE)_Total_500nm(alpha)": "angstrom_exponent_total_500nm",
            "dAE/dln(wavelength)_Total_500nm(alphap)": "dae_dln_wavelength_total_500nm",
            "AE_Fine_Mode_500nm(alpha_f)": "ae_fine_mode_500nm",
            "dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)": "dae_dln_wavelength_fine_mode_500nm",
            "870nm_Input_AOD": "aod_870nm",
            "675nm_Input_AOD": "aod_675nm",
            "500nm_Input_AOD": "aod_500nm",
            "440nm_Input_AOD": "aod_440nm",
            "380nm_Input_AOD": "aod_380nm",
            "STDEV-Total_AOD_500nm(tau_a)": "stdev_total_aod_500nm",
            "STDEV-Fine_Mode_AOD_500nm(tau_f)": "stdev_fine_mode_aod_500nm",
            "STDEV-Coarse_Mode_AOD_500nm(tau_c)": "stdev_coarse_mode_aod_500nm",
            "STDEV-FineModeFraction_500nm(eta)": "stdev_fine_mode_fraction_500nm",
            "STDEV-CoarseModeFraction_500nm(1_eta)": "stdev_coarse_mode_fraction_500nm",
            "STDEV-2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)": "stdev_regression_dtau_a",
            "STDEV-RMSE_Fine_Mode_AOD_500nm(Dtau_f)": "stdev_rmse_fine_mode_aod_500nm",
            "STDEV-RMSE_Coarse_Mode_AOD_500nm(Dtau_c)": "stdev_rmse_coarse_mode_aod_500nm",
            "STDEV-RMSE_FMF_and_CMF_Fractions_500nm(Deta)": "stdev_rmse_fmf_and_cmf_fractions_500nm",
            "STDEV-Angstrom_Exponent(AE)_Total_500nm(alpha)": "stdev_angstrom_exponent_total_500nm",
            "STDEV-dAE/dln(wavelength)_Total_500nm(alphap)": "stdev_dae_dln_wavelength_total_500nm",
            "STDEV-AE_Fine_Mode_500nm(alpha_f)": "stdev_ae_fine_mode_500nm",
            "STDEV-dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)": "stdev_dae_dln_wavelength_fine_mode_500nm",
            "STDEV-870nm_Input_AOD": "stdev_aod_870nm",
            "STDEV-675nm_Input_AOD": "stdev_aod_675nm",
            "STDEV-500nm_Input_AOD": "stdev_aod_500nm",
            "Solar_Zenith_Angle": "solar_zenith_angle",
            "STDEV-440nm_Input_AOD": "stdev_aod_440nm",
            "STDEV-380nm_Input_AOD": "stdev_aod_380nm",
            "Number_of_Observations": "number_of_observations",
            "Last_Processing_Date(dd:mm:yyyy)": "last_processing_date_DD_MM_YYYY",
            "AERONET_Number": "aeronet_number",
            "Microtops_Number": "microtops_number",
        }

        def prepare_extract_data(file):
            df = None
            level = None
            pi_info = None
            pi = None
            pi_email = None
            cruise = None
            lines = None
            outputcsv = None
            header = None

            try:
                with open(file, "r", encoding="latin-1") as f:
                    lines = f.readlines()

                pi_info = lines[3]
                pi = (
                    pi_info.split("=")[1]
                    .split(",")[0]
                    .replace("\n", "")
                    .replace(",", ";")
                )
                pi_email = (
                    pi_info.split(",Email=")[1].replace("\n", "").replace(",", ";")
                )
                cruise = lines[1].split(",")[0].replace("\n", "")

                if ".lev" in file:
                    level = file.split(".lev")[1]
                    outputcsv = "." + file.split(".")[1] + "_AOD_" + level + ".csv"
                else:
                    level = file.split(".ONEILL_")[1]
                    outputcsv = "." + file.split(".")[1] + "_SDA_" + level + ".csv"
                header = lines[4].strip().split(",")
                reg = re.compile(".*\(int\)")
                bad_cols = list(filter(reg.match, header))
                if bad_cols:
                    for col in bad_cols:
                        header[header.index(col)] = col.replace("(int)", "")

                if "ONEILL_" in file:
                    translated_cols = [
                        sda_dict.get(header, header) for header in header
                    ]
                else:
                    translated_cols = [
                        aod_dict.get(header, header) for header in header
                    ]
                data = [line.strip().split(",") for line in lines[5:]]
                df = pd.DataFrame(data, columns=header)

                df.columns = translated_cols
                df["coordinates"] = df.apply(
                    lambda row: Point(float(row["Longitude"]), float(row["Latitude"])),
                    axis=1,
                )
                df["coordinates_wkt"] = df.apply(
                    lambda row: Point(float(row["Longitude"]), float(row["Latitude"])),
                    axis=1,
                )
                df = df.drop(columns=["Longitude", "Latitude"])
                df["date_DD_MM_YYYY"] = df["date_DD_MM_YYYY"].str.replace(
                    ":", "-", regex=False
                )
                df["date_DD_MM_YYYY"] = pd.to_datetime(
                    df["date_DD_MM_YYYY"], format="%d-%m-%Y", errors="coerce"
                )
                df["last_processing_date_DD_MM_YYYY"] = df[
                    "last_processing_date_DD_MM_YYYY"
                ].str.replace(":", "-", regex=False)
                df["last_processing_date_DD_MM_YYYY"] = pd.to_datetime(
                    df["last_processing_date_DD_MM_YYYY"],
                    format="%d-%m-%Y",
                    errors="coerce",
                )
                df["cruise"] = cruise
                df["level"] = level
                df["pi"] = pi
                df["pi_email"] = pi_email
                df.to_csv(outputcsv, index=False)

                if "daily.lev15" in file:
                    self.site_df = pd.concat(
                        [
                            pd.DataFrame(
                                [
                                    [
                                        df.loc[0]["cruise"],
                                        df.loc[0]["aeronet_number"],
                                        "?",
                                        {},
                                    ]
                                ],
                                columns=self.site_cols,
                            ),
                            self.site_df,
                        ],
                        ignore_index=True,
                    )
            except Exception as e:
                with open(log_filename, "a") as log_file:
                    print("\n\n\n Err")
                    print(e)
                    log_file.write(f"failed to create csv {cruise} - File: {file})\n")
                    log_file.write(f"Header: {header}\n")
                    # log_file.write(f"new: {df.columns}\n")
                    log_file.write(f"Error: {e}\n\n")

        for file in files_csv:
            if os.path.isfile(file) and ".csv" not in file:
                # print(file)
                prepare_extract_data(file)

        # Process -
        # Make folder output_fp = os.path.join(".", "src_csvs")
        # Output to os.path.join(output_fp, "{AOD/SDA}_name.split((type)[0]).csv")
        # Save Data That needs to be appended or sent to table
        # Grab PI from header/PI Email from header using readline to preprocess this.

    def setup_header_table(self):
        files = []

        files.append(get_single_match(csv_dir, "*series.lev15"))
        files.append(get_single_match(csv_dir, "*series.lev20"))
        files.append(get_single_match(csv_dir, "*series.ONEILL_15"))
        files.append(get_single_match(csv_dir, "*series.ONEILL_20"))
        files.append(get_single_match(csv_dir, "*daily.lev15"))
        files.append(get_single_match(csv_dir, "*daily.lev20"))
        files.append(get_single_match(csv_dir, "*daily.ONEILL_15"))
        files.append(get_single_match(csv_dir, "*daily.ONEILL_20"))
        files.append(get_single_match(csv_dir, "*all_points.lev10"))
        files.append(get_single_match(csv_dir, "*all_points.lev15"))
        files.append(get_single_match(csv_dir, "*all_points.lev20"))
        files.append(get_single_match(csv_dir, "*all_points.ONEILL_10"))
        files.append(get_single_match(csv_dir, "*all_points.ONEILL_15"))
        files.append(get_single_match(csv_dir, "*all_points.ONEILL_20"))

        def addHeadToDB(file):
            level = 0
            datatype = None
            baseheader_l1 = None
            baseheader_l2 = None
            baseheader_l3 = None

            with open(file, "r") as f:

                freq = None
                match file:
                    case _ if "all_points" in file:
                        freq = "Point"
                    case _ if "series" in file:
                        freq = "Series"
                    case _ if "daily" in file:
                        freq = "Daily"

                lines = f.readlines(806)
                baseheader_l1 = lines[0]
                baseheader_l2 = lines[2]
                header = lines[4]
                cols = header.split(",")
                cols.remove("Latitude")
                cols.remove("Longitude")
                new_cols = ["Coordinates", "Cruise", "Level", "PI", "PI_EMAIL\n"]
                cols.extend(new_cols)
                cols = [element.replace("\n", "") for element in cols]
                header = ",".join(cols)

                if ".lev" in file:
                    datatype = "AOD"
                    level = file.split(".lev")[1]
                else:
                    datatype = "SDA"
                    level = file.split(".ONEILL_")[1]
                f.close()
            try:
                h, created = TableHeader.objects.get_or_create(
                    freq=freq,
                    datatype=datatype,
                    level=level,
                    base_header_l1=baseheader_l1,
                    base_header_l2=baseheader_l2,
                )

                # print(created)
            except:
                pass

        for file in files:
            addHeadToDB(file)

    def handle(self, *args, **kwargs):
        self.setup()
        self.setup_header_table()
        # print("n")
        self.csv()
        self.site_df.to_csv("./src_csvs/sites.csv", index=False)
        # self.push_to_db()
