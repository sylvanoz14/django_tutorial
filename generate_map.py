"""
generate_map.py — Melbourne Pet Hospital Investment Map
Uses cartopy + Natural Earth for proper geographic background.
"""

import sqlite3, os, warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.ticker as mticker
import numpy as np

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from shapely.geometry import Point
import shapely.vectorized

# ─── load data ────────────────────────────────────────────────────────────
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pethosp_analysis.db')
conn = sqlite3.connect(DB)
cur  = conn.cursor()

cur.execute("""
    SELECT name, suburb, latitude, longitude, hospital_type
    FROM pethosp_pethospital WHERE is_active=1
""")
hospitals = cur.fetchall()

cur.execute("""
    SELECT l.name, l.latitude, l.longitude,
           s.composite_score, s.rank,
           l.is_growth_corridor, l.population,
           s.estimated_pet_population,
           s.min_distance_to_hospital_km
    FROM pethosp_lga l
    JOIN pethosp_lgascore s ON l.id = s.lga_id
    ORDER BY s.rank ASC LIMIT 5
""")
top_lgas = cur.fetchall()
conn.close()

# ─── colour scheme ─────────────────────────────────────────────────────────
HOSP_CFG = {
    'emergency':  {'color': '#c0392b', 'marker': 'P', 'size': 180, 'label': 'Emergency hospital'},
    'specialist': {'color': '#6c3483', 'marker': '*', 'size': 240, 'label': 'Specialist hospital'},
    'general':    {'color': '#d35400', 'marker': 's', 'size': 140, 'label': 'General hospital'},
}

CAND_COLORS = ['#1b5e20', '#388e3c', '#e65100', '#1565c0', '#4a148c']
CAND_RADIUS_DEG = 0.22   # circle radius in degrees (~24 km)

SHORT = {
    'Animal Emergency Centre - Ascot Vale':                   'AEC Ascot Vale',
    'Animal Emergency Centre - Malvern East':                 'AEC Malvern East',
    'Animal Emergency Service (AES) Frankston':               'AES Frankston',
    'Animal Emergency Service (AES) Glen Waverley':           'AES Glen Waverley',
    'Animal Referral Hospital (ARH) Essendon':                'ARH Essendon',
    'Ballarat Veterinary Practice After Hours':               'Ballarat VP',
    'Casey Animal Emergency Centre':                          'Casey AEC',
    'Geelong Animal Emergency':                               'Geelong AE',
    'Lort Smith Animal Hospital':                             'Lort Smith',
    'Melbourne Veterinary Specialist Centre (MVSC)':          'MVSC Moorabbin',
    'Pet Emergency - Bundoora':                               'Pet Emerg. Bundoora',
    'Southern Animal Emergency (SAE) Seaford':                'SAE Seaford',
    'University of Melbourne Veterinary Hospital (Werribee)': 'UMelb Werribee',
    'University of Melbourne Veterinary Teaching Hospital':   'UMelb Parkville',
    'Veterinary Specialist Services (VSS) Essendon':          'VSS Essendon',
}

# ─── build figure ─────────────────────────────────────────────────────────
PROJ = ccrs.PlateCarree()
fig = plt.figure(figsize=(18, 14))
ax  = fig.add_subplot(1, 1, 1, projection=PROJ)

# Map extent: includes Melton(W), Whittlesea(N), Geelong(SW), Cardinia(SE)
ax.set_extent([143.70, 146.15, -38.60, -37.10], crs=PROJ)

# ─── geographic background ─────────────────────────────────────────────────
# Ocean (light blue)
ocean_shp = shpreader.natural_earth(resolution='10m', category='physical', name='ocean')
ocean_feat = cfeature.ShapelyFeature(
    shpreader.Reader(ocean_shp).geometries(),
    PROJ, facecolor='#c8dff5', edgecolor='none'
)
ax.add_feature(ocean_feat, zorder=1)

# Land (light warm grey)
land_shp = shpreader.natural_earth(resolution='10m', category='physical', name='land')
land_feat = cfeature.ShapelyFeature(
    shpreader.Reader(land_shp).geometries(),
    PROJ, facecolor='#f0ece4', edgecolor='none'
)
ax.add_feature(land_feat, zorder=2)

# Lakes (same blue as ocean)
lake_shp = shpreader.natural_earth(resolution='10m', category='physical', name='lakes')
lake_feat = cfeature.ShapelyFeature(
    shpreader.Reader(lake_shp).geometries(),
    PROJ, facecolor='#c8dff5', edgecolor='none'
)
ax.add_feature(lake_feat, zorder=3)

# Coastline
ax.add_feature(cfeature.COASTLINE.with_scale('10m'),
               linewidth=0.7, edgecolor='#6b7b8d', zorder=4)

# State border (Victoria outline)
states_shp = shpreader.natural_earth(resolution='10m',
                                      category='cultural',
                                      name='admin_1_states_provinces')
states_feat = cfeature.ShapelyFeature(
    shpreader.Reader(states_shp).geometries(),
    PROJ, facecolor='none', edgecolor='#8899aa', linewidth=0.8
)
ax.add_feature(states_feat, zorder=4)

# Subtle lat/lon tick labels (gridlines() omitted: current cartopy/shapely
# combo throws on this extent's map boundary; not essential to the figure)
ax.set_xticks(np.arange(144.0, 146.5, 0.5), crs=PROJ)
ax.set_yticks(np.arange(-38.5, -37.0, 0.5), crs=PROJ)
ax.tick_params(labelsize=7, colors='#555555', length=0)
ax.grid(True, linewidth=0.4, color='#bbbbbb', alpha=0.6, linestyle='--', zorder=5)

# ─── candidate LGA circles ─────────────────────────────────────────────────
for i, row in enumerate(top_lgas):
    name, lat, lng, score, rank, is_corr, pop, est_pets, nearest_km = row
    lat, lng, score = float(lat), float(lng), float(score)
    color = CAND_COLORS[i]
    r = CAND_RADIUS_DEG

    # Filled semi-transparent circle
    circle = mpatches.Circle(
        (lng, lat), radius=r,
        transform=PROJ,
        facecolor=color, alpha=0.18,
        edgecolor=color, linewidth=2.5,
        zorder=6
    )
    ax.add_patch(circle)

    # Central dot
    ax.plot(lng, lat, 'o', color=color, markersize=9,
            markeredgecolor='white', markeredgewidth=1.5,
            transform=PROJ, zorder=8)

    # Label
    short = name.replace('City of ', '').replace('Shire of ', '')
    corr_tag = '▲ Growth Corridor' if is_corr else ''
    label = f'#{rank}  {short}\n{score:.1f}/100  ·  {nearest_km:.0f} km gap'
    if corr_tag:
        label += f'\n{corr_tag}'

    # Per-candidate label offsets (dx, dy) tuned for Melbourne geography
    # Melton=W, Wyndham=SW, Hume=N, Cardinia=SE, Casey=S (near Cardinia)
    label_offsets = [
        (-0.35, 0.05),   # #1 Melton — label to the left
        (-0.32,-0.28),   # #2 Wyndham — label lower-left
        ( 0.05, 0.32),   # #3 Hume — label above
        ( 0.38, 0.10),   # #4 Cardinia — label to the right
        (-0.18,-0.32),   # #5 Casey — label below-left (avoid Cardinia)
    ]
    dx, dy = label_offsets[i]
    ha_map = ['right', 'right', 'center', 'left', 'right']

    txt = ax.text(
        lng + dx, lat + dy,
        label,
        fontsize=9, fontweight='bold',
        ha=ha_map[i], va='center',
        color=color, transform=PROJ, zorder=9,
        linespacing=1.4,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  alpha=0.82, edgecolor=color, linewidth=0.8),
    )
    txt.set_path_effects([pe.withStroke(linewidth=1.5, foreground='white')])

    # Connector line from dot to label box
    ax.annotate(
        '', xy=(lng, lat), xytext=(lng + dx, lat + dy),
        xycoords=PROJ._as_mpl_transform(ax),
        textcoords=PROJ._as_mpl_transform(ax),
        arrowprops=dict(arrowstyle='-', color=color, lw=1.1, alpha=0.7),
        zorder=8,
    )


# ─── existing hospitals ────────────────────────────────────────────────────
plotted_types = set()
for name, suburb, lat, lng, htype in hospitals:
    lat, lng = float(lat), float(lng)
    cfg = HOSP_CFG.get(htype, HOSP_CFG['general'])
    lbl = cfg['label'] if htype not in plotted_types else '_nolegend_'
    ax.scatter(
        lng, lat,
        c=cfg['color'], marker=cfg['marker'], s=cfg['size'],
        edgecolors='white', linewidths=1.2,
        transform=PROJ, zorder=10,
        label=lbl,
    )
    plotted_types.add(htype)

    short = SHORT.get(name, name.split('(')[0].strip()[:20])
    txt = ax.text(
        lng, lat + 0.025, short,
        fontsize=6.3, ha='center', va='bottom',
        color='#1a1a1a', transform=PROJ, zorder=11,
    )
    txt.set_path_effects([pe.withStroke(linewidth=2.2, foreground='white')])

# ─── legend ────────────────────────────────────────────────────────────────
legend_handles = []

legend_handles.append(
    mpatches.Patch(facecolor='none', edgecolor='none',
                   label='── PROPOSED SITES ──')
)
for i, row in enumerate(top_lgas):
    name, lat, lng, score, rank, is_corr, pop, est_pets, nearest_km = row
    short = name.replace('City of ', '').replace('Shire of ', '')
    legend_handles.append(mpatches.Patch(
        facecolor=CAND_COLORS[i], alpha=0.75, edgecolor='white',
        label=f'#{rank}  {short}  ({float(score):.1f}/100)',
    ))

legend_handles.append(
    mpatches.Patch(facecolor='none', edgecolor='none', label=' ')
)
legend_handles.append(
    mpatches.Patch(facecolor='none', edgecolor='none',
                   label='── EXISTING HOSPITALS ──')
)
for htype, cfg in HOSP_CFG.items():
    legend_handles.append(mpatches.Patch(
        facecolor=cfg['color'], edgecolor='white',
        label=cfg['label'],
    ))

leg = ax.legend(
    handles=legend_handles,
    loc='lower right',
    fontsize=8.8,
    framealpha=0.94,
    edgecolor='#aaaaaa',
    handlelength=1.1,
    borderpad=1.0,
    labelspacing=0.5,
)

# ─── title & footnote ──────────────────────────────────────────────────────
ax.set_title(
    'Victoria — Pet Hospital Investment Analysis\n'
    'Proposed 2,000–5,000 m² Development Sites  vs  Existing Facilities',
    fontsize=14, fontweight='bold', pad=12, color='#1a1a1a',
)

fig.text(
    0.01, 0.005,
    'Scoring weights: pet population 30% · growth/corridor 25% · supply gap 25% · road access 10% · income 10%\n'
    f'Data: ABS 2021 Census · Plan Melbourne 2017-2050 · VIF 2022 · {len(hospitals)} known pet hospitals '
    '(updated July 2026: adds VicVet Whittlesea, opened Mar 2026)',
    fontsize=6.5, color='#666666', va='bottom',
)

# ─── Melbourne CBD reference point ────────────────────────────────────────
cbd_lng, cbd_lat = 144.9631, -37.8136
ax.plot(cbd_lng, cbd_lat, 'k^', markersize=7, transform=PROJ, zorder=12,
        markeredgecolor='white', markeredgewidth=1.0)
t = ax.text(cbd_lng + 0.04, cbd_lat - 0.04, 'Melbourne\nCBD',
            fontsize=7, ha='left', va='top', color='#222222',
            transform=PROJ, zorder=12)
t.set_path_effects([pe.withStroke(linewidth=2, foreground='white')])

plt.tight_layout(pad=0.8)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pethosp_map.png')
fig.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved: {out}")
plt.close(fig)
