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

import pandas as pd
import pyarrow.csv as pv
from django.http import HttpResponse
from django.views.decorators.http import require_GET


def process_file(file_path, start_date, end_date, bounds):
    try:
        with open(file_path, "r", encoding="latin-1") as f:
            header_lines = [next(f) for _ in range(4)]

        f.close()
        df = pd.read_csv(file_path, skiprows=4, encoding="latin-1")
        print(f"reading file {file_path}")
        date_format = "%d:%m:%Y"

        df["Date(dd:mm:yyyy)"] = pd.to_datetime(
            df["Date(dd:mm:yyyy)"], format=date_format, errors="coerce"
        )

        if df["Date(dd:mm:yyyy)"].isna().any():
            print(f"Warning: Some dates in {file_path} could not be parsed")

        start_date = (
            pd.to_datetime(start_date, format="%Y-%m-%d", errors="coerce")
            if start_date
            else None
        )
        end_date = (
            pd.to_datetime(end_date, format="%Y-%m-%d", errors="coerce")
            if end_date
            else None
        )

        if start_date:
            df = df[df["Date(dd:mm:yyyy)"] >= start_date]
        if end_date:
            df = df[df["Date(dd:mm:yyyy)"] <= end_date]

        if bounds["min_lat"]:
            df = df[df["Latitude"] >= float(bounds["min_lat"])]
        if bounds["max_lat"]:
            df = df[df["Latitude"] <= float(bounds["max_lat"])]
        if bounds["min_lng"]:
            df = df[df["Longitude"] >= float(bounds["min_lng"])]
        if bounds["max_lng"]:
            df = df[df["Longitude"] <= float(bounds["max_lng"])]

        print(f"Number of columns after filtering: {df.shape[1]}")

        if df.empty:
            return

        df["Date(dd:mm:yyyy)"] = df["Date(dd:mm:yyyy)"].dt.strftime(date_format)

        with open(file_path, "w") as f:
            f.writelines(header_lines)
            # new filtered data
            df.to_csv(f, index=False, chunksize=100000, header=True)
        f.close()

    # TODO: Log exceptions to log file
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")


import csv
# ----- Download #TODO: Swap to database downlaod instead of file creation
import json
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import pyarrow.csv as pv
from django.contrib.gis.geos import Point, Polygon
from django.http import HttpResponse, JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import *


@csrf_protect
@require_POST
def download_data(request):
    src_dir = r"./src"
    temp_base_dir = r"./temp"
    unique_temp_folder = str(int(time.time())) + "_MAN_DATA"

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

    tar_filename = f"{unique_temp_folder}.tar.gz"
    tar_path = os.path.join(temp_base_dir, tar_filename)
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
                if cur_header is not None:
                    l1_header = cur_header.base_header_l1
                    l2_header = cur_header.base_header_l2
                    header = cur_header.header

                    query = model.objects.filter(cruise__in=sites, level=level_value)

                    if date_filter:
                        query = query.filter(date_filter)

                    if all(value is not None for value in bounds.values()):
                        min_point = Point(bounds["min_lng"], bounds["min_lat"])
                        max_point = Point(bounds["max_lng"], bounds["max_lat"])

                        query = query.filter(
                            coordinates__gte=min_point, coordinates__lte=max_point
                        )

                    if query.exists():
                        file_path = os.path.join(full_temp_path, filename + str(".csv"))

                        with open(file_path, "w", newline="") as file:
                            file.write(f"{l1_header}")
                            file.write(f"{freq},** interpolated 500nm channel **\n")
                            file.write(f"{l2_header}")
                            file.write(f"{header}\n")
                            file.close()

                        queryset_dict = query.values(*fieldnames)
                        df = pd.DataFrame(queryset_dict)

                        with open(file_path, "a", newline="") as file:
                            df.to_csv(
                                file,
                                index=False,
                                chunksize=100000,
                                header=False,
                                encoding="utf-8",
                            )
                        file.close()
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
                "tar",
                "-czvf",
                os.path.join("./temp", tar_path.split("/")[2]),
                "-C",
                full_temp_path,
                ".",
            ],
            check=True,
        )
        print(f"Successfully created {tar_filename} from {directory_to_archive}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the tar file: {e}")
        return JsonResponse(
            {"error": "An error occurred while creating the tar file."}, status=500
        )

    try:
        with open(tar_path, "rb") as f:
            response = HttpResponse(
                f.read(),
                content_type="application/gzip",
                headers={
                    "Content-Disposition": f'attachment; filename="{tar_filename}"'
                },
            )

            return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        if os.path.exists(full_temp_path):
            shutil.rmtree(full_temp_path)
            print(f"Deleted temporary directory {full_temp_path}")
        if os.path.exists(tar_path):
            os.remove(tar_path)
            print(f"Deleted temporary file {tar_path}")

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.contrib.gis.geos import Point, Polygon
from django.db.models import F, Q
##### INTERFACING FRONT-END ####
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.views.decorators.http import require_GET

from .models import Site, SiteMeasurementsDaily15


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
                SiteMeasurementsDaily15.objects.filter(coordinates__within=bbox_polygon)
                .values_list("site_id", flat=True)
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

from .models import Site, SiteMeasurementsDaily15


@require_GET
def get_display_info(request):
    returned = []
    for field in SiteMeasurementsDaily15._meta.get_fields():
        if isinstance(field, models.FloatField):
            returned.append(field.name)
    return JsonResponse({"opts": returned})


from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.point import Point
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from .models import Site, SiteMeasurementsDaily15


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

    queryset = SiteMeasurementsDaily15.objects.filter(site__in=sites)

    if min_lat and min_lng and max_lat and max_lng:
        polygon = Polygon.from_bbox(
            (float(min_lng), float(min_lat), float(max_lng), float(max_lat))
        )
        queryset = queryset.filter(coordinates__within=polygon).distinct()

    if start_date_str and end_date_str:
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        queryset = queryset.filter(date__range=(start_date, end_date))
    elif start_date_str:
        start_date = parse_date(start_date_str)
        queryset = queryset.filter(date__gte=start_date)
    elif end_date_str:
        end_date = parse_date(end_date_str)
        queryset = queryset.filter(date__lte=end_date)

    measurements = list(
        queryset.values(
            "site", "filename", "date", "time", "coordinates", "aeronet_number", aod_key
        )
        # queryset.exclude(**{aod_key: -999}).values(
        #     "site", "filename", "date", "time", "coordinates", "aeronet_number", aod_key
        # )
    )

    for measurement in measurements:
        coordinates = measurement.get("coordinates")
        if isinstance(coordinates, Point):
            measurement["coordinates"] = {"lng": coordinates.x, "lat": coordinates.y}
        else:
            measurement["coordinates"] = None

        measurement["value"] = measurement.pop(aod_key)

    return JsonResponse(measurements, safe=False)
