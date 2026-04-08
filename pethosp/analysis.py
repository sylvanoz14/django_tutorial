"""
Pet Hospital Location Analysis — Scoring Engine

Computes a composite investment attractiveness score for each Victorian LGA
based on four factors:
  - Pet population (30%)
  - Population growth / growth corridor status (25%)
  - Supply gap / distance to nearest pet hospital (25%)
  - Road access (10%)
  - Household income affordability index (10%)
"""
from __future__ import unicode_literals
import math
from decimal import Decimal


# --- Constants (from RSPCA/PIAA 2021 & Animal Medicines Australia 2022) ---
PET_OWNERSHIP_RATE = 0.69       # 69% of Australian households own pets
AVG_PETS_PER_HH = 1.6           # avg pets per pet-owning household

# --- Scoring weights ---
W_PET_POP = 0.30
W_GROWTH = 0.25
W_SUPPLY_GAP = 0.25
W_ROAD = 0.10
W_INCOME = 0.10


def haversine_km(lat1, lon1, lat2, lon2):
    """Return great-circle distance in kilometres between two lat/lng points."""
    R = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _minmax(value, min_val, max_val):
    """Normalise value to 0–100 using min-max scaling."""
    if max_val == min_val:
        return 50.0
    return (value - min_val) / (max_val - min_val) * 100.0


def _supply_gap_score(dist_km):
    """
    Tiered supply gap score based on distance to nearest pet hospital.
    ≥15 km  → 100  (excellent gap, strong unmet demand)
    10–15 km → 75
    5–10 km  → 40
    <5 km    → 10  (existing competition nearby)
    """
    if dist_km >= 15:
        return 100.0
    elif dist_km >= 10:
        return 75.0
    elif dist_km >= 5:
        return 40.0
    else:
        return 10.0


def compute_scores(lgas, hospitals):
    """
    Compute investment scores for all LGAs.

    Args:
        lgas: queryset / list of LGA model instances
        hospitals: queryset / list of PetHospital model instances

    Returns:
        list of dicts, one per LGA, with all score components and composite.
    """
    # Pre-compute per-LGA raw metrics
    raw = []
    for lga in lgas:
        estimated_pets = int(lga.household_count * PET_OWNERSHIP_RATE * AVG_PETS_PER_HH)
        # Nearest hospital
        nearest_h = None
        min_dist = float('inf')
        for h in hospitals:
            d = haversine_km(lga.latitude, lga.longitude, h.latitude, h.longitude)
            if d < min_dist:
                min_dist = d
                nearest_h = h
        raw.append({
            'lga': lga,
            'estimated_pets': estimated_pets,
            'min_dist': min_dist,
            'nearest_hospital': nearest_h,
        })

    # --- Normalise pet population score ---
    pet_counts = [r['estimated_pets'] for r in raw]
    pet_min, pet_max = min(pet_counts), max(pet_counts)

    # --- Normalise growth rate ---
    growth_rates = [float(r['lga'].growth_rate_pct) for r in raw]
    rate_min, rate_max = min(growth_rates), max(growth_rates)

    # --- Normalise income index ---
    incomes = [float(r['lga'].median_income_index) for r in raw]
    inc_min, inc_max = min(incomes), max(incomes)

    results = []
    for r in raw:
        lga = r['lga']

        # 1. Pet population score
        pp_score = _minmax(r['estimated_pets'], pet_min, pet_max)

        # 2. Growth score (0-80 from rate, +20 corridor bonus, capped at 100)
        growth_base = _minmax(float(lga.growth_rate_pct), rate_min, rate_max) * 0.80
        corridor_bonus = 20.0 if lga.is_growth_corridor else 0.0
        g_score = min(growth_base + corridor_bonus, 100.0)

        # 3. Supply gap score
        sg_score = _supply_gap_score(r['min_dist'])

        # 4. Road access score (field is 0-10, scale to 0-100)
        ra_score = float(lga.road_access_score) * 10.0

        # 5. Affordability / income score
        inc_score = _minmax(float(lga.median_income_index), inc_min, inc_max)

        # Weighted composite
        composite = (
            pp_score  * W_PET_POP +
            g_score   * W_GROWTH +
            sg_score  * W_SUPPLY_GAP +
            ra_score  * W_ROAD +
            inc_score * W_INCOME
        )

        results.append({
            'lga': lga,
            'estimated_pets': r['estimated_pets'],
            'min_dist': round(r['min_dist'], 2),
            'nearest_hospital': r['nearest_hospital'],
            'pet_population_score': round(pp_score, 2),
            'growth_score': round(g_score, 2),
            'supply_gap_score': round(sg_score, 2),
            'road_access_score': round(ra_score, 2),
            'affordability_score': round(inc_score, 2),
            'composite_score': round(composite, 2),
        })

    # Rank by composite score descending
    results.sort(key=lambda x: x['composite_score'], reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return results


def generate_report(results, top_n=5):
    """
    Generate a plain-text investment report for the top N LGA candidates.
    Returns the report as a string.
    """
    from datetime import date
    lines = []
    lines.append('=' * 65)
    lines.append('  VICTORIA PET HOSPITAL — INVESTMENT LOCATION REPORT')
    lines.append('  Generated: {}'.format(date.today().strftime('%d %B %Y')))
    lines.append('=' * 65)
    lines.append('')
    lines.append('TOP {} RECOMMENDED LOCATIONS FOR PET HOSPITAL DEVELOPMENT'.format(top_n))
    lines.append('(2,000–5,000 sqm facility, for lease to specialist operator)')
    lines.append('-' * 65)
    lines.append('')

    WHY = {
        # Narrative snippets keyed by rank; overridden per-LGA in loop
    }

    for r in results[:top_n]:
        lga = r['lga']
        rank = r['rank']
        corridor_flag = 'GROWTH CORRIDOR' if lga.is_growth_corridor else 'Established LGA'
        roads = lga.major_roads if lga.major_roads else 'Major arterial access'

        # Build WHY narrative automatically from scores
        why_parts = []
        if r['supply_gap_score'] >= 75:
            why_parts.append(
                'The nearest existing pet hospital is {:.1f} km away, leaving a large '
                'underserved catchment.'.format(r['min_dist'])
            )
        if lga.is_growth_corridor:
            why_parts.append(
                'Designated growth corridor with {:.1f}% annual population growth — '
                'pet ownership demand will increase rapidly.'.format(float(lga.growth_rate_pct))
            )
        else:
            why_parts.append(
                'Established population of {:,} with {:.1f}% annual growth.'.format(
                    lga.population, float(lga.growth_rate_pct)
                )
            )
        if r['pet_population_score'] >= 50:
            why_parts.append(
                'Estimated {:,} pets in catchment provide a strong existing patient base.'.format(
                    r['estimated_pets']
                )
            )
        if float(lga.median_income_index) >= 1.10:
            why_parts.append(
                'Above-average household incomes (index {:.2f}) support willingness to pay '
                'for specialist veterinary care.'.format(float(lga.median_income_index))
            )
        why_text = '  '.join(why_parts) if why_parts else 'Strong combined metrics.'

        lines.append('#{rank}  {name}  —  Composite Score: {score:.1f}/100'.format(
            rank=rank, name=lga.name, score=r['composite_score']
        ))
        lines.append('    Council/LGA:        {}'.format(lga.name))
        lines.append('    Status:             {}'.format(corridor_flag))
        lines.append('    Population:         {:,}  (growth: {:.1f}%/yr)'.format(
            lga.population, float(lga.growth_rate_pct)
        ))
        lines.append('    Households:         {:,}'.format(lga.household_count))
        lines.append('    Est. Pet Population:{:,} pets in LGA catchment'.format(
            r['estimated_pets']
        ))
        nearest_name = r['nearest_hospital'].name if r['nearest_hospital'] else 'N/A'
        lines.append('    Nearest Pet Hosp:   {} ({:.1f} km)'.format(
            nearest_name, r['min_dist']
        ))
        lines.append('    Major Road Access:  {}'.format(roads))
        lines.append('    Income Index:       {:.2f}  (state avg = 1.00)'.format(
            float(lga.median_income_index)
        ))
        lines.append('    --- Score breakdown ---')
        lines.append('      Pet Population:   {:5.1f}/100'.format(r['pet_population_score']))
        lines.append('      Growth:           {:5.1f}/100'.format(r['growth_score']))
        lines.append('      Supply Gap:       {:5.1f}/100'.format(r['supply_gap_score']))
        lines.append('      Road Access:      {:5.1f}/100'.format(r['road_access_score']))
        lines.append('      Affordability:    {:5.1f}/100'.format(r['affordability_score']))
        lines.append('    WHY THIS SITE:')
        lines.append('      ' + why_text)
        lines.append('')

    lines.append('-' * 65)
    lines.append('METHODOLOGY NOTES')
    lines.append('  Pet population: households x 69% ownership x 1.6 pets/household')
    lines.append('  Supply gap: distance to nearest known pet hospital (not vet clinic)')
    lines.append('  Growth data: Plan Melbourne 2017-2050, VIF 2022 projections')
    lines.append('  Weights: Pet Pop 30%, Growth 25%, Supply Gap 25%, Road 10%, Income 10%')
    lines.append('  Data source: ABS 2021 Census, Animal Medicines Australia 2022')
    lines.append('=' * 65)

    return '\n'.join(lines)
