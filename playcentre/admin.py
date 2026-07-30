from django.contrib import admin
from playcentre.models import Suburb, CompetitorPlayCentre, CandidateSite, SuburbScore


@admin.register(Suburb)
class SuburbAdmin(admin.ModelAdmin):
    list_display = ('name', 'lga_name', 'population', 'est_children_under_12',
                    'growth_rate_pct', 'is_growth_corridor', 'has_freeway_access')
    list_filter = ('lga_name', 'is_growth_corridor', 'has_freeway_access')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(CompetitorPlayCentre)
class CompetitorPlayCentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'suburb', 'format_type', 'is_active')
    list_filter = ('format_type', 'is_active')
    search_fields = ('name', 'address')


@admin.register(CandidateSite)
class CandidateSiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'suburb', 'site_type', 'size_sqm', 'price_or_rent', 'verified')
    list_filter = ('site_type', 'verified', 'suburb')
    search_fields = ('name', 'address')


@admin.register(SuburbScore)
class SuburbScoreAdmin(admin.ModelAdmin):
    list_display = ('suburb', 'rank', 'composite_score', 'min_distance_to_competitor_km',
                    'nearest_competitor', 'best_candidate_site')
    ordering = ('rank',)
    readonly_fields = ('last_calculated',)
