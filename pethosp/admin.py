from __future__ import unicode_literals
from django.contrib import admin
from pethosp.models import LGA, PetHospital, LGAScore


@admin.register(LGA)
class LGAAdmin(admin.ModelAdmin):
    list_display = ('name', 'population', 'household_count', 'growth_rate_pct',
                    'is_growth_corridor', 'has_freeway_access')
    list_filter = ('is_growth_corridor', 'has_freeway_access')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(PetHospital)
class PetHospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'suburb', 'hospital_type', 'is_active')
    list_filter = ('hospital_type', 'is_active')
    search_fields = ('name', 'suburb')


@admin.register(LGAScore)
class LGAScoreAdmin(admin.ModelAdmin):
    list_display = ('lga', 'rank', 'composite_score', 'estimated_pet_population',
                    'min_distance_to_hospital_km', 'nearest_hospital')
    ordering = ('rank',)
    readonly_fields = ('last_calculated',)
