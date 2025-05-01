## FILE DOWNLOAD ##

# TODO: Display implemention within github repo
"""
How file download works:

Source file contains all data files in a directory structure.

The user selects sites, start date, end date, retrievals, frequency, quality, and bounding box coordinates.

The backend filters the files based on the user's selection - a list of files names are generated based on parameters
and  this list is used to processes the files to filter by date and bounds.

The processed files are then zipped and sent to the user as a stream to be downloaded.
"""
from django.http import JsonResponse
from django.middleware.csrf import get_token


def set_csrf_token(request):
    response = JsonResponse({"detail": "CSRF cookie set"})
    response["X-CSRFToken"] = get_token(request)
    return response


import os
import shutil
import subprocess
import tarfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime
from re import sub

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as csv
from django.contrib.gis.geos import Point
from django.http import HttpResponse
from django.views.decorators.http import require_GET


def point_to_wkt(point):
    if isinstance(point, Point):
        return point.wkt  # Convert to Well-Known Text format
    return point


import csv
# ----- Download #TODO: Swap to database downlaod instead of file creation
import json
import os
import shutil
import subprocess
import tempfile
import time as tme
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time

import geopandas as gpd
import polars as pl
import pyarrow.csv as pv
from django.contrib.gis.geos import Point, Polygon
from django.http import HttpResponse, JsonResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import make_naive
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import *


@csrf_protect
@require_POST
def download_data(request):
    aod_dict = {
        "date_DD_MM_YYYY": "Date(dd:mm:yyyy)",
        "time_HH_MM_SS": "Time(hh:mm:ss)",
        "air_mass": "Air Mass",
        "aod_340nm": "AOD_340nm",
        "aod_380nm": "AOD_380nm",
        "aod_440nm": "AOD_440nm",
        "aod_500nm": "AOD_500nm",
        "aod_675nm": "AOD_675nm",
        "aod_870nm": "AOD_870nm",
        "aod_1020nm": "AOD_1020nm",
        "aod_1640nm": "AOD_1640nm",
        "water_vapor_CM": "Water Vapor(cm)",
        "angstrom_exponent_440_870": "440-870nm_Angstrom_Exponent",
        "std_340nm": "STD_340nm",
        "std_380nm": "STD_380nm",
        "std_440nm": "STD_440nm",
        "std_500nm": "STD_500nm",
        "std_675nm": "STD_675nm",
        "std_870nm": "STD_870nm",
        "std_1020nm": "STD_1020nm",
        "std_1640nm": "STD_1640nm",
        "std_water_vapor_CM": "STD_Water_Vapor(cm)",
        "std_angstrom_exponent_440_870": "STD_440-870nm_Angstrom_Exponent",
        "number_of_observations": "Number_of_Observations",
        "last_processing_date_DD_MM_YYYY": "Last_Processing_Date(dd:mm:yyyy)",
        "aeronet_number": "AERONET_Number",
        "microtops_number": "Microtops_Number",
    }

    sda_dict = {
        "date_DD_MM_YYYY": "Date(dd:mm:yyyy)",
        "time_HH_MM_SS": "Time(hh:mm:ss)",
        "julian_day": "Julian_Day",
        "air_mass": "Air_Mass",
        "total_aod_500nm": "Total_AOD_500nm(tau_a)",
        "fine_mode_aod_500nm": "Fine_Mode_AOD_500nm(tau_f)",
        "coarse_mode_aod_500nm": "Coarse_Mode_AOD_500nm(tau_c)",
        "fine_mode_fraction_500nm": "FineModeFraction_500nm(eta)",
        "coarse_mode_fraction_500nm": "CoarseModeFraction_500nm(1_eta)",
        "regression_dtau_a": "2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)",
        "rmse_fine_mode_aod_500nm": "RMSE_Fine_Mode_AOD_500nm(Dtau_f)",
        "rmse_coarse_mode_aod_500nm": "RMSE_Coarse_Mode_AOD_500nm(Dtau_c)",
        "rmse_fmf_and_cmf_fractions_500nm": "RMSE_FMF_and_CMF_Fractions_500nm(Deta)",
        "angstrom_exponent_total_500nm": "Angstrom_Exponent(AE)_Total_500nm(alpha)",
        "dae_dln_wavelength_total_500nm": "dAE/dln(wavelength)_Total_500nm(alphap)",
        "ae_fine_mode_500nm": "AE_Fine_Mode_500nm(alpha_f)",
        "dae_dln_wavelength_fine_mode_500nm": "dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)",
        "aod_870nm": "870nm_Input_AOD",
        "aod_675nm": "675nm_Input_AOD",
        "aod_500nm": "500nm_Input_AOD",
        "aod_440nm": "440nm_Input_AOD",
        "aod_380nm": "380nm_Input_AOD",
        "stdev_total_aod_500nm": "STDEV-Total_AOD_500nm(tau_a)",
        "stdev_fine_mode_aod_500nm": "STDEV-Fine_Mode_AOD_500nm(tau_f)",
        "stdev_coarse_mode_aod_500nm": "STDEV-Coarse_Mode_AOD_500nm(tau_c)",
        "stdev_fine_mode_fraction_500nm": "STDEV-FineModeFraction_500nm(eta)",
        "stdev_coarse_mode_fraction_500nm": "STDEV-CoarseModeFraction_500nm(1_eta)",
        "stdev_regression_dtau_a": "STDEV-2nd_Order_Reg_Fit_Error_Total_AOD_500nm(regression_dtau_a)",
        "stdev_rmse_fine_mode_aod_500nm": "STDEV-RMSE_Fine_Mode_AOD_500nm(Dtau_f)",
        "stdev_rmse_coarse_mode_aod_500nm": "STDEV-RMSE_Coarse_Mode_AOD_500nm(Dtau_c)",
        "stdev_rmse_fmf_and_cmf_fractions_500nm": "STDEV-RMSE_FMF_and_CMF_Fractions_500nm(Deta)",
        "stdev_angstrom_exponent_total_500nm": "STDEV-Angstrom_Exponent(AE)_Total_500nm(alpha)",
        "stdev_dae_dln_wavelength_total_500nm": "STDEV-dAE/dln(wavelength)_Total_500nm(alphap)",
        "stdev_ae_fine_mode_500nm": "STDEV-AE_Fine_Mode_500nm(alpha_f)",
        "stdev_dae_dln_wavelength_fine_mode_500nm": "STDEV-dAE/dln(wavelength)_Fine_Mode_500nm(alphap_f)",
        "stdev_aod_870nm": "STDEV-870nm_Input_AOD",
        "stdev_aod_675nm": "STDEV-675nm_Input_AOD",
        "stdev_aod_500nm": "STDEV-500nm_Input_AOD",
        "solar_zenith_angle": "Solar_Zenith_Angle",
        "stdev_aod_440nm": "STDEV-440nm_Input_AOD",
        "stdev_aod_380nm": "STDEV-380nm_Input_AOD",
        "number_of_observations": "Number_of_Observations",
        "last_processing_date_DD_MM_YYYY": "Last_Processing_Date(dd:mm:yyyy)",
        "aeronet_number": "AERONET_Number",
        "microtops_number": "Microtops_Number",
    }

    src_dir = r"./src"
    temp_base_dir = r"./temp"
    unique_temp_folder = str(int(tme.time())) + "_MAN_DATA"

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    sites = data.get("sites", [])
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    retrievals = data.get("retrievals", [])
    frequency = data.get("frequency", [])
    quality = data.get("quality", [])
    bounds = {
        "min_lat": data.get("min_lat", None),
        "min_lng": data.get("min_lng", None),
        "max_lat": data.get("max_lat", None),
        "max_lng": data.get("max_lng", None),
    }

    if (start_date is not None) or (end_date is not None):
        init_start_date = datetime(2004, 10, 16).strftime("%Y-%m-%d")
        today_date = datetime.now().date().strftime("%Y-%m-%d")

        if start_date is not None:
            if start_date == init_start_date:
                start_date = None
        if end_date is not None:
            if end_date == today_date:
                end_date = None

    full_temp_path = os.path.join(temp_base_dir, unique_temp_folder)
    os.makedirs(full_temp_path, exist_ok=True)

    # print(sites, retrievals, frequency, quality)

    zip_filename = f"{unique_temp_folder}.zip"
    zip_path = os.path.join(temp_base_dir, zip_filename)
    directory_to_archive = os.path.join(temp_base_dir, unique_temp_folder)

    model = None
    filename = None
    date_filter = Q()

    if start_date:
        date_filter &= Q(date_DD_MM_YYYY__gte=start_date)
    if end_date:
        date_filter &= Q(date_DD_MM_YYYY__lte=end_date)

    for retrieval in retrievals:
        for freq in frequency:
            match (retrieval, freq):
                case ("SDA", "Point"):
                    model = DownloadSDAAP
                    filename = "MAN_DATASET_SDA_POINT"

                case ("SDA", "Series"):
                    model = DownloadSDASeries
                    filename = "MAN_DATASET_SDA_SERIES"

                case ("SDA", "Daily"):
                    model = DownloadSDADaily
                    filename = "MAN_DATASET_SDA_DAILY"

                case ("AOD", "Daily"):
                    model = DownloadAODDaily
                    filename = "MAN_DATASET_AOD_DAILY"

                case ("AOD", "Series"):
                    model = DownloadAODSeries
                    filename = "MAN_DATASET_AOD_SERIES"

                case ("AOD", "Point"):
                    model = DownloadAODAP
                    filename = "MAN_DATASET_AOD_POINT"

            fieldnames = [field.name for field in model._meta.fields]
            fieldnames.pop(0)
            quality_map = {"Level 1.0": 10, "Level 1.5": 15, "Level 2.0": 20}

            temp_fn = filename

            for level in quality:
                level_value = quality_map.get(level)

                filename = temp_fn + str(level_value)

                cur_header = TableHeader.objects.filter(
                    level=quality_map[level], freq=freq, datatype=retrieval
                ).first()

                if "SDA" in retrieval:
                    translated_cols = [
                        sda_dict.get(header, header) for header in fieldnames
                    ]
                else:
                    translated_cols = [
                        aod_dict.get(header, header) for header in fieldnames
                    ]

                if cur_header is not None:
                    l1_header = cur_header.base_header_l1
                    l2_header = cur_header.base_header_l2
                    translated_cols.remove("coordinates_wkt")
                    header = ",".join(translated_cols)
                    # print(header)
                    query = model.objects.filter(cruise__in=sites, level=level_value)
                    if date_filter:
                        query = query.filter(date_filter)

                    if all(value is not None for value in bounds.values()):
                        min_point = Point(bounds["min_lng"], bounds["min_lat"])
                        max_point = Point(bounds["max_lng"], bounds["max_lat"])
                        bbox_polygon = Polygon.from_bbox(
                            (min_point.x, min_point.y, max_point.x, max_point.y)
                        )
                        query = query.filter(coordinates__within=bbox_polygon)
                    if query.exists():
                        file_path = os.path.join(full_temp_path, filename + str(".csv"))

                        with open(file_path, "w", newline="") as file:
                            file.write(f"{l1_header}")
                            file.write(f"{freq},** interpolated 500nm channel **\n")
                            file.write(f"{l2_header}")
                            file.write(f"{header}\n")
                            file.close()

                        queryset_dict = query.values(*fieldnames)

                        df = pl.DataFrame(list(queryset_dict))
                        df = df.drop("coordinates")
                        df.write_csv(
                            open(file_path, "a"),
                            include_header=False,
                            batch_size=20000,
                        )

    try:
        keep_files = ["data_usage_policy.pdf", "data_usage_policy.txt"]
        for policy_file in keep_files:
            src_policy_file = os.path.join(src_dir, policy_file)
            temp_policy_file = os.path.join(full_temp_path, policy_file)

            os.makedirs(os.path.dirname(temp_policy_file), exist_ok=True)

            if os.path.isfile(src_policy_file):
                shutil.copy(src_policy_file, temp_policy_file)
                print(f"Copied {src_policy_file} to {temp_policy_file}")
            else:
                print(f"Source policy file {src_policy_file} does not exist")

        subprocess.run(
            [
                "zip",
                "-r -X",
                # os.path.join("./temp", zip_path.split("/")[2]),
                zip_filename,
                directory_to_archive,
            ],
            check=True,
        )
        print(f"Successfully created {zip_filename} from {directory_to_archive}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the tar file: {e}")
        return JsonResponse(
            {"error": "An error occurred while creating the tar file."}, status=500
        )

    try:
        with open(zip_path, "rb") as f:
            response = HttpResponse(
                f.read(),
                content_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{zip_filename}"'
                },
            )

            return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        if os.path.exists(full_temp_path):
            shutil.rmtree(full_temp_path)
            print(f"Deleted temporary directory {full_temp_path}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"Deleted temporary file {zip_path}")

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.contrib.gis.geos import Point, Polygon
from django.db.models import F, Q
##### INTERFACING FRONT-END ####
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.views.decorators.http import require_GET

from .models import Site


@require_GET
def list_sites(request):
    reading = request.GET.get("reading")
    min_lat = request.GET.get("min_lat")
    min_lng = request.GET.get("min_lng")
    max_lat = request.GET.get("max_lat")
    max_lng = request.GET.get("max_lng")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    queryset = Site.objects.all()

    if min_lat and min_lng and max_lat and max_lng:
        try:
            min_point = Point(float(min_lng), float(min_lat))
            max_point = Point(float(max_lng), float(max_lat))
            bbox_polygon = Polygon.from_bbox(
                (min_point.x, min_point.y, max_point.x, max_point.y)
            )

            # Get all Site IDs that have measurements within the bounding box
            filtered_sites_ids = (
                DownloadAODDaily.objects.filter(
                    coordinates__within=bbox_polygon, level=15
                )
                .values_list("cruise", flat=True)
                .distinct()
            )

            # Debug
            # print(f"list sites: {list(filtered_sites_ids)}")

            if filtered_sites_ids:
                queryset = queryset.filter(name__in=filtered_sites_ids)
            else:
                return JsonResponse([], safe=False)

        except (ValueError, TypeError) as e:
            # invalid coordinates provided
            print(f"Error with bounding box coordinates: {e}")
            return JsonResponse([], safe=False)

    today = now().date()

    if start_date_str:
        start_date = parse_date(start_date_str)
        if start_date:
            if end_date_str:
                end_date = parse_date(end_date_str)
                if end_date:
                    # Filter for sites with span_date that intersects with [start_date, end_date]
                    queryset = queryset.filter(
                        Q(span_date__0__lte=end_date, span_date__1__gte=start_date)
                        | Q(span_date__0__lte=start_date, span_date__1__gte=end_date)
                    ).distinct()
            else:
                # span_date [0, 1] 0 = start_date, 1 = end_date
                # Filter for sites with span_date that intersects with [today, start_date]
                queryset = queryset.filter(
                    Q(span_date__0__lte=today, span_date__1__gte=start_date)
                    | Q(span_date__0__lte=start_date, span_date__1__gte=today)
                ).distinct()
    elif end_date_str:
        end_date = parse_date(end_date_str)
        if end_date:
            queryset = queryset.filter(
                Q(span_date__0__lte=end_date, span_date__1__gte=end_date)
            ).distinct()

    queryset = queryset.annotate(start_date=F("span_date__0")).order_by("start_date")

    sites = queryset.values("name", "span_date")
    return JsonResponse(list(sites), safe=False)


from django.db import models

from .models import DownloadAODDaily, Site


@require_GET
def get_display_info(request):
    returned = []
    for field in DownloadAODDaily._meta.get_fields():
        if isinstance(field, models.FloatField):
            returned.append(field.name)
    return JsonResponse({"opts": returned})


from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.point import Point
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from .models import Site


@csrf_protect
@require_POST
def site_measurements(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    aod_key = data.get("reading")
    min_lat = data.get("min_lat")
    min_lng = data.get("min_lng")
    max_lat = data.get("max_lat")
    max_lng = data.get("max_lng")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    selected_sites = data.get("sites", [])
    site_names = selected_sites if selected_sites else []

    if len(site_names) == 0:
        return JsonResponse({"error": "No sites selected"}, status=400)

    sites = (
        Site.objects.filter(name__in=site_names) if site_names else Site.objects.all()
    )
    queryset = None
    try:

        queryset = DownloadAODDaily.objects.filter(cruise__in=sites, level=15)
        if min_lat and min_lng and max_lat and max_lng:
            polygon = Polygon.from_bbox(
                (float(min_lng), float(min_lat), float(max_lng), float(max_lat))
            )
            queryset = queryset.filter(coordinates__within=polygon).distinct()

        if start_date_str and end_date_str:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            queryset = queryset.filter(date_DD_MM_YYYY__range=(start_date, end_date))
        elif start_date_str:
            start_date = parse_date(start_date_str)
            queryset = queryset.filter(date_DD_MM_YYYY__gte=start_date)
        elif end_date_str:
            end_date = parse_date(end_date_str)
            queryset = queryset.filter(date_DD_MM_YYYY__lte=end_date)

    except Exception as e:
        print(e)
    measurements = list(
        queryset.values(
            "cruise",
            "date_DD_MM_YYYY",
            "time_HH_MM_SS",
            "coordinates",
            "aeronet_number",
            aod_key,
        )
    )

    for measurement in measurements:
        coordinates = measurement.get("coordinates")
        if isinstance(coordinates, Point):
            measurement["coordinates"] = {"lng": coordinates.x, "lat": coordinates.y}
        else:
            measurement["coordinates"] = None

        measurement["value"] = measurement.pop(aod_key)
        measurement["date"] = measurement.pop("date_DD_MM_YYYY")
        measurement["time"] = measurement.pop("time_HH_MM_SS")
        measurement["site"] = measurement.pop("cruise")
    return JsonResponse(measurements, safe=False)
