from __future__ import unicode_literals
from django.db import models


class LGA(models.Model):
    """Local Government Area with demographic and geographic data."""
    name = models.CharField(max_length=100, unique=True)
    population = models.IntegerField(help_text='ABS 2021 Census population')
    household_count = models.IntegerField(help_text='ABS 2021 Census household count')
    median_income_index = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text='1.00 = state average, 1.30 = 30% above average'
    )
    growth_rate_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Annual population growth rate percent'
    )
    is_growth_corridor = models.BooleanField(
        default=False,
        help_text='Designated growth corridor per Plan Melbourne 2017-2050'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    has_freeway_access = models.BooleanField(default=False)
    road_access_score = models.DecimalField(
        max_digits=4, decimal_places=1, default=5.0,
        help_text='0-10 scale: proximity and quality of major road access'
    )
    major_roads = models.CharField(
        max_length=300, blank=True,
        help_text='Comma-separated list of nearby major roads/freeways'
    )

    class Meta:
        verbose_name = 'LGA'
        verbose_name_plural = 'LGAs'
        ordering = ['name']

    def __str__(self):
        return self.name


class PetHospital(models.Model):
    """Known pet hospital / specialist / emergency facility."""
    HOSPITAL_TYPE_CHOICES = [
        ('emergency', 'Emergency & Critical Care'),
        ('specialist', 'Specialist Referral'),
        ('general', 'General Practice Hospital'),
    ]
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    suburb = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    hospital_type = models.CharField(max_length=20, choices=HOSPITAL_TYPE_CHOICES)
    services = models.TextField(
        blank=True,
        help_text='Comma-separated list: Emergency,Surgery,Oncology,...'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '{} ({})'.format(self.name, self.suburb)


class LGAScore(models.Model):
    """Computed investment attractiveness score for each LGA."""
    lga = models.OneToOneField(LGA, on_delete=models.CASCADE, related_name='score')
    estimated_pet_population = models.IntegerField(default=0)
    min_distance_to_hospital_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    nearest_hospital = models.ForeignKey(
        PetHospital, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='nearest_to_lgas'
    )
    # Component scores 0-100
    pet_population_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    growth_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    supply_gap_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    road_access_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    affordability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Weighted composite
    composite_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rank = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-composite_score']

    def __str__(self):
        return '{} — Score: {:.1f}/100 (Rank #{})'.format(
            self.lga.name, float(self.composite_score), self.rank
        )
