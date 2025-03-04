import csv
import datetime
import glob
import os
import re
import subprocess
from datetime import datetime
from functools import partial
from multiprocessing import Pool

import pandas as pd
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from maritimeapp.models import *

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


def process(file, design_type):
    print(f"attempting to add {file}\n")
    try:
        with transaction.atomic():
            with open(file, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                if design_type == "sda_points":
                    process_sda_points(reader)
                elif design_type == "aod_points":
                    process_aod_points(reader)
                elif design_type == "sda_series":
                    process_sda_series(reader)
                elif design_type == "aod_series":
                    process_aod_series(reader)
                elif design_type == "sda_daily":
                    process_sda_daily(reader)
                elif design_type == "aod_daily":
                    process_aod_daily(reader)
                print(f"added {file}\n")
        return True

    except Exception as e:
        with open(log_filename, "a") as log_file:
            log_file.write(
                f"FILE: {file}\n TYPE: {design_type}\n ISSUE: {e}\n DATA:\n{reader}\n\n"
            )
        print(f"did not add {file}\n")
        return False


def bulk_get_or_create(model, data):
    existing_objects = model.objects.filter(
        cruise__in=[item["cruise"] for item in data],
        level__in=[item["level"] for item in data],
        date_DD_MM_YYYY__in=[item["date_DD_MM_YYYY"] for item in data],
        time_HH_MM_SS__in=[item["time_HH_MM_SS"] for item in data],
    )

    print("Number of existing objects:", len(existing_objects))

    existing_keys = set(
        (obj.cruise, obj.level, obj.date_DD_MM_YYYY, obj.time_HH_MM_SS)
        for obj in existing_objects
    )

    new_objects = [
        model(**item)
        for item in data
        if (
            item["cruise"],
            item["level"],
            item["date_DD_MM_YYYY"],
            item["time_HH_MM_SS"],
        )
        not in existing_keys
    ]

    print("Number of new objects to create:", len(new_objects))

    if new_objects:
        model.objects.bulk_create(new_objects)
        print("New objects created successfully")
    else:
        print("No new objects to create")


def process_sda_daily(reader):
    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "julian_day": row["Julian_Day"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "total_aod_500nm": row["Total_AOD_500nm(tau_a)"],
            "fine_mode_aod_500nm": row["Fine_Mode_AOD_500nm(tau_f)"],
            "coarse_mode_aod_500nm": row["Coarse_Mode_AOD_500nm(tau_c)"],
            "fine_mode_fraction_500nm": row["FineModeFraction_500nm(eta)"],
            "coarse_mode_fraction_500nm": row["CoarseModeFraction_500nm(1_eta)"],
            "regression_dtau_a": row[
                "2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)"
            ],
            "rmse_fine_mode_aod_500nm": row["RMSE_Fine_Mode_AOD_500nm(Dtau_f)"],
            "rmse_coarse_mode_aod_500nm": row["RMSE_Coarse_Mode_AOD_500nm(Dtau_c)"],
            "rmse_fmf_and_cmf_fractions_500nm": row[
                "RMSE_FMF_and_CMF_Fractions_500nm(Deta)"
            ],
            "angstrom_exponent_total_500nm": row[
                "Angstrom_Exponent(AE)_Total_500nm(alpha)"
            ],
            "dae_dln_wavelength_total_500nm": row[
                "dAE/dln(wavelength)_Total_500nm(alphap)"
            ],
            "ae_fine_mode_500nm": row["AE_Fine_Mode_500nm(alpha_f)"],
            "dae_dln_wavelength_fine_mode_500nm": row[
                "dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)"
            ],
            "aod_870nm": row["870nm_Input_AOD"],
            "aod_675nm": row["675nm_Input_AOD"],
            "aod_500nm": float(row["500nm_Input_AOD"]),
            "aod_440nm": row["440nm_Input_AOD"],
            "aod_380nm": row["380nm_Input_AOD"],
            "stdev_total_aod_500nm": row["STDEV-Total_AOD_500nm(tau_a)"],
            "stdev_fine_mode_aod_500nm": row["STDEV-Fine_Mode_AOD_500nm(tau_f)"],
            "stdev_coarse_mode_aod_500nm": row["STDEV-Coarse_Mode_AOD_500nm(tau_c)"],
            "stdev_fine_mode_fraction_500nm": row["STDEV-FineModeFraction_500nm(eta)"],
            "stdev_coarse_mode_fraction_500nm": row[
                "STDEV-CoarseModeFraction_500nm(1_eta)"
            ],
            "stdev_regression_dtau_a": row[
                "STDEV-2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)"
            ],
            "stdev_rmse_fine_mode_aod_500nm": row[
                "STDEV-RMSE_Fine_Mode_AOD_500nm(Dtau_f)"
            ],
            "stdev_rmse_coarse_mode_aod_500nm": row[
                "STDEV-RMSE_Coarse_Mode_AOD_500nm(Dtau_c)"
            ],
            "stdev_rmse_fmf_and_cmf_fractions_500nm": row[
                "STDEV-RMSE_FMF_and_CMF_Fractions_500nm(Deta)"
            ],
            "stdev_angstrom_exponent_total_500nm": row[
                "STDEV-Angstrom_Exponent(AE)_Total_500nm(alpha)"
            ],
            "stdev_dae_dln_wavelength_total_500nm": row[
                "STDEV-dAE/dln(wavelength)_Total_500nm(alphap)"
            ],
            "stdev_ae_fine_mode_500nm": row["STDEV-AE_Fine_Mode_500nm(alpha_f)"],
            "stdev_dae_dln_wavelength_fine_mode_500nm": row[
                "STDEV-dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)"
            ],
            "stdev_aod_870nm": row["STDEV-870nm_Input_AOD"],
            "stdev_aod_675nm": row["STDEV-675nm_Input_AOD"],
            "stdev_aod_500nm": row["STDEV-500nm_Input_AOD"],
            "stdev_aod_440nm": row["STDEV-440nm_Input_AOD"],
            "stdev_aod_380nm": row["STDEV-380nm_Input_AOD"],
            "number_of_observations": row["Number_of_Observations"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]
    bulk_get_or_create(DownloadSDADaily, data)


def process_sda_points(reader):
    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "julian_day": row["Julian_Day"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "total_aod_500nm": row["Total_AOD_500nm(tau_a)"],
            "fine_mode_aod_500nm": row["Fine_Mode_AOD_500nm(tau_f)"],
            "coarse_mode_aod_500nm": row["Coarse_Mode_AOD_500nm(tau_c)"],
            "fine_mode_fraction_500nm": row["FineModeFraction_500nm(eta)"],
            "coarse_mode_fraction_500nm": row["CoarseModeFraction_500nm(1_eta)"],
            "regression_dtau_a": row[
                "2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)"
            ],
            "rmse_fine_mode_aod_500nm": row["RMSE_Fine_Mode_AOD_500nm(Dtau_f)"],
            "rmse_coarse_mode_aod_500nm": row["RMSE_Coarse_Mode_AOD_500nm(Dtau_c)"],
            "rmse_fmf_and_cmf_fractions_500nm": row[
                "RMSE_FMF_and_CMF_Fractions_500nm(Deta)"
            ],
            "angstrom_exponent_total_500nm": row[
                "Angstrom_Exponent(AE)_Total_500nm(alpha)"
            ],
            "dae_dln_wavelength_total_500nm": row[
                "dAE/dln(wavelength)_Total_500nm(alphap)"
            ],
            "ae_fine_mode_500nm": row["AE_Fine_Mode_500nm(alpha_f)"],
            "dae_dln_wavelength_fine_mode_500nm": row[
                "dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)"
            ],
            "aod_870nm": row["870nm_Input_AOD"],
            "aod_675nm": row["675nm_Input_AOD"],
            "aod_500nm": float(row["500nm_Input_AOD"]),
            "aod_440nm": row["440nm_Input_AOD"],
            "aod_380nm": row["380nm_Input_AOD"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]

    bulk_get_or_create(DownloadSDAAP, data)


def process_sda_series(reader):
    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "julian_day": row["Julian_Day"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "total_aod_500nm": row["Total_AOD_500nm(tau_a)"],
            "fine_mode_aod_500nm": row["Fine_Mode_AOD_500nm(tau_f)"],
            "coarse_mode_aod_500nm": row["Coarse_Mode_AOD_500nm(tau_c)"],
            "fine_mode_fraction_500nm": row["FineModeFraction_500nm(eta)"],
            "coarse_mode_fraction_500nm": row["CoarseModeFraction_500nm(1_eta)"],
            "regression_dtau_a": row[
                "2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)"
            ],
            "rmse_fine_mode_aod_500nm": row["RMSE_Fine_Mode_AOD_500nm(Dtau_f)"],
            "rmse_coarse_mode_aod_500nm": row["RMSE_Coarse_Mode_AOD_500nm(Dtau_c)"],
            "rmse_fmf_and_cmf_fractions_500nm": row[
                "RMSE_FMF_and_CMF_Fractions_500nm(Deta)"
            ],
            "angstrom_exponent_total_500nm": row[
                "Angstrom_Exponent(AE)_Total_500nm(alpha)"
            ],
            "dae_dln_wavelength_total_500nm": row[
                "dAE/dln(wavelength)_Total_500nm(alphap)"
            ],
            "ae_fine_mode_500nm": row["AE_Fine_Mode_500nm(alpha_f)"],
            "dae_dln_wavelength_fine_mode_500nm": row[
                "dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)"
            ],
            "aod_870nm": row["870nm_Input_AOD"],
            "aod_675nm": row["675nm_Input_AOD"],
            "aod_500nm": float(row["500nm_Input_AOD"]),
            "aod_440nm": row["440nm_Input_AOD"],
            "aod_380nm": row["380nm_Input_AOD"],
            "stdev_total_aod_500nm": row["STDEV-Total_AOD_500nm(tau_a)"],
            "stdev_fine_mode_aod_500nm": row["STDEV-Fine_Mode_AOD_500nm(tau_f)"],
            "stdev_coarse_mode_aod_500nm": row["STDEV-Coarse_Mode_AOD_500nm(tau_c)"],
            "stdev_fine_mode_fraction_500nm": row["STDEV-FineModeFraction_500nm(eta)"],
            "stdev_coarse_mode_fraction_500nm": row[
                "STDEV-CoarseModeFraction_500nm(1_eta)"
            ],
            "stdev_regression_dtau_a": row[
                "STDEV-2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)"
            ],
            "stdev_rmse_fine_mode_aod_500nm": row[
                "STDEV-RMSE_Fine_Mode_AOD_500nm(Dtau_f)"
            ],
            "stdev_rmse_coarse_mode_aod_500nm": row[
                "STDEV-RMSE_Coarse_Mode_AOD_500nm(Dtau_c)"
            ],
            "stdev_rmse_fmf_and_cmf_fractions_500nm": row[
                "STDEV-RMSE_FMF_and_CMF_Fractions_500nm(Deta)"
            ],
            "stdev_angstrom_exponent_total_500nm": row[
                "STDEV-Angstrom_Exponent(AE)_Total_500nm(alpha)"
            ],
            "stdev_dae_dln_wavelength_total_500nm": row[
                "STDEV-dAE/dln(wavelength)_Total_500nm(alphap)"
            ],
            "stdev_ae_fine_mode_500nm": row["STDEV-AE_Fine_Mode_500nm(alpha_f)"],
            "stdev_dae_dln_wavelength_fine_mode_500nm": row[
                "STDEV-dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)"
            ],
            "stdev_aod_870nm": row["STDEV-870nm_Input_AOD"],
            "stdev_aod_675nm": row["STDEV-675nm_Input_AOD"],
            "stdev_aod_500nm": row["STDEV-500nm_Input_AOD"],
            "stdev_aod_440nm": row["STDEV-440nm_Input_AOD"],
            "stdev_aod_380nm": row["STDEV-380nm_Input_AOD"],
            "number_of_observations": row["Number_of_Observations"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]
    bulk_get_or_create(DownloadSDASeries, data)


def process_aod_daily(reader):

    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "air_mass": row["Air Mass"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "aod_340nm": row["AOD_340nm"],
            "aod_380nm": row["AOD_380nm"],
            "aod_440nm": row["AOD_440nm"],
            "aod_500nm": row["AOD_500nm"],
            "aod_675nm": row["AOD_675nm"],
            "aod_870nm": row["AOD_870nm"],
            "aod_1020nm": row["AOD_1020nm"],
            "aod_1640nm": row["AOD_1640nm"],
            "water_vapor_CM": row["Water Vapor(cm)"],
            "angstrom_exponent_440_870": row["440-870nm_Angstrom_Exponent"],
            "std_340nm": row["STD_340nm"],
            "std_380nm": row["STD_380nm"],
            "std_440nm": row["STD_440nm"],
            "std_500nm": row["STD_500nm"],
            "std_675nm": row["STD_675nm"],
            "std_870nm": row["STD_870nm"],
            "std_1020nm": row["STD_1020nm"],
            "std_1640nm": row["STD_1640nm"],
            "std_water_vapor_CM": row["STD_Water_Vapor(cm)"],
            "std_angstrom_exponent_440_870": row["STD_440-870nm_Angstrom_Exponent"],
            "number_of_observations": row["Number_of_Observations"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]
    bulk_get_or_create(DownloadAODDaily, data)


def process_aod_points(reader):
    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "air_mass": row["Air Mass"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "aod_340nm": row["AOD_340nm"],
            "aod_380nm": row["AOD_380nm"],
            "aod_440nm": row["AOD_440nm"],
            "aod_500nm": row["AOD_500nm"],
            "aod_675nm": row["AOD_675nm"],
            "aod_870nm": row["AOD_870nm"],
            "aod_1020nm": row["AOD_1020nm"],
            "aod_1640nm": row["AOD_1640nm"],
            "water_vapor_CM": row["Water Vapor(cm)"],
            "angstrom_exponent_440_870": row["440-870nm_Angstrom_Exponent"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]
    bulk_get_or_create(DownloadAODAP, data)


def process_aod_series(reader):
    data = [
        {
            "date_DD_MM_YYYY": correct_date(row["Date(dd:mm:yyyy)"]),
            "time_HH_MM_SS": row["Time(hh:mm:ss)"],
            "air_mass": row["Air Mass"],
            "coordinates": Point(float(row["Longitude"]), float(row["Latitude"])),
            "aod_340nm": row["AOD_340nm"],
            "aod_380nm": row["AOD_380nm"],
            "aod_440nm": row["AOD_440nm"],
            "aod_500nm": row["AOD_500nm"],
            "aod_675nm": row["AOD_675nm"],
            "aod_870nm": row["AOD_870nm"],
            "aod_1020nm": row["AOD_1020nm"],
            "aod_1640nm": row["AOD_1640nm"],
            "water_vapor_CM": row["Water Vapor(cm)"],
            "angstrom_exponent_440_870": row["440-870nm_Angstrom_Exponent"],
            "std_340nm": row["STD_340nm"],
            "std_380nm": row["STD_380nm"],
            "std_440nm": row["STD_440nm"],
            "std_500nm": row["STD_500nm"],
            "std_675nm": row["STD_675nm"],
            "std_870nm": row["STD_870nm"],
            "std_1020nm": row["STD_1020nm"],
            "std_1640nm": row["STD_1640nm"],
            "std_water_vapor_CM": row["STD_Water_Vapor(cm)"],
            "std_angstrom_exponent_440_870": row["STD_440-870nm_Angstrom_Exponent"],
            "number_of_observations": row["Number_of_Observations"],
            "last_processing_date_DD_MM_YYYY": correct_date(
                row["Last_Processing_Date(dd:mm:yyyy)"]
            ),
            "aeronet_number": row["AERONET_Number"],
            "microtops_number": row["Microtops_Number"],
            "cruise": row["cruise"],
            "level": row["level"],
            "pi": row["pi"],
            "pi_email": row["pi_email"],
        }
        for row in reader
    ]
    bulk_get_or_create(DownloadAODSeries, data)


class Command(BaseCommand):
    help = "Migrate man data tar to database."

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

    def push_to_db(self):
        total_success = 0
        total_bad = 0

        def process_with_tracking(file, design_type):
            nonlocal total_success, total_bad
            process(file, design_type, total_success, total_bad)
            if total_success:
                total_success += 1
            else:
                total_bad += 1

        def process_group(csvs, design_type):
            total_success = 0
            total_bad = 0

            with Pool(processes=2) as pool:
                results = pool.starmap(process, [(file, design_type) for file in csvs])

            for result in results:
                if result:
                    total_success += 1
                else:
                    total_bad += 1
            with open(log_filename, "a") as log_file:

                log_file.write(f"RESULTS:\n {results}\n")
                log_file.write(f"Total readings added: {total_success}")
                log_file.write(f"Total readings not added: {total_bad}")
                return results

        sda_points = os.path.join(".", "src_csvs", "*points_SDA_*.csv")
        csvs = glob.glob(sda_points)
        process_group(csvs, "sda_points")
        aod_points = os.path.join(".", "src_csvs", "*points_AOD_*.csv")
        csvs = glob.glob(aod_points)
        process_group(csvs, "aod_points")
        sda_series = os.path.join(".", "src_csvs", "*series_SDA_*.csv")
        csvs = glob.glob(sda_series)
        process_group(csvs, "sda_series")
        aod_daily = os.path.join(".", "src_csvs", "*daily_AOD_*.csv")
        csvs = glob.glob(aod_daily)
        process_group(csvs, "aod_daily")
        aod_series = os.path.join(".", "src_csvs", "*series_AOD_*.csv")
        csvs = glob.glob(aod_series)
        process_group(csvs, "aod_series")
        sda_daily = os.path.join(".", "src_csvs", "*daily_SDA_*.csv")
        csvs = glob.glob(sda_daily)
        process_group(csvs, "sda_daily")

    def csv(self):
        files_csv = glob.glob("./src_csvs/*")

        def prepare_extract_data(file):
            df = None
            level = None
            pi_info = None
            pi = None
            pi_email = None
            cruise = None
            lines = None
            outputcsv = None
            headers = None

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
                headers = lines[4].strip().split(",")
                reg = re.compile(".*\(int\)")
                bad_cols = list(filter(reg.match, headers))
                if bad_cols:
                    for col in bad_cols:
                        # print(col.replace("(int)", ""))
                        headers[headers.index(col)] = col.replace("(int)", "")
                        # print(headers)

                data = [line.strip().split(",") for line in lines[5:]]
                df = pd.DataFrame(data, columns=headers)
                df["cruise"] = cruise
                df["level"] = level
                df["pi"] = pi
                df["pi_email"] = pi_email
                df.to_csv(outputcsv, index=False)
            except Exception as e:
                with open(log_filename, "a") as log_file:
                    log_file.write(f"failed to create csv {cruise} - File: {file})\n")
                    log_file.write(f"Header: {headers}\n")
                    log_file.write(f"Error: {e}\n\n")

        for file in files_csv:
            if os.path.isfile(file) and ".csv" not in file:
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
        files.append(get_single_match(csv_dir, "*all_points.lev10*"))
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
                header = header.split(",")
                header.remove("Latitude")
                header.remove("Longitude")
                new_cols = ["Coordinates", "Cruise", "Level", "PI", "PI_EMAIL\n"]
                header.extend(new_cols)
                header = [element.replace("\n", "") for element in header]

                header = ",".join(header)

                # print(",".join(lines[1].split(",")[1:]))

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
                    header=header,
                )
            except:
                pass

        for file in files:
            addHeadToDB(file)

    def handle(self, *args, **kwargs):
        self.setup()
        self.setup_header_table()
        self.csv()
        self.push_to_db()
