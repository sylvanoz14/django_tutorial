"""
Management command: seed_playcentre_data

Loads suburb demographic data, known competitor play centres, and candidate
real-estate sites for the Wyndham growth-corridor play centre feasibility study.
Safe to re-run (uses get_or_create / update pattern).

Usage:
    python manage.py seed_playcentre_data
"""
from django.core.management.base import BaseCommand
from playcentre.models import Suburb, CompetitorPlayCentre, CandidateSite


# ---------------------------------------------------------------------------
# SUBURB DATA — Wyndham growth corridor + immediate competitive catchment.
# Population/household figures are approximate current estimates; growth rates
# reflect known differences between still-developing estates (Mambourin, Manor
# Lakes, Tarneit, Truganina) and more established suburbs (Werribee, Point Cook,
# Hoppers Crossing, Williams Landing). Children-under-12 estimated using an
# ABS-pattern proportion of ~0.65 children/household for new family estates and
# ~0.45 for established suburbs (clearly an estimate, not a Census figure).
#
# Format per row:
#   (name, lga_name, population, households, est_children_u12,
#    growth_rate_pct, is_growth_corridor, lat, lng, has_freeway, road_score, major_roads)
# ---------------------------------------------------------------------------
SUBURB_DATA = [
    ('Mambourin', 'City of Wyndham', 8000, 2800, 1820, 12.0, True,
     -37.8916, 144.5766, False, 6.0, 'Black Forest Rd,Princes Fwy (via Ballan Rd)'),

    ('Manor Lakes', 'City of Wyndham', 18000, 6200, 4030, 6.5, True,
     -37.8747, 144.6132, True, 7.5, 'Ballan Rd,Princes Fwy'),

    ('Wyndham Vale', 'City of Wyndham', 32000, 10800, 7020, 4.5, True,
     -37.8907, 144.6072, True, 8.0, 'Princes Fwy,Ballan Rd,Wyndham Vale Station'),

    ('Werribee', 'City of Wyndham', 51000, 18500, 8325, 2.2, False,
     -37.8964, 144.6620, True, 8.5, 'Princes Fwy,Old Geelong Rd,Werribee Station'),

    ('Werribee South', 'City of Wyndham', 9500, 3400, 1190, 1.5, False,
     -37.9569, 144.6892, False, 4.0, 'Point Wilson Rd'),

    ('Tarneit', 'City of Wyndham', 58000, 19000, 12350, 5.8, True,
     -37.8360, 144.6980, True, 8.0, 'Princes Fwy,Derrimut Rd,Tarneit Station'),

    ('Truganina', 'City of Wyndham', 42000, 14200, 9230, 7.2, True,
     -37.8103, 144.7508, True, 8.5, 'Western Fwy,Palmers Rd,Dohertys Rd'),

    ('Point Cook', 'City of Wyndham', 61000, 20500, 9225, 3.0, False,
     -37.9111, 144.7500, True, 8.0, 'Princes Fwy,Point Cook Rd'),

    ('Hoppers Crossing', 'City of Wyndham', 39000, 13800, 6210, 1.8, False,
     -37.8763, 144.6969, True, 7.5, 'Princes Fwy,Old Geelong Rd,Hoppers Crossing Station'),

    ('Williams Landing', 'City of Wyndham', 12500, 4300, 1935, 4.0, False,
     -37.8797, 144.7523, True, 7.5, 'Princes Fwy,Williams Landing Station'),
]


# ---------------------------------------------------------------------------
# COMPETITOR PLAY CENTRES — existing indoor play/entertainment venues serving
# the Wyndham growth corridor, found via web search July 2026.
#
# Format: (name, address, suburb_name, lat, lng, format_type, services)
# ---------------------------------------------------------------------------
COMPETITOR_DATA = [
    ('BouncyRoos',
     '13 Riverside Ave', 'Werribee',
     -37.9010, 144.6550,
     'boutique_inflatable',
     'Inflatables,Slides,Obstacle Course,Birthday Parties'),

    ('Werribee Indoor Sports',
     'Riverside Ave (Werribee precinct)', 'Werribee',
     -37.9005, 144.6555,
     'other',
     'Inflatables,Nerf,Laser Tag,Private Hire'),

    ('Bumble Beez Indoor Playcentre & Cafe',
     'Watton St area', 'Werribee',
     -37.8960, 144.6600,
     'boutique_inflatable',
     'Indoor Play,Cafe,Birthday Parties'),
]


# ---------------------------------------------------------------------------
# CANDIDATE SITES — real-estate opportunities found via web search July 2026.
# `verified=False` marks listings whose full detail page blocked automated
# retrieval (e.g. 403) - address/type confirmed via search result text only.
#
# Format: (name, address, suburb_name, lat, lng, site_type, size_sqm,
#          price_or_rent, zoning_notes, source_url, verified, notes)
# ---------------------------------------------------------------------------
CANDIDATE_SITE_DATA = [
    ('Industrial/Warehouse Space – 42 Sunline Drive',
     '42 Sunline Drive', 'Truganina',
     -37.8103, 144.7508,
     'warehouse_lease', 5000, 'Contact agent (Cushman & Wakefield)',
     'Industrial zoned; sublease, ready for immediate occupation',
     'https://www.cushmanwakefield.com/en/australia/properties/for-lease/industrialwarehouse/vic/truganina/42-sunline-drive/a8ypy0000006f612ae-l',
     True,
     'Immediate occupation, 5,000 sqm matches top of target size range exactly.'),

    ('Industrial/Warehouse Space – 355 Palmers Rd',
     '355 Palmers Rd', 'Truganina',
     -37.8090, 144.7460,
     'warehouse_lease', 1571, 'Contact agent (Cushman & Wakefield / Central Commercial Group)',
     'Brand-new showroom + office/warehouse, main road exposure, 130m frontage near corner Palmers/Dohertys Rd',
     'https://www.cushmanwakefield.com/en/australia/properties/for-lease/industrialwarehouse/vic/truganina/355-palmers-rd/a8y8b000000gm69eag-l',
     True,
     'Below target size range alone, but high street exposure ideal for a family entertainment venue.'),

    ('Warehouse/Showroom/Retail Space – 14 Tallis Circuit',
     '14 Tallis Circuit', 'Truganina',
     -37.8130, 144.7440,
     'commercial_dev_site', None, 'Contact agent (Raine & Horne Williams Landing)',
     'Marketed explicitly for showroom/retail use, not pure logistics — lower zoning risk',
     'https://www.raineandhorne.com.au/pointcookwilliamslanding/properties/14-tallis-circuit-truganina-3029-victoria',
     True,
     'Marketed for showroom/retail, which reduces re-zoning risk versus pure logistics warehouse stock.'),

    ('Land/Development Site – Lot 3-4, 440 Black Forest Rd / 323 Greens Rd',
     'Lot 3-4, 440 Black Forest Rd / 323 Greens Rd', 'Mambourin',
     -37.8890, 144.5750,
     'industrial_land_sale', None, 'Contact agent (Cushman & Wakefield)',
     'Earmarked industrial per Western Growth Corridor Plan / Mambourin East Precinct Plan',
     'https://www.cushmanwakefield.com/en/australia/properties/for-sale/landdevelopment/victoria/mambourin/lot-3-4-440-black-forest-rd-323-greens-road/a8y5c000000lcupeao-s',
     False,
     'Falls directly inside the marked target zone. Full listing detail (size/price) blocked '
     'automated retrieval (403) — confirm directly with agent before relying on this.'),

    ('Mambourin Town Centre (future precinct)',
     'Mambourin Town Centre precinct', 'Mambourin',
     -37.8930, 144.5820,
     'future_precinct', 25000, 'Not yet available — precinct in planning',
     'Planned mixed retail precinct; may include cinema per public precinct information',
     '',
     True,
     '25,000 sqm retail hub planned (cafes, restaurants, supermarkets, specialty stores, possible '
     'cinema). A co-located or adjacent play centre would benefit from shared footfall once this '
     'opens — worth monitoring as a longer-term anchor opportunity, not an immediate site.'),

    ('Foundation at Truganina (Dexus industrial estate)',
     'Truganina industrial precinct', 'Truganina',
     -37.8050, 144.7550,
     'warehouse_lease', None, 'Contact agent (Dexus)',
     'Premium grade industrial estate; freestanding warehouse & office facilities',
     'https://www.dexus.com/leasing/industrial/properties/foundation-at-truganina.html',
     True,
     'Large-format estate (units generally 11,000-15,000 sqm) — likely oversized unless subdivided.'),
]


class Command(BaseCommand):
    help = 'Seed the database with Wyndham corridor suburb, competitor, and candidate site data'

    def handle(self, *args, **options):
        suburb_count = 0
        suburbs_by_name = {}
        for row in SUBURB_DATA:
            (name, lga_name, population, households, est_children, growth_rate,
             is_corridor, lat, lng, has_freeway, road_score, major_roads) = row
            obj, created = Suburb.objects.get_or_create(
                name=name,
                defaults={
                    'lga_name': lga_name,
                    'population': population,
                    'household_count': households,
                    'est_children_under_12': est_children,
                    'growth_rate_pct': growth_rate,
                    'is_growth_corridor': is_corridor,
                    'latitude': lat,
                    'longitude': lng,
                    'has_freeway_access': has_freeway,
                    'road_access_score': road_score,
                    'major_roads': major_roads,
                }
            )
            if not created:
                obj.lga_name = lga_name
                obj.population = population
                obj.household_count = households
                obj.est_children_under_12 = est_children
                obj.growth_rate_pct = growth_rate
                obj.is_growth_corridor = is_corridor
                obj.latitude = lat
                obj.longitude = lng
                obj.has_freeway_access = has_freeway
                obj.road_access_score = road_score
                obj.major_roads = major_roads
                obj.save()
            suburbs_by_name[name] = obj
            suburb_count += 1

        competitor_count = 0
        for row in COMPETITOR_DATA:
            name, address, suburb_name, lat, lng, format_type, services = row
            suburb = suburbs_by_name[suburb_name]
            obj, created = CompetitorPlayCentre.objects.get_or_create(
                name=name,
                defaults={
                    'address': address,
                    'suburb': suburb,
                    'latitude': lat,
                    'longitude': lng,
                    'format_type': format_type,
                    'services': services,
                    'is_active': True,
                }
            )
            if not created:
                obj.address = address
                obj.suburb = suburb
                obj.latitude = lat
                obj.longitude = lng
                obj.format_type = format_type
                obj.services = services
                obj.save()
            competitor_count += 1

        site_count = 0
        for row in CANDIDATE_SITE_DATA:
            (name, address, suburb_name, lat, lng, site_type, size_sqm,
             price_or_rent, zoning_notes, source_url, verified, notes) = row
            suburb = suburbs_by_name[suburb_name]
            obj, created = CandidateSite.objects.get_or_create(
                name=name,
                defaults={
                    'address': address,
                    'suburb': suburb,
                    'latitude': lat,
                    'longitude': lng,
                    'site_type': site_type,
                    'size_sqm': size_sqm,
                    'price_or_rent': price_or_rent,
                    'zoning_notes': zoning_notes,
                    'source_url': source_url,
                    'verified': verified,
                    'notes': notes,
                }
            )
            if not created:
                obj.address = address
                obj.suburb = suburb
                obj.latitude = lat
                obj.longitude = lng
                obj.site_type = site_type
                obj.size_sqm = size_sqm
                obj.price_or_rent = price_or_rent
                obj.zoning_notes = zoning_notes
                obj.source_url = source_url
                obj.verified = verified
                obj.notes = notes
                obj.save()
            site_count += 1

        self.stdout.write(self.style.SUCCESS(
            'Loaded {} suburbs, {} competitor play centres, {} candidate sites.'.format(
                suburb_count, competitor_count, site_count
            )
        ))
