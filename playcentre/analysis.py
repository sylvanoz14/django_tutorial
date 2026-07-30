"""
Play Centre Feasibility — Scoring Engine (Wyndham Growth Corridor)

Computes a composite investment-attractiveness score for each suburb based on:
  - Estimated family population with young children (30%)
  - Population growth / growth corridor status (25%)
  - Supply gap / distance to nearest existing competitor play centre (25%)
  - Road access (10%)
  - Site availability - confirmed candidate real-estate site nearby (10%)
"""
import math


# --- Scoring weights ---
W_FAMILY_POP = 0.30
W_GROWTH = 0.25
W_SUPPLY_GAP = 0.25
W_ROAD = 0.10
W_SITE_AVAIL = 0.10

# Target facility size range for site-availability scoring
TARGET_SIZE_MIN = 1500
TARGET_SIZE_MAX = 6000


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
    """Normalise value to 0-100 using min-max scaling."""
    if max_val == min_val:
        return 50.0
    return (value - min_val) / (max_val - min_val) * 100.0


def _supply_gap_score(dist_km):
    """
    Tiered supply gap score based on distance to nearest competitor play centre.
    >=10 km -> 100 (excellent gap)
    6-10 km -> 75
    3-6 km  -> 40
    <3 km   -> 10 (existing competition nearby)
    """
    if dist_km >= 10:
        return 100.0
    elif dist_km >= 6:
        return 75.0
    elif dist_km >= 3:
        return 40.0
    else:
        return 10.0


def _site_availability_score(candidate_sites):
    """Score based on whether confirmed, appropriately-sized real estate exists."""
    if not candidate_sites:
        return 20.0
    score = 40.0
    if any(s.verified for s in candidate_sites):
        score += 30.0
    if any(
        (s.size_sqm and TARGET_SIZE_MIN <= s.size_sqm <= TARGET_SIZE_MAX)
        or s.site_type in ('commercial_dev_site', 'future_precinct')
        for s in candidate_sites
    ):
        score += 30.0
    return min(score, 100.0)


def _best_candidate_site(candidate_sites):
    """Pick the most promising candidate site for display: prefer verified + on-size."""
    if not candidate_sites:
        return None

    def rank_key(s):
        size_match = 1 if (s.size_sqm and TARGET_SIZE_MIN <= s.size_sqm <= TARGET_SIZE_MAX) else 0
        return (1 if s.verified else 0, size_match)

    return max(candidate_sites, key=rank_key)


def compute_scores(suburbs, competitors, candidate_sites_by_suburb):
    """
    Compute investment scores for all suburbs.

    Args:
        suburbs: queryset / list of Suburb model instances
        competitors: queryset / list of CompetitorPlayCentre model instances
        candidate_sites_by_suburb: dict mapping suburb.id -> list of CandidateSite instances

    Returns:
        list of dicts, one per suburb, with all score components and composite.
    """
    raw = []
    for suburb in suburbs:
        nearest_c = None
        min_dist = float('inf')
        for c in competitors:
            d = haversine_km(suburb.latitude, suburb.longitude, c.latitude, c.longitude)
            if d < min_dist:
                min_dist = d
                nearest_c = c
        raw.append({
            'suburb': suburb,
            'min_dist': min_dist,
            'nearest_competitor': nearest_c,
            'candidate_sites': candidate_sites_by_suburb.get(suburb.id, []),
        })

    # --- Normalise family population score ---
    child_counts = [r['suburb'].est_children_under_12 for r in raw]
    child_min, child_max = min(child_counts), max(child_counts)

    # --- Normalise growth rate ---
    growth_rates = [float(r['suburb'].growth_rate_pct) for r in raw]
    rate_min, rate_max = min(growth_rates), max(growth_rates)

    results = []
    for r in raw:
        suburb = r['suburb']

        # 1. Family population score
        fp_score = _minmax(suburb.est_children_under_12, child_min, child_max)

        # 2. Growth score (0-80 from rate, +20 corridor bonus, capped at 100)
        growth_base = _minmax(float(suburb.growth_rate_pct), rate_min, rate_max) * 0.80
        corridor_bonus = 20.0 if suburb.is_growth_corridor else 0.0
        g_score = min(growth_base + corridor_bonus, 100.0)

        # 3. Supply gap score
        sg_score = _supply_gap_score(r['min_dist'])

        # 4. Road access score (field is 0-10, scale to 0-100)
        ra_score = float(suburb.road_access_score) * 10.0

        # 5. Site availability score
        sa_score = _site_availability_score(r['candidate_sites'])

        composite = (
            fp_score * W_FAMILY_POP +
            g_score  * W_GROWTH +
            sg_score * W_SUPPLY_GAP +
            ra_score * W_ROAD +
            sa_score * W_SITE_AVAIL
        )

        results.append({
            'suburb': suburb,
            'min_dist': round(r['min_dist'], 2),
            'nearest_competitor': r['nearest_competitor'],
            'best_candidate_site': _best_candidate_site(r['candidate_sites']),
            'candidate_sites': r['candidate_sites'],
            'family_population_score': round(fp_score, 2),
            'growth_score': round(g_score, 2),
            'supply_gap_score': round(sg_score, 2),
            'road_access_score': round(ra_score, 2),
            'site_availability_score': round(sa_score, 2),
            'composite_score': round(composite, 2),
        })

    results.sort(key=lambda x: x['composite_score'], reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return results


def generate_report(results, top_n=5):
    """Generate a plain-text feasibility report for the top N suburb candidates."""
    from datetime import date
    lines = []
    lines.append('=' * 68)
    lines.append('  WYNDHAM CORRIDOR — PLAY CENTRE FEASIBILITY REPORT')
    lines.append('  Generated: {}'.format(date.today().strftime('%d %B %Y')))
    lines.append('=' * 68)
    lines.append('')
    lines.append('TOP {} RECOMMENDED SUBURBS FOR BIG-BOX PLAY CENTRE DEVELOPMENT'.format(top_n))
    lines.append('-' * 68)
    lines.append('')

    for r in results[:top_n]:
        suburb = r['suburb']
        rank = r['rank']
        corridor_flag = 'GROWTH CORRIDOR' if suburb.is_growth_corridor else 'Established Suburb'

        lines.append('#{rank}  {name}  —  Composite Score: {score:.1f}/100'.format(
            rank=rank, name=suburb.name, score=r['composite_score']
        ))
        lines.append('    LGA:                {}'.format(suburb.lga_name))
        lines.append('    Status:             {}'.format(corridor_flag))
        lines.append('    Population:         {:,}  (growth: {:.1f}%/yr)'.format(
            suburb.population, float(suburb.growth_rate_pct)
        ))
        lines.append('    Est. Children <12:  {:,}'.format(suburb.est_children_under_12))
        nearest_name = r['nearest_competitor'].name if r['nearest_competitor'] else 'N/A'
        lines.append('    Nearest Competitor: {} ({:.1f} km)'.format(nearest_name, r['min_dist']))
        lines.append('    Major Road Access:  {}'.format(suburb.major_roads))

        best_site = r['best_candidate_site']
        if best_site:
            size_str = '{:,} sqm'.format(best_site.size_sqm) if best_site.size_sqm else 'size TBC'
            verified_str = 'VERIFIED' if best_site.verified else 'UNVERIFIED — confirm with agent'
            lines.append('    Best Candidate Site: {} — {} ({}) [{}]'.format(
                best_site.name, best_site.address, size_str, verified_str
            ))
            if best_site.source_url:
                lines.append('       Source: {}'.format(best_site.source_url))
        else:
            lines.append('    Best Candidate Site: none identified yet in this suburb')

        lines.append('    --- Score breakdown ---')
        lines.append('      Family Population: {:5.1f}/100'.format(r['family_population_score']))
        lines.append('      Growth:            {:5.1f}/100'.format(r['growth_score']))
        lines.append('      Supply Gap:        {:5.1f}/100'.format(r['supply_gap_score']))
        lines.append('      Road Access:       {:5.1f}/100'.format(r['road_access_score']))
        lines.append('      Site Availability: {:5.1f}/100'.format(r['site_availability_score']))
        lines.append('')

    lines.append('-' * 68)
    lines.append('ALL CANDIDATE SITES FOUND (across all suburbs, for reference)')
    lines.append('-' * 68)
    seen_sites = set()
    for r in results:
        for site in r['candidate_sites']:
            if site.id in seen_sites:
                continue
            seen_sites.add(site.id)
            size_str = '{:,} sqm'.format(site.size_sqm) if site.size_sqm else 'size TBC'
            verified_str = 'VERIFIED' if site.verified else 'UNVERIFIED'
            lines.append('  [{}] {} — {} ({}, {}) [{}]'.format(
                site.get_site_type_display(), site.name, site.address, size_str,
                site.price_or_rent, verified_str
            ))
            if site.zoning_notes:
                lines.append('       Zoning: {}'.format(site.zoning_notes))
            if site.notes:
                lines.append('       Note: {}'.format(site.notes))
            if site.source_url:
                lines.append('       Source: {}'.format(site.source_url))
    lines.append('')

    lines.append('-' * 68)
    lines.append('ZONING & APPROVALS NOTE')
    lines.append('  Wyndham City Council requires a Town Planning permit for any')
    lines.append('  "Place of Assembly" (land where people congregate for entertainment,')
    lines.append('  meetings, or cultural activities) — a play centre falls under this')
    lines.append('  definition regardless of underlying zone. Budget time/cost for this')
    lines.append('  approval step; industrial-zoned sites may need an additional permit')
    lines.append('  for change of use from warehouse/logistics to indoor recreation.')
    lines.append('')

    lines.append('-' * 68)
    lines.append('METHODOLOGY NOTES')
    lines.append('  Children under 12 estimated from household count x ABS-pattern child')
    lines.append('  proportion (~0.65/household for new family estates, ~0.45 for')
    lines.append('  established suburbs) - an estimate, not a Census figure.')
    lines.append('  Supply gap: distance to nearest known competitor play centre.')
    lines.append('  Weights: Family Pop 30%, Growth 25%, Supply Gap 25%, Road 10%,')
    lines.append('  Site Availability 10%.')
    lines.append('  Competitor & listing data: web search, July 2026 - see source URLs above.')
    lines.append('=' * 68)

    return '\n'.join(lines)
