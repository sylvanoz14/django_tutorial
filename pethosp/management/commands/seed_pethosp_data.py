"""
Management command: seed_pethosp_data

Loads all Victorian LGA demographic data and known pet hospital locations
into the database. Safe to re-run (uses get_or_create).

Usage:
    python manage.py seed_pethosp_data
"""
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from pethosp.models import LGA, PetHospital


# ---------------------------------------------------------------------------
# LGA DATA — sourced from ABS 2021 Census, Plan Melbourne 2017-2050,
#            VIF 2022 (Victoria in Future) projections.
#
# Format per row:
#   (name, population, households, income_index, growth_rate_pct,
#    is_growth_corridor, lat, lng, has_freeway, road_score, major_roads)
# ---------------------------------------------------------------------------
LGA_DATA = [
    # ---- INNER MELBOURNE ----
    ('City of Melbourne', 178000, 91000, 1.20, 2.8, False,
     -37.8136, 144.9631, True, 10.0, 'CityLink,West Gate Fwy,Eastern Fwy'),
    ('City of Yarra', 95000, 46000, 1.25, 2.5, False,
     -37.8010, 144.9928, True, 9.0, 'Eastern Fwy,Hoddle St'),
    ('City of Port Phillip', 114000, 56000, 1.30, 2.2, False,
     -37.8672, 144.9627, True, 9.0, 'West Gate Fwy,Nepean Hwy'),
    ('City of Stonnington', 116000, 54000, 1.45, 1.8, False,
     -37.8573, 145.0192, True, 9.0, 'Monash Fwy,Nepean Hwy'),
    ('City of Boroondara', 177000, 71000, 1.55, 1.2, False,
     -37.8219, 145.0654, True, 9.0, 'Eastern Fwy,Monash Fwy'),
    ('City of Glen Eira', 153000, 59000, 1.20, 1.5, False,
     -37.8968, 145.0256, True, 8.0, 'Nepean Hwy,Princes Hwy'),
    ('City of Bayside', 105000, 40000, 1.50, 1.0, False,
     -37.9241, 145.0234, True, 8.0, 'Nepean Hwy,South Rd'),
    ('City of Kingston', 167000, 62000, 1.10, 1.8, False,
     -37.9814, 145.0758, True, 8.0, 'Monash Fwy,Nepean Hwy,Eastlink'),
    ('City of Monash', 202000, 74000, 1.15, 1.5, False,
     -37.8759, 145.1213, True, 8.0, 'Monash Fwy,Eastlink'),
    ('City of Whitehorse', 179000, 67000, 1.20, 1.3, False,
     -37.8220, 145.1697, True, 8.0, 'Eastern Fwy,Eastlink'),
    ('City of Manningham', 126000, 46000, 1.25, 1.2, False,
     -37.7673, 145.1718, True, 7.0, 'Eastern Fwy,Eastlink'),
    ('City of Darebin', 157000, 65000, 1.00, 2.0, False,
     -37.7469, 145.0079, True, 8.0, 'Metropolitan Ring Rd,Hume Fwy'),
    ('City of Moreland', 185000, 77000, 1.05, 2.2, False,
     -37.7341, 144.9619, True, 8.0, 'Metropolitan Ring Rd,Sydney Rd'),
    ('City of Brimbank', 202000, 70000, 0.85, 1.8, False,
     -37.7329, 144.8264, True, 8.0, 'Western Ring Rd,Western Fwy'),
    ('City of Moonee Valley', 126000, 51000, 1.10, 1.8, False,
     -37.7445, 144.9155, True, 9.0, 'CityLink,Western Ring Rd,Tullamarine Fwy'),
    ('City of Maribyrnong', 90000, 38000, 1.00, 2.5, False,
     -37.7940, 144.8807, True, 8.0, 'Western Ring Rd,West Gate Fwy'),
    ('City of Hobsons Bay', 96000, 37000, 1.00, 1.5, False,
     -37.8669, 144.8699, True, 8.0, 'West Gate Fwy,Princes Fwy'),
    # ---- MIDDLE RING ----
    ('City of Knox', 165000, 59000, 1.10, 1.2, False,
     -37.8878, 145.2424, True, 8.0, 'Eastlink,Burwood Hwy'),
    ('City of Maroondah', 117000, 44000, 1.05, 1.5, False,
     -37.8085, 145.2918, True, 7.0, 'Eastlink,Maroondah Hwy'),
    ('Shire of Yarra Ranges', 158000, 57000, 1.00, 1.3, False,
     -37.7576, 145.5285, False, 5.0, 'Maroondah Hwy,Warburton Hwy'),
    ('City of Banyule', 130000, 48000, 1.15, 1.2, False,
     -37.7067, 145.0830, True, 7.0, 'Metropolitan Ring Rd,Greensborough Hwy'),
    # ---- OUTER / GROWTH CORRIDORS ----
    ('City of Wyndham', 300000, 99000, 0.88, 5.5, True,
     -37.8978, 144.5840, True, 9.0, 'Princes Fwy,Western Ring Rd,Geelong Rd'),
    ('City of Melton', 185000, 62000, 0.88, 5.8, True,
     -37.6853, 144.5796, True, 8.0, 'Western Fwy,Metropolitan Ring Rd'),
    ('City of Whittlesea', 235000, 79000, 0.90, 4.2, True,
     -37.5435, 145.0178, True, 8.0, 'Hume Fwy,Metropolitan Ring Rd'),
    ('City of Hume', 230000, 77000, 0.90, 3.8, True,
     -37.5916, 144.9519, True, 9.0, 'Tullamarine Fwy,Hume Fwy,Western Ring Rd'),
    ('City of Casey', 390000, 131000, 0.95, 3.5, True,
     -38.0539, 145.2976, True, 8.0, 'Monash Fwy,Eastlink,South Gippsland Hwy'),
    ('Shire of Cardinia', 112000, 38000, 0.95, 4.8, True,
     -38.0351, 145.4845, True, 7.0, 'South Gippsland Hwy,Princes Fwy'),
    ('Shire of Mitchell', 48000, 16000, 0.90, 4.5, True,
     -37.1339, 145.0072, True, 7.0, 'Hume Fwy'),
    ('Shire of Moorabool', 38000, 13000, 0.92, 3.5, True,
     -37.7303, 144.2741, True, 6.0, 'Western Fwy'),
    ('Shire of Baw Baw', 57000, 21500, 0.92, 2.8, True,
     -38.0035, 145.9672, True, 6.0, 'Princes Fwy'),
    # ---- SOUTHEAST ----
    ('City of Greater Dandenong', 168000, 57000, 0.80, 1.8, False,
     -37.9878, 145.2151, True, 8.0, 'Monash Fwy,Eastlink,Princes Hwy'),
    ('City of Frankston', 142000, 54000, 0.90, 1.5, False,
     -38.1467, 145.1272, True, 7.0, 'Mornington Peninsula Fwy,Nepean Hwy'),
    ('Shire of Mornington Peninsula', 167000, 66000, 1.05, 1.8, False,
     -38.2319, 145.0458, False, 5.0, 'Mornington Peninsula Fwy,Nepean Hwy'),
    # ---- REGIONAL VICTORIA ----
    ('City of Greater Geelong', 265000, 107000, 0.95, 2.8, False,
     -38.1499, 144.3617, True, 8.0, 'Princes Fwy (Geelong),Geelong Ring Rd'),
    ('City of Ballarat', 115000, 46000, 0.92, 1.8, False,
     -37.5622, 143.8503, True, 7.0, 'Western Fwy,Midland Hwy'),
    ('City of Greater Bendigo', 120000, 50000, 0.92, 1.8, False,
     -36.7570, 144.2794, True, 7.0, 'Calder Fwy,Loddon Valley Hwy'),
    ('City of Latrobe', 76000, 31000, 0.88, 1.0, False,
     -38.2218, 146.4045, True, 6.0, 'Princes Fwy (Gippsland)'),
    ('Shire of Macedon Ranges', 52000, 19000, 1.10, 2.5, False,
     -37.3576, 144.5547, True, 6.0, 'Calder Fwy,Hume Fwy'),
    ('City of Greater Shepparton', 67000, 27000, 0.82, 0.8, False,
     -36.3800, 145.3990, True, 6.0, 'Goulburn Valley Hwy'),
    ('City of Wodonga', 41000, 16500, 0.92, 1.5, False,
     -36.1215, 146.8879, True, 6.0, 'Hume Fwy'),
    ('City of Wangaratta', 30000, 12500, 0.88, 0.8, False,
     -36.3578, 146.3124, True, 6.0, 'Hume Fwy'),
    ('City of Mildura', 57000, 23000, 0.85, 1.0, False,
     -34.1851, 142.1620, True, 5.0, 'Calder Hwy,Sturt Hwy'),
    ('City of Warrnambool', 35000, 14500, 0.90, 1.2, False,
     -38.3837, 142.4864, True, 6.0, 'Princes Hwy (Western)'),
    ('Shire of Nillumbik', 65000, 23000, 1.25, 1.0, False,
     -37.6369, 145.2003, False, 5.0, 'Greensborough Hwy,Eltham-Yarra Glen Rd'),
    ('Shire of Bass Coast', 36000, 15500, 0.95, 2.2, False,
     -38.5497, 145.6065, False, 4.0, 'South Gippsland Hwy'),
    ('Shire of East Gippsland', 46000, 19500, 0.85, 0.8, False,
     -37.5780, 148.0045, False, 3.0, 'Princes Hwy (Gippsland)'),
    ('Shire of Wellington', 44000, 18500, 0.88, 0.5, False,
     -37.9556, 147.1139, True, 5.0, 'Princes Fwy (Gippsland)'),
    ('Shire of South Gippsland', 31000, 13000, 0.90, 0.8, False,
     -38.6667, 146.1667, False, 3.0, 'South Gippsland Hwy'),
    ('Shire of Surf Coast', 34000, 13000, 1.15, 2.5, False,
     -38.3332, 144.1023, False, 4.0, 'Surf Coast Hwy'),
    ('Shire of Colac-Otway', 22000, 8500, 0.85, 0.8, False,
     -38.3404, 143.5895, False, 3.0, 'Princes Hwy (Western)'),
    ('Shire of Golden Plains', 24000, 8800, 0.90, 2.8, False,
     -37.9987, 143.9198, False, 4.0, 'Midland Hwy'),
    ('Shire of Pyrenees', 7500, 3100, 0.82, 0.3, False,
     -37.3157, 143.4088, False, 2.0, 'Western Hwy'),
    ('Shire of Hepburn', 15500, 6400, 0.95, 0.8, False,
     -37.3480, 144.2780, False, 3.0, 'Midland Hwy'),
    ('Shire of Mount Alexander', 20000, 8500, 0.98, 1.2, False,
     -37.0608, 144.2154, False, 3.0, 'Calder Hwy'),
    ('Shire of Loddon', 8000, 3400, 0.78, 0.2, False,
     -36.6046, 143.9741, False, 2.0, 'Calder Hwy'),
    ('Shire of Campaspe', 38000, 15500, 0.85, 0.5, False,
     -36.3695, 144.9041, True, 5.0, 'Goulburn Valley Hwy'),
    ('Shire of Moira', 30000, 12500, 0.82, 0.5, False,
     -36.0750, 145.6660, False, 3.0, 'Goulburn Valley Hwy'),
    ('Shire of Strathbogie', 10500, 4200, 0.82, 0.3, False,
     -36.8620, 145.7438, False, 2.0, 'Hume Fwy'),
    ('Shire of Murrindindi', 14000, 5500, 0.88, 1.0, False,
     -37.3381, 145.5685, False, 3.0, 'Maroondah Hwy'),
    ('Shire of Mansfield', 8500, 3600, 0.90, 1.2, False,
     -37.0548, 146.0837, False, 3.0, 'Maroondah Hwy'),
    ('Shire of Indigo', 16000, 6700, 0.88, 0.8, False,
     -36.3577, 146.9299, False, 3.0, 'Hume Fwy'),
    ('Shire of Alpine', 12500, 5200, 0.90, 0.5, False,
     -36.8551, 147.1390, False, 3.0, 'Great Alpine Rd'),
    ('Shire of Benalla', 14000, 6000, 0.82, 0.3, False,
     -36.5538, 145.9831, True, 5.0, 'Hume Fwy'),
    ('Shire of Towong', 5500, 2300, 0.80, 0.2, False,
     -36.4782, 147.6994, False, 1.0, 'Omeo Hwy'),
    ('Shire of Yarriambiack', 6500, 2900, 0.75, -0.5, False,
     -36.2019, 142.4596, False, 1.0, 'Wimmera Hwy'),
    ('Shire of Hindmarsh', 5500, 2400, 0.75, -0.5, False,
     -35.8683, 141.8671, False, 1.0, 'Western Hwy'),
    ('Rural City of Horsham', 20000, 8500, 0.85, 0.5, False,
     -36.7127, 142.2025, True, 5.0, 'Western Hwy'),
    ('Shire of West Wimmera', 4200, 1900, 0.72, -0.8, False,
     -36.7197, 141.5432, False, 1.0, 'Wimmera Hwy'),
    ('Shire of Northern Grampians', 11000, 4600, 0.78, -0.2, False,
     -37.0617, 142.7753, False, 2.0, 'Western Hwy'),
    ('Shire of Ararat', 11500, 4900, 0.80, 0.2, False,
     -37.2837, 142.9178, False, 3.0, 'Western Hwy'),
    ('Shire of Corangamite', 19000, 7800, 0.85, 0.5, False,
     -38.2019, 143.3000, False, 3.0, 'Princes Hwy (Western)'),
    ('Shire of Moyne', 17000, 7200, 0.88, 0.8, False,
     -38.3588, 142.5131, False, 3.0, 'Princes Hwy (Western)'),
    ('Shire of Glenelg', 20000, 8400, 0.85, 0.3, False,
     -37.8321, 141.4890, False, 3.0, 'Princes Hwy (Western)'),
    ('Shire of Southern Grampians', 16000, 6900, 0.85, 0.2, False,
     -37.6431, 142.0172, False, 3.0, 'Hamilton Hwy'),
    ('Shire of Swan Hill', 21000, 8500, 0.80, 0.3, False,
     -35.3378, 143.5542, True, 4.0, 'Calder Hwy'),
    ('Shire of Buloke', 6000, 2600, 0.75, -0.5, False,
     -36.3016, 143.0929, False, 1.0, 'Calder Hwy'),
    ('Shire of Gannawarra', 10500, 4500, 0.78, -0.3, False,
     -35.7109, 143.9046, False, 2.0, 'Murray Valley Hwy'),
    ('Shire of Central Goldfields', 13500, 5800, 0.80, 0.5, False,
     -37.0505, 143.9001, False, 3.0, 'Calder Hwy'),
    ('Borough of Queenscliffe', 3500, 1600, 1.10, 0.5, False,
     -38.2672, 144.6623, False, 2.0, 'Bellarine Hwy'),
]


# ---------------------------------------------------------------------------
# KNOWN PET HOSPITALS — 15 major emergency/specialist facilities in Victoria
# (excludes standard vet clinics; includes 24-hr emergency and specialist refs)
#
# Format: (name, address, suburb, lat, lng, hospital_type, services)
# ---------------------------------------------------------------------------
PET_HOSPITALS_DATA = [
    ('Lort Smith Animal Hospital',
     '24 Villiers St', 'North Melbourne',
     -37.7969, 144.9464,
     'general',
     'Emergency,Surgery,Dental,General Practice,Rehabilitation,Oncology'),

    ('Animal Referral Hospital (ARH) Essendon',
     '5 Fastline Rd', 'Tullamarine',
     -37.7133, 144.8897,
     'specialist',
     'Surgery,Neurology,Cardiology,Oncology,Internal Medicine,Emergency,ICU'),

    ('University of Melbourne Veterinary Teaching Hospital',
     'Corner Flemington Rd & Park Drive', 'Parkville',
     -37.7963, 144.9566,
     'specialist',
     'Surgery,Internal Medicine,Oncology,Cardiology,Neurology,Ophthalmology,Emergency'),

    ('Veterinary Specialist Services (VSS) Essendon',
     '1/315 Pascoe Vale Rd', 'Essendon',
     -37.7478, 144.9189,
     'specialist',
     'Surgery,Oncology,Cardiology,Neurology,Dermatology,Internal Medicine'),

    ('Animal Emergency Centre - Ascot Vale',
     '267 Ascot Vale Rd', 'Ascot Vale',
     -37.7833, 144.9144,
     'emergency',
     'Emergency,Critical Care,Surgery,ICU'),

    ('Animal Emergency Centre - Malvern East',
     '32 Waverley Rd', 'Malvern East',
     -37.8709, 145.0574,
     'emergency',
     'Emergency,Critical Care,ICU'),

    ('Melbourne Veterinary Specialist Centre (MVSC)',
     '1 Homeleigh Rd', 'Moorabbin',
     -37.9453, 145.0645,
     'specialist',
     'Surgery,Internal Medicine,Oncology,Ophthalmology,Dermatology'),

    ('Animal Emergency Service (AES) Glen Waverley',
     '1/233 Springvale Rd', 'Glen Waverley',
     -37.8787, 145.1629,
     'emergency',
     'Emergency,Critical Care,Surgery,ICU'),

    ('Pet Emergency - Bundoora',
     '904 Plenty Rd', 'Bundoora',
     -37.6968, 145.0565,
     'emergency',
     'Emergency,Surgery,Critical Care'),

    ('Casey Animal Emergency Centre',
     '36 Patterdale Way', 'Narre Warren',
     -38.0272, 145.2929,
     'emergency',
     'Emergency,Critical Care'),

    ('Southern Animal Emergency (SAE) Seaford',
     '5 Hartnett Ct', 'Seaford',
     -38.1015, 145.1284,
     'emergency',
     'Emergency,Surgery,Critical Care'),

    ('Animal Emergency Service (AES) Frankston',
     '9/51 Cranbourne Rd', 'Frankston',
     -38.1387, 145.1227,
     'emergency',
     'Emergency,Critical Care'),

    ('Geelong Animal Emergency',
     '185 Ryrie St', 'Geelong',
     -38.1438, 144.3603,
     'emergency',
     'Emergency,Critical Care,Surgery'),

    ('Ballarat Veterinary Practice After Hours',
     '108 Drummond St South', 'Ballarat',
     -37.5702, 143.8659,
     'general',
     'Emergency,General Practice'),

    ('University of Melbourne Veterinary Hospital (Werribee)',
     'K Rd', 'Werribee',
     -37.9022, 144.6681,
     'specialist',
     'Surgery,Internal Medicine,Oncology,Cardiology,Neurology,Wildlife'),

    # Added July 2026: opened March 2026, confirmed via web search.
    # Coordinates approximate (Plenty Rd, Whittlesea township) - not precisely geocoded.
    ('VicVet Emergency and Referral',
     '2394 Plenty Rd', 'Whittlesea',
     -37.5136, 145.1195,
     'specialist',
     'Emergency,Critical Care,Surgery,Oncology,Internal Medicine,Rehabilitation'),
]


class Command(BaseCommand):
    help = 'Seed the database with Victorian LGA data and known pet hospital locations'

    def handle(self, *args, **options):
        lga_count = 0
        for row in LGA_DATA:
            (name, population, households, income_index, growth_rate,
             is_corridor, lat, lng, has_freeway, road_score, major_roads) = row
            obj, created = LGA.objects.get_or_create(
                name=name,
                defaults={
                    'population': population,
                    'household_count': households,
                    'median_income_index': income_index,
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
                # Update existing record
                obj.population = population
                obj.household_count = households
                obj.median_income_index = income_index
                obj.growth_rate_pct = growth_rate
                obj.is_growth_corridor = is_corridor
                obj.latitude = lat
                obj.longitude = lng
                obj.has_freeway_access = has_freeway
                obj.road_access_score = road_score
                obj.major_roads = major_roads
                obj.save()
            lga_count += 1

        hosp_count = 0
        for row in PET_HOSPITALS_DATA:
            name, address, suburb, lat, lng, hosp_type, services = row
            obj, created = PetHospital.objects.get_or_create(
                name=name,
                defaults={
                    'address': address,
                    'suburb': suburb,
                    'latitude': lat,
                    'longitude': lng,
                    'hospital_type': hosp_type,
                    'services': services,
                    'is_active': True,
                }
            )
            if not created:
                obj.address = address
                obj.suburb = suburb
                obj.latitude = lat
                obj.longitude = lng
                obj.hospital_type = hosp_type
                obj.services = services
                obj.save()
            hosp_count += 1

        self.stdout.write(self.style.SUCCESS(
            'Loaded {} LGAs and {} pet hospitals.'.format(lga_count, hosp_count)
        ))
