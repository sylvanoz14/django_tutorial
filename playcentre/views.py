import json
from django.shortcuts import render
from playcentre.models import Suburb, CompetitorPlayCentre, CandidateSite, SuburbScore
from playcentre.analysis import generate_report, compute_scores


def dashboard(request):
    """Main dashboard: interactive map + ranked table + feasibility report."""
    scores = list(
        SuburbScore.objects.select_related('suburb', 'nearest_competitor', 'best_candidate_site')
                           .order_by('-composite_score')
    )
    competitors = list(CompetitorPlayCentre.objects.filter(is_active=True))
    sites = list(CandidateSite.objects.all())

    suburb_features = []
    for s in scores:
        suburb = s.suburb
        score = float(s.composite_score)
        if score >= 65:
            color = '#27ae60'
        elif score >= 45:
            color = '#f39c12'
        else:
            color = '#e74c3c'

        suburb_features.append({
            'name': suburb.name,
            'lat': float(suburb.latitude),
            'lng': float(suburb.longitude),
            'score': score,
            'rank': s.rank,
            'color': color,
            'est_children': suburb.est_children_under_12,
            'min_dist': float(s.min_distance_to_competitor_km),
            'nearest_competitor': s.nearest_competitor.name if s.nearest_competitor else 'N/A',
            'growth_rate': float(suburb.growth_rate_pct),
            'is_corridor': suburb.is_growth_corridor,
            'population': suburb.population,
            'roads': suburb.major_roads,
            'family_pop_score': float(s.family_population_score),
            'growth_score': float(s.growth_score),
            'supply_gap_score': float(s.supply_gap_score),
            'road_score': float(s.road_access_score),
            'site_score': float(s.site_availability_score),
            'best_site': s.best_candidate_site.name if s.best_candidate_site else None,
        })

    competitor_features = []
    for c in competitors:
        competitor_features.append({
            'name': c.name,
            'suburb': c.suburb.name,
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'type': c.get_format_type_display(),
            'services': c.services,
        })

    site_features = []
    for s in sites:
        site_features.append({
            'name': s.name,
            'address': s.address,
            'suburb': s.suburb.name,
            'lat': float(s.latitude),
            'lng': float(s.longitude),
            'type': s.get_site_type_display(),
            'size_sqm': s.size_sqm,
            'price_or_rent': s.price_or_rent,
            'verified': s.verified,
            'source_url': s.source_url,
        })

    suburbs = list(Suburb.objects.all())
    if suburbs and competitors:
        from collections import defaultdict
        sites_by_suburb = defaultdict(list)
        for s in sites:
            sites_by_suburb[s.suburb_id].append(s)
        results = compute_scores(suburbs, competitors, sites_by_suburb)
        report_text = generate_report(results, top_n=5)
    else:
        report_text = ('No data loaded yet. Run: python manage.py seed_playcentre_data '
                       '&& python manage.py run_playcentre_analysis')

    top5 = scores[:5]

    context = {
        'suburb_features_json': json.dumps(suburb_features),
        'competitor_features_json': json.dumps(competitor_features),
        'site_features_json': json.dumps(site_features),
        'scores': scores,
        'top5': top5,
        'sites': sites,
        'report_text': report_text,
        'total_suburbs': len(scores),
        'total_competitors': len(competitors),
        'total_sites': len(sites),
    }
    return render(request, 'playcentre/dashboard.html', context)
