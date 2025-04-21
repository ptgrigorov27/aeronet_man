import csv
import os

import psycopg2
from django.conf import settings
from django.core.management.base import BaseCommand
from psycopg2 import sql

DB_PARAMS = {
    "dbname": settings.DATABASES["default"]["NAME"],
    "user": settings.DATABASES["default"]["USER"],
    "password": settings.DATABASES["default"]["PASSWORD"],
    "host": settings.DATABASES["default"]["HOST"],
    "port": settings.DATABASES["default"]["PORT"],
}

CSV_FOLDER = "./src_csvs/"


class Command(BaseCommand):
    help = "Bulk import CSV files into PostgreSQL"

    def handle(self, *args, **kwargs):
        self.bulk_load_csvs_from_folder()
        # self.list_table_names()

    def get_db_connection(self):
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            return conn
        except Exception as e:
            self.stdout.write(f"Error connecting to PostgreSQL: {e}")
            return None

    def load_csv_to_postgres(self, csv_file, table_name):
        self.stdout.write(f"Loading {csv_file} into {table_name}...")
        with open(csv_file, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)
            conn = self.get_db_connection()
            if not conn:
                self.stdout.write(
                    f"Could not connect to the database. Skipping {csv_file}"
                )
                return

            cursor = conn.cursor()

            insert_query = sql.SQL(
                "COPY {} ({}) FROM STDIN WITH CSV HEADER DELIMITER ','"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(",").join(map(sql.Identifier, headers)),
            )

            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    cursor.copy_expert(insert_query, f)
                conn.commit()
                self.stdout.write(f"Successfully loaded {csv_file} into {table_name}")
            except Exception as e:
                self.stdout.write(f"Error loading {csv_file} into {table_name}: {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

    def get_db_connection(self):
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            return conn
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None

    def list_table_names(self):
        conn = self.get_db_connection()
        if not conn:
            print("Could not connect to the database.")
            return []

        cursor = conn.cursor()

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE';
        """

        cursor.execute(query)
        tables = cursor.fetchall()

        table_names = [table[0] for table in tables]

        print(table_names)
        cursor.close()
        conn.close()

        return table_names

    def bulk_load_csvs_from_folder(self):
        for filename in os.listdir(CSV_FOLDER):
            if filename.endswith(".csv"):
                csv_file = os.path.join(CSV_FOLDER, filename)
                table_name = filename.replace(".csv", "")
                if "series_SDA" in filename:
                    table_name = "maritimeapp_downloadsdaseries"
                if "all_points_SDA" in filename:
                    table_name = "maritimeapp_downloadsdaap"
                if "daily_SDA" in filename:
                    table_name = "maritimeapp_downloadsdadaily"
                if "series_AOD" in filename:
                    table_name = "maritimeapp_downloadaodseries"
                if "all_points_AOD" in filename:
                    table_name = "maritimeapp_downloadaodap"
                if "daily_AOD" in filename:
                    table_name = "maritimeapp_downloadaoddaily"

                self.load_csv_to_postgres(csv_file, table_name)
        self.load_csv_to_postgres("./src_csvs/sites.csv", "maritimeapp_site")
