from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Max, Min


class Site(models.Model):
    name = models.CharField(primary_key=True, max_length=255)
    aeronet_number = models.IntegerField(default=0)
    description = models.TextField()
    span_date = ArrayField(
        models.DateField(),
        size=2,
        blank=True,
        null=True,
        help_text="Array holding the span of dates [start_date, end_date]",
    )

    def update_span_date(self):
        # Calculate the span date using related DownloadDaily15 entries
        dates = DownloadDaily15.objects.filter(site=self).aggregate(
            start_date=Min("date"), end_date=Max("date")
        )
        Site.objects.filter(pk=self.pk).update(
            span_date=[dates["start_date"], dates["end_date"]]
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update span_date after the initial save
        self.update_span_date()


class SiteMeasurementsDaily15(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=None)
    filename = models.CharField(max_length=255, default="")
    date = models.DateField(db_index=True)
    time = models.TimeField(db_index=False)
    air_mass = models.FloatField(default=-999.0)
    latlng = gis_models.PointField(default=Point(0, 0))
    aod_340nm = models.FloatField(default=-999.0)
    aod_380nm = models.FloatField(default=-999.0)
    aod_440nm = models.FloatField(default=-999.0)
    aod_500nm = models.FloatField(default=-999.0)
    aod_675nm = models.FloatField(default=-999.0)
    aod_870nm = models.FloatField(default=-999.0)
    aod_1020nm = models.FloatField(default=-999.0)
    aod_1640nm = models.FloatField(default=-999.0)
    water_vapor = models.FloatField(default=-999.0)
    angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    std_340nm = models.FloatField(default=-999.0)
    std_380nm = models.FloatField(default=-999.0)
    std_440nm = models.FloatField(default=-999.0)
    std_500nm = models.FloatField(default=-999.0)
    std_675nm = models.FloatField(default=-999.0)
    std_870nm = models.FloatField(default=-999.0)
    std_1020nm = models.FloatField(default=-999.0)
    std_1640nm = models.FloatField(default=-999.0)
    std_water_vapor = models.FloatField(default=-999.0)
    std_angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    num_observations = models.IntegerField(default=0)
    last_processing_date = models.DateField()
    aeronet_number = models.IntegerField(default=0)
    microtops_number = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the span_date in the related Site instance
        self.site.update_span_date()

    def delete(self, *args, **kwargs):
        site = self.site
        super().delete(*args, **kwargs)
        # Update the span_date in the related Site instance after deletion
        site.update_span_date()


class SiteMeasurementsDaily20(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255, default="")
    date = models.DateField(db_index=True)
    time = models.TimeField(db_index=False)
    air_mass = models.FloatField(default=-999.0)
    latlng = gis_models.PointField(default=Point(0, 0))
    aod_340nm = models.FloatField(default=-999.0)
    aod_380nm = models.FloatField(default=-999.0)
    aod_440nm = models.FloatField(default=-999.0)
    aod_500nm = models.FloatField(default=-999.0)
    aod_675nm = models.FloatField(default=-999.0)
    aod_870nm = models.FloatField(default=-999.0)
    aod_1020nm = models.FloatField(default=-999.0)
    aod_1640nm = models.FloatField(default=-999.0)
    water_vapor = models.FloatField(default=-999.0)
    angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    std_340nm = models.FloatField(default=-999.0)
    std_380nm = models.FloatField(default=-999.0)
    std_440nm = models.FloatField(default=-999.0)
    std_500nm = models.FloatField(default=-999.0)
    std_675nm = models.FloatField(default=-999.0)
    std_870nm = models.FloatField(default=-999.0)
    std_1020nm = models.FloatField(default=-999.0)
    std_1640nm = models.FloatField(default=-999.0)
    std_water_vapor = models.FloatField(default=-999.0)
    std_angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    num_observations = models.IntegerField(default=0)
    last_processing_date = models.DateField()
    aeronet_number = models.IntegerField(default=0)
    microtops_number = models.IntegerField(default=0)


# DOWNLOAD MODELS
class DownloadDaily15(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=None)
    filename = models.CharField(max_length=255, default="")
    date = models.DateField(db_index=True)
    time = models.TimeField(db_index=False)
    air_mass = models.FloatField(default=-999.0)
    latlng = gis_models.PointField(default=Point(0, 0))
    aod_340nm = models.FloatField(default=-999.0)
    aod_380nm = models.FloatField(default=-999.0)
    aod_440nm = models.FloatField(default=-999.0)
    aod_500nm = models.FloatField(default=-999.0)
    aod_675nm = models.FloatField(default=-999.0)
    aod_870nm = models.FloatField(default=-999.0)
    aod_1020nm = models.FloatField(default=-999.0)
    aod_1640nm = models.FloatField(default=-999.0)
    water_vapor = models.FloatField(default=-999.0)
    angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    std_340nm = models.FloatField(default=-999.0)
    std_380nm = models.FloatField(default=-999.0)
    std_440nm = models.FloatField(default=-999.0)
    std_500nm = models.FloatField(default=-999.0)
    std_675nm = models.FloatField(default=-999.0)
    std_870nm = models.FloatField(default=-999.0)
    std_1020nm = models.FloatField(default=-999.0)
    std_1640nm = models.FloatField(default=-999.0)
    std_water_vapor = models.FloatField(default=-999.0)
    std_angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    num_observations = models.IntegerField(default=0)
    last_processing_date = models.DateField()
    aeronet_number = models.IntegerField(default=0)
    microtops_number = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the span_date in the related Site instance
        self.site.update_span_date()

    def delete(self, *args, **kwargs):
        site = self.site
        super().delete(*args, **kwargs)
        # Update the span_date in the related Site instance after deletion
        site.update_span_date()


class DownloadDaily20(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255, default="")
    date = models.DateField(db_index=True)
    time = models.TimeField(db_index=False)
    air_mass = models.FloatField(default=-999.0)
    latlng = gis_models.PointField(default=Point(0, 0))
    aod_340nm = models.FloatField(default=-999.0)
    aod_380nm = models.FloatField(default=-999.0)
    aod_440nm = models.FloatField(default=-999.0)
    aod_500nm = models.FloatField(default=-999.0)
    aod_675nm = models.FloatField(default=-999.0)
    aod_870nm = models.FloatField(default=-999.0)
    aod_1020nm = models.FloatField(default=-999.0)
    aod_1640nm = models.FloatField(default=-999.0)
    water_vapor = models.FloatField(default=-999.0)
    angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    std_340nm = models.FloatField(default=-999.0)
    std_380nm = models.FloatField(default=-999.0)
    std_440nm = models.FloatField(default=-999.0)
    std_500nm = models.FloatField(default=-999.0)
    std_675nm = models.FloatField(default=-999.0)
    std_870nm = models.FloatField(default=-999.0)
    std_1020nm = models.FloatField(default=-999.0)
    std_1640nm = models.FloatField(default=-999.0)
    std_water_vapor = models.FloatField(default=-999.0)
    std_angstrom_exponent_440_870 = models.FloatField(default=-999.0)
    num_observations = models.IntegerField(default=0)
    last_processing_date = models.DateField()
    aeronet_number = models.IntegerField(default=0)
    microtops_number = models.IntegerField(default=0)


# tables for download
class DownloadSeriesAOD(models.Model):
    # Define the date and time fields
    date = models.DateField()
    time = models.TimeField()

    air_mass = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    aod_340nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1020nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1640nm = models.FloatField(null=True, blank=True, default=-999.0)
    water_vapor = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440_870nm_angstrom_exponent = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    std_340nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_380nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_1020nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_1640nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_water_vapor = models.FloatField(null=True, blank=True, default=-999.0)
    std_440_870nm_angstrom_exponent = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    number_of_observations = models.IntegerField(null=True, blank=True)
    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)

    quality = models.FloatField()

    class Meta:
        verbose_name = "Site Measurement Series AOD"
        verbose_name_plural = "Site Measurements Series AOD"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time", "aeronet_number"],
                name="prevent_dupe_series_aod",
            )
        ]


class DownloadDailyAOD(models.Model):
    date = models.DateField()
    time = models.TimeField()

    air_mass = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    aod_340nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1020nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1640nm = models.FloatField(null=True, blank=True, default=-999.0)
    water_vapor = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440_870nm_angstrom_exponent = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    std_340nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_380nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_1020nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_1640nm = models.FloatField(null=True, blank=True, default=-999.0)
    std_water_vapor = models.FloatField(null=True, blank=True, default=-999.0)
    std_440_870nm_angstrom_exponent = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    number_of_observations = models.IntegerField(null=True, blank=True)
    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Site Measurement Daily AOD"
        verbose_name_plural = "Site Measurements Daily AOD"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time", "aeronet_number"], name="prevent_dupe_daily_aod"
            )
        ]


class DownloadPointsAOD(models.Model):
    date = models.DateField()
    time = models.TimeField()

    air_mass = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    aod_340nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1020nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_1640nm = models.FloatField(null=True, blank=True, default=-999.0)
    water_vapor = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440_870nm_angstrom_exponent = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Site Measurement Point AOD"
        verbose_name_plural = "Site Measurements Point AOD"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time", "aeronet_number"], name="prevent_dupe_point_aod"
            )
        ]


# TODO: Add constraints when header is fixed on sda tables
class DownloadPointsSDA(models.Model):
    date = models.DateField()
    time = models.TimeField()

    julian_day = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    total_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_fraction_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    regression_dtau_a = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    rmse_fmf_and_cmf_fractions_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    angstrom_exponent_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    dAE_dln_wavelength_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    ae_fine_mode_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    dAE_dln_wavelength_fine_mode_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    solar_zenith_angle = models.FloatField(null=True, blank=True, default=-999.0)
    air_mass = models.FloatField(null=True, blank=True, default=-999.0)
    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)

    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)
    number_of_wavelengths = models.IntegerField(null=True, blank=True)
    exact_wavelengths_for_input_aod = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name = "Site Measurement Extended AOD"
        verbose_name_plural = "Site Measurements Extended AOD"


class DownloadDailySDA(models.Model):
    date = models.DateField()
    time = models.TimeField()

    julian_day = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    total_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_fraction_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    regression_dtau_a = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    rmse_fmf_and_cmf_fractions_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    angstrom_exponent_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    dAE_dln_wavelength_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    ae_fine_mode_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    dAE_dln_wavelength_fine_mode_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)

    stdev_total_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_fine_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_coarse_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_regression_dtau_a = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_rmse_fine_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_rmse_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_rmse_fmf_and_cmf_fractions_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_angstrom_exponent_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_dae_dln_wavelength_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_ae_fine_mode_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_dae_dln_wavelength_fine_mode_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    number_of_observations = models.IntegerField(null=True, blank=True)
    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)
    number_of_wavelengths = models.IntegerField(null=True, blank=True)
    exact_wavelengths_for_input_aod = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name = "Site Measurement Detailed AOD"
        verbose_name_plural = "Site Measurements Detailed AOD"


class DownloadSeriesSDA(models.Model):
    date = models.DateField()
    time = models.TimeField()

    julian_day = models.FloatField(null=True, blank=True, default=-999.0)
    latitude = models.FloatField(null=True, blank=True, default=-999.0)
    longitude = models.FloatField(null=True, blank=True, default=-999.0)
    total_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    fine_mode_fraction_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    coarse_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    regression_dtau_a = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    rmse_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    rmse_fmf_and_cmf_fractions_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    angstrom_exponent_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    dAE_dln_wavelength_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    ae_fine_mode_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    dAE_dln_wavelength_fine_mode_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    aod_870nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_675nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_440nm = models.FloatField(null=True, blank=True, default=-999.0)
    aod_380nm = models.FloatField(null=True, blank=True, default=-999.0)

    stdev_total_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_fine_mode_aod_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_fine_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_coarse_mode_fraction_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_regression_dtau_a = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_rmse_fine_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_rmse_coarse_mode_aod_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_rmse_fmf_and_cmf_fractions_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_angstrom_exponent_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_dae_dln_wavelength_total_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )
    stdev_ae_fine_mode_500nm = models.FloatField(null=True, blank=True, default=-999.0)
    stdev_dae_dln_wavelength_fine_mode_500nm = models.FloatField(
        null=True, blank=True, default=-999.0
    )

    number_of_observations = models.IntegerField(null=True, blank=True)
    last_processing_date = models.DateField(null=True, blank=True)
    aeronet_number = models.IntegerField(null=True, blank=True)
    microtops_number = models.IntegerField(null=True, blank=True)
    number_of_wavelengths = models.IntegerField(null=True, blank=True)
    exact_wavelengths_for_input_aod = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name = "Oneill Site Measurements with Standard Deviation"
        verbose_name_plural = "Site Measurements Detailed AOD with Standard Deviations"
