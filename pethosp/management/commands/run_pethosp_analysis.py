"""
Management command: run_pethosp_analysis

Runs the pet hospital location scoring algorithm over all Victorian LGAs,
saves results to the LGAScore table, prints the top-5 investment report to
stdout, and writes it to pethosp_report.txt in the project root.

Usage:
    python manage.py run_pethosp_analysis
"""
from __future__ import unicode_literals
import os
from django.core.management.base import BaseCommand
from pethosp.models import LGA, PetHospital, LGAScore
from pethosp.analysis import compute_scores, generate_report


class Command(BaseCommand):
    help = 'Score all Victorian LGAs and generate the top-5 pet hospital investment report'

    def handle(self, *args, **options):
        lgas = list(LGA.objects.all())
        hospitals = list(PetHospital.objects.filter(is_active=True))

        if not lgas:
            self.stderr.write('No LGA data found. Run: python manage.py seed_pethosp_data')
            return
        if not hospitals:
            self.stderr.write('No pet hospital data found. Run: python manage.py seed_pethosp_data')
            return

        self.stdout.write('Scoring {} LGAs against {} pet hospitals...'.format(
            len(lgas), len(hospitals)
        ))

        results = compute_scores(lgas, hospitals)

        # Persist to database
        for r in results:
            score_obj, _ = LGAScore.objects.get_or_create(lga=r['lga'])
            score_obj.estimated_pet_population = r['estimated_pets']
            score_obj.min_distance_to_hospital_km = r['min_dist']
            score_obj.nearest_hospital = r['nearest_hospital']
            score_obj.pet_population_score = r['pet_population_score']
            score_obj.growth_score = r['growth_score']
            score_obj.supply_gap_score = r['supply_gap_score']
            score_obj.road_access_score = r['road_access_score']
            score_obj.affordability_score = r['affordability_score']
            score_obj.composite_score = r['composite_score']
            score_obj.rank = r['rank']
            score_obj.save()

        # Generate report text
        report_text = generate_report(results, top_n=5)

        # Print to stdout
        self.stdout.write('\n' + report_text)

        # Write to file
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            'pethosp_report.txt'
        )
        with open(report_path, 'w') as f:
            f.write(report_text)

        self.stdout.write(self.style.SUCCESS(
            '\nReport saved to: {}'.format(report_path)
        ))
        self.stdout.write(self.style.SUCCESS(
            'Dashboard available at: http://localhost:8000/pethosp/'
        ))
