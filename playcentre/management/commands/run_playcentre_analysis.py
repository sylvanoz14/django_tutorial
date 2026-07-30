"""
Management command: run_playcentre_analysis

Scores all Wyndham-corridor suburbs for play centre development attractiveness,
saves results to the SuburbScore table, and writes playcentre_report.txt.

Usage:
    python manage.py run_playcentre_analysis
"""
import os
from collections import defaultdict
from django.core.management.base import BaseCommand
from playcentre.models import Suburb, CompetitorPlayCentre, CandidateSite, SuburbScore
from playcentre.analysis import compute_scores, generate_report


class Command(BaseCommand):
    help = 'Score all Wyndham corridor suburbs and generate the play centre feasibility report'

    def handle(self, *args, **options):
        suburbs = list(Suburb.objects.all())
        competitors = list(CompetitorPlayCentre.objects.filter(is_active=True))
        sites = list(CandidateSite.objects.all())

        if not suburbs:
            self.stderr.write('No suburb data found. Run: python manage.py seed_playcentre_data')
            return
        if not competitors:
            self.stderr.write('No competitor data found. Run: python manage.py seed_playcentre_data')
            return

        sites_by_suburb = defaultdict(list)
        for s in sites:
            sites_by_suburb[s.suburb_id].append(s)

        self.stdout.write('Scoring {} suburbs against {} competitors and {} candidate sites...'.format(
            len(suburbs), len(competitors), len(sites)
        ))

        results = compute_scores(suburbs, competitors, sites_by_suburb)

        for r in results:
            score_obj, _ = SuburbScore.objects.get_or_create(suburb=r['suburb'])
            score_obj.min_distance_to_competitor_km = r['min_dist']
            score_obj.nearest_competitor = r['nearest_competitor']
            score_obj.best_candidate_site = r['best_candidate_site']
            score_obj.family_population_score = r['family_population_score']
            score_obj.growth_score = r['growth_score']
            score_obj.supply_gap_score = r['supply_gap_score']
            score_obj.road_access_score = r['road_access_score']
            score_obj.site_availability_score = r['site_availability_score']
            score_obj.composite_score = r['composite_score']
            score_obj.rank = r['rank']
            score_obj.save()

        report_text = generate_report(results, top_n=5)
        self.stdout.write('\n' + report_text)

        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            'playcentre_report.txt'
        )
        with open(report_path, 'w') as f:
            f.write(report_text)

        self.stdout.write(self.style.SUCCESS('\nReport saved to: {}'.format(report_path)))
        self.stdout.write(self.style.SUCCESS('Dashboard available at: http://localhost:8000/playcentre/'))
