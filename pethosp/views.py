from __future__ import unicode_literals
import json
from django.shortcuts import render
from pethosp.models import LGA, PetHospital, LGAScore
from pethosp.analysis import generate_report


def dashboard(request):
    """Main dashboard: interactive map + ranked table + investment report."""
    scores = list(
        LGAScore.objects.select_related('lga', 'nearest_hospital')
                        .order_by('-composite_score')
    )
    hospitals = list(PetHospital.objects.filter(is_active=True))

    # Build JSON for Leaflet map
    lga_features = []
    for s in scores:
        lga = s.lga
        # Color: green >= 65, yellow >= 45, red < 45
        score = float(s.composite_score)
        if score >= 65:
            color = '#27ae60'
        elif score >= 45:
            color = '#f39c12'
        else:
            color = '#e74c3c'

        lga_features.append({
            'name': lga.name,
            'lat': float(lga.latitude),
            'lng': float(lga.longitude),
            'score': score,
            'rank': s.rank,
            'color': color,
            'estimated_pets': s.estimated_pet_population,
            'min_dist': float(s.min_distance_to_hospital_km),
            'nearest_hospital': s.nearest_hospital.name if s.nearest_hospital else 'N/A',
            'growth_rate': float(lga.growth_rate_pct),
            'is_corridor': lga.is_growth_corridor,
            'population': lga.population,
            'income_index': float(lga.median_income_index),
            'roads': lga.major_roads,
            'pet_pop_score': float(s.pet_population_score),
            'growth_score': float(s.growth_score),
            'supply_gap_score': float(s.supply_gap_score),
            'road_score': float(s.road_access_score),
            'afford_score': float(s.affordability_score),
        })

    hospital_features = []
    for h in hospitals:
        hospital_features.append({
            'name': h.name,
            'suburb': h.suburb,
            'lat': float(h.latitude),
            'lng': float(h.longitude),
            'type': h.get_hospital_type_display(),
            'services': h.services,
        })

    # Generate report text for top-5
    from pethosp.analysis import compute_scores
    lgas = list(LGA.objects.all())
    if lgas and hospitals:
        results = compute_scores(lgas, hospitals)
        report_text = generate_report(results, top_n=5)
    else:
        report_text = 'No data loaded yet. Run: python manage.py seed_pethosp_data && python manage.py run_pethosp_analysis'

    top5 = scores[:5]

    context = {
        'lga_features_json': json.dumps(lga_features),
        'hospital_features_json': json.dumps(hospital_features),
        'scores': scores,
        'top5': top5,
        'report_text': report_text,
        'total_lgas': len(scores),
        'total_hospitals': len(hospitals),
    }
    return render(request, 'pethosp/dashboard.html', context)
