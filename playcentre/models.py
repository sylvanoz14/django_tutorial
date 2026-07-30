from django.db import models


class Suburb(models.Model):
    """Suburb-level catchment area for a play centre (finer grain than an LGA)."""
    name = models.CharField(max_length=100, unique=True)
    lga_name = models.CharField(max_length=100, help_text='Parent LGA, e.g. City of Wyndham')
    population = models.IntegerField(help_text='Approximate current population')
    household_count = models.IntegerField()
    est_children_under_12 = models.IntegerField(
        help_text='Estimated children aged 0-12, from household count x ABS-pattern child proportion'
    )
    growth_rate_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Annual population growth percent'
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
    major_roads = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        verbose_name = 'Suburb'
        verbose_name_plural = 'Suburbs'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompetitorPlayCentre(models.Model):
    """Existing indoor play centre / entertainment venue for children."""
    FORMAT_CHOICES = [
        ('boutique_inflatable', 'Boutique / Inflatable Play'),
        ('big_box_chain', 'Big-Box Chain Play Centre'),
        ('trampoline_park', 'Trampoline Park'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    suburb = models.ForeignKey(Suburb, on_delete=models.CASCADE, related_name='competitors')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    format_type = models.CharField(max_length=25, choices=FORMAT_CHOICES, default='other')
    services = models.TextField(blank=True, default='', help_text='Comma-separated list of offerings')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '{} ({})'.format(self.name, self.suburb.name)


class CandidateSite(models.Model):
    """A real-estate opportunity: land for sale, warehouse for lease, or future precinct."""
    SITE_TYPE_CHOICES = [
        ('industrial_land_sale', 'Industrial Land For Sale'),
        ('warehouse_lease', 'Warehouse For Lease'),
        ('commercial_dev_site', 'Commercial Development Site'),
        ('future_precinct', 'Future Precinct / Town Centre'),
    ]
    name = models.CharField(max_length=200, help_text='Listing name or precinct name')
    address = models.CharField(max_length=300)
    suburb = models.ForeignKey(Suburb, on_delete=models.CASCADE, related_name='candidate_sites')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    site_type = models.CharField(max_length=25, choices=SITE_TYPE_CHOICES)
    size_sqm = models.IntegerField(null=True, blank=True, help_text='Floor/land size in sqm, if known')
    price_or_rent = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Price guide / rent, often a range or POA'
    )
    zoning_notes = models.CharField(max_length=300, blank=True, default='')
    source_url = models.URLField(max_length=500, blank=True, default='')
    verified = models.BooleanField(
        default=False,
        help_text='True if listing detail was independently confirmed, False if source blocked verification'
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['suburb__name', 'name']

    def __str__(self):
        return '{} — {} ({})'.format(self.name, self.suburb.name, self.get_site_type_display())


class SuburbScore(models.Model):
    """Computed play-centre-site investment attractiveness score for each suburb."""
    suburb = models.OneToOneField(Suburb, on_delete=models.CASCADE, related_name='score')
    min_distance_to_competitor_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    nearest_competitor = models.ForeignKey(
        CompetitorPlayCentre, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='nearest_to_suburbs'
    )
    best_candidate_site = models.ForeignKey(
        CandidateSite, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='best_for_suburbs'
    )
    # Component scores 0-100
    family_population_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    growth_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    supply_gap_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    road_access_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    site_availability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Weighted composite
    composite_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rank = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-composite_score']

    def __str__(self):
        return '{} — Score: {:.1f}/100 (Rank #{})'.format(
            self.suburb.name, float(self.composite_score), self.rank
        )
