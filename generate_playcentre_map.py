"""
generate_playcentre_map.py — Wyndham Corridor Play Centre Feasibility Map
Uses cartopy + Natural Earth for proper geographic background (same technique
as generate_map.py, but zoomed to the Wyndham growth corridor).
"""

import sqlite3, os, warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

# ─── load data ────────────────────────────────────────────────────────────
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pethosp_analysis.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
    SELECT name, suburb_id, latitude, longitude, format_type
    FROM playcentre_competitorplaycentre WHERE is_active=1
""")
competitors = cur.fetchall()

cur.execute("""
    SELECT s.name, sc.rank, sc.composite_score, s.latitude, s.longitude,
           s.is_growth_corridor, sc.min_distance_to_competitor_km
    FROM playcentre_suburb s
    JOIN playcentre_suburbscore sc ON s.id = sc.suburb_id
    ORDER BY sc.rank ASC
""")
suburbs = cur.fetchall()

cur.execute("""
    SELECT name, latitude, longitude, site_type, size_sqm, verified
    FROM playcentre_candidatesite
""")
sites = cur.fetchall()
conn.close()

# ─── colour scheme ─────────────────────────────────────────────────────────
RANK_COLORS = ['#1b5e20', '#388e3c', '#7cb342', '#f9a825', '#ef6c00',
               '#e64a19', '#c62828', '#8e24aa', '#5e35b1', '#37474f']

COMPETITOR_CFG = {
    'boutique_inflatable': {'color': '#c0392b', 'marker': 'P', 'size': 170, 'label': 'Boutique / inflatable play'},
    'big_box_chain':       {'color': '#922b21', 'marker': '*', 'size': 230, 'label': 'Big-box chain play centre'},
    'trampoline_park':     {'color': '#a04000', 'marker': '^', 'size': 190, 'label': 'Trampoline park'},
    'other':               {'color': '#b03a2e', 'marker': 'o', 'size': 150, 'label': 'Other entertainment venue'},
}

SITE_CFG = {
    'warehouse_lease':      {'color': '#1565c0', 'label': 'Warehouse for lease'},
    'industrial_land_sale': {'color': '#00838f', 'label': 'Industrial land for sale'},
    'commercial_dev_site':  {'color': '#2e7d32', 'label': 'Commercial dev. site'},
    'future_precinct':      {'color': '#6a1b9a', 'label': 'Future precinct'},
}

SUBURB_LABEL_OFFSETS = {
    'Mambourin':        (-0.035,  0.012),
    'Manor Lakes':      ( 0.006,  0.028),
    'Wyndham Vale':     ( 0.028, -0.020),
    'Werribee':         ( 0.020, -0.020),
    'Werribee South':   ( 0.000, -0.022),
    'Tarneit':          ( 0.022,  0.016),
    'Truganina':        ( 0.024,  0.010),
    'Point Cook':       ( 0.010, -0.024),
    'Hoppers Crossing': (-0.028, -0.014),
    'Williams Landing': ( 0.016,  0.020),
}

# ─── build figure ─────────────────────────────────────────────────────────
PROJ = ccrs.PlateCarree()
fig = plt.figure(figsize=(16, 13))
ax = fig.add_subplot(1, 1, 1, projection=PROJ)

# Tight zoom on the Wyndham growth corridor
ax.set_extent([144.50, 144.82, -37.99, -37.76], crs=PROJ)

# ─── geographic background ─────────────────────────────────────────────────
ocean_shp = shpreader.natural_earth(resolution='10m', category='physical', name='ocean')
ax.add_feature(cfeature.ShapelyFeature(
    shpreader.Reader(ocean_shp).geometries(), PROJ,
    facecolor='#c8dff5', edgecolor='none'), zorder=1)

land_shp = shpreader.natural_earth(resolution='10m', category='physical', name='land')
ax.add_feature(cfeature.ShapelyFeature(
    shpreader.Reader(land_shp).geometries(), PROJ,
    facecolor='#f0ece4', edgecolor='none'), zorder=2)

ax.add_feature(cfeature.COASTLINE.with_scale('10m'),
               linewidth=0.7, edgecolor='#6b7b8d', zorder=4)

ax.set_xticks(np.arange(144.50, 144.85, 0.05), crs=PROJ)
ax.set_yticks(np.arange(-37.99, -37.75, 0.05), crs=PROJ)
ax.tick_params(labelsize=6.5, colors='#555555', length=0)
ax.grid(True, linewidth=0.4, color='#bbbbbb', alpha=0.5, linestyle='--', zorder=5)

# ─── user's marked target zone (approximate outline from the hand-drawn map) ──
# Rough polygon tracing Mambourin - Manor Lakes - Wyndham Vale, matching the
# hand-drawn loops in the source screenshot (not a precise cadastral boundary).
target_zone_lng = [144.560, 144.585, 144.625, 144.645, 144.630, 144.600,
                   144.575, 144.555, 144.548, 144.560]
target_zone_lat = [-37.883, -37.862, -37.858, -37.872, -37.900, -37.912,
                   -37.905, -37.895, -37.888, -37.883]
target_zone = mpatches.Polygon(
    list(zip(target_zone_lng, target_zone_lat)),
    closed=True, transform=PROJ,
    facecolor='none', edgecolor='#d81b60', linewidth=2.8,
    linestyle=(0, (6, 3)), zorder=6,
)
ax.add_patch(target_zone)
ax.text(144.600, -37.858, "USER'S MARKED TARGET ZONE",
        fontsize=8, fontweight='bold', color='#d81b60',
        ha='center', va='bottom', transform=PROJ, zorder=11,
        path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])

# ─── recommended tri-suburb centre point ───────────────────────────────────
# Geometric centroid of Mambourin / Wyndham Vale / Manor Lakes, which sits on
# the Ballan Road corridor — the primary recommendation for a single site
# serving all three suburbs (see report's "PRIMARY RECOMMENDATION" section).
centre_lng, centre_lat = 144.599, -37.886
ax.plot(centre_lng, centre_lat, marker='*', markersize=26, color='#ffca28',
        markeredgecolor='#c62828', markeredgewidth=1.8, transform=PROJ, zorder=20)
rec_txt = ax.text(
    centre_lng - 0.028, centre_lat - 0.006,
    'RECOMMENDED:\nBallan Rd corridor\n(serves all 3 suburbs)',
    fontsize=8.2, fontweight='bold', color='#c62828',
    ha='right', va='center', transform=PROJ, zorder=20, linespacing=1.3,
    bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff8e1', alpha=0.95,
              edgecolor='#c62828', linewidth=1.3),
)

# ─── suburb score circles ──────────────────────────────────────────────────
for name, rank, score, lat, lng, is_corr, min_dist in suburbs:
    lat, lng, score = float(lat), float(lng), float(score)
    color = RANK_COLORS[(rank - 1) % len(RANK_COLORS)]
    radius = 0.010 + (score / 100.0) * 0.014

    circle = mpatches.Circle(
        (lng, lat), radius=radius, transform=PROJ,
        facecolor=color, alpha=0.30, edgecolor=color, linewidth=2.0, zorder=7,
    )
    ax.add_patch(circle)
    ax.plot(lng, lat, 'o', color=color, markersize=6,
            markeredgecolor='white', markeredgewidth=1.2, transform=PROJ, zorder=9)

    dx, dy = SUBURB_LABEL_OFFSETS.get(name, (0.015, 0.015))
    corridor_flag = ' ▲' if is_corr else ''
    label = '#{}  {}{}\n{:.0f}/100'.format(rank, name, corridor_flag, score)
    txt = ax.text(
        lng + dx, lat + dy, label,
        fontsize=7.8, fontweight='bold', color=color,
        ha='left' if dx >= 0 else 'right', va='bottom' if dy >= 0 else 'top',
        transform=PROJ, zorder=10, linespacing=1.3,
        bbox=dict(boxstyle='round,pad=0.22', facecolor='white', alpha=0.85,
                  edgecolor=color, linewidth=0.7),
    )

# ─── existing competitors ──────────────────────────────────────────────────
# Manual per-competitor label offsets: these 3 venues sit within ~700m of each
# other in Werribee, so default offsets collide.
COMPETITOR_LABEL_OFFSETS = {
    'BouncyRoos':               (0.012, 0.006, 'left', 'bottom'),
    'Werribee Indoor Sports':   (0.012, -0.010, 'left', 'top'),
    'Bumble Beez Indoor Playcentre & Cafe': (-0.012, -0.010, 'right', 'top'),
}

plotted_types = set()
for name, suburb_id, lat, lng, ftype in competitors:
    lat, lng = float(lat), float(lng)
    cfg = COMPETITOR_CFG.get(ftype, COMPETITOR_CFG['other'])
    lbl = cfg['label'] if ftype not in plotted_types else '_nolegend_'
    ax.scatter(lng, lat, c=cfg['color'], marker=cfg['marker'], s=cfg['size'],
               edgecolors='white', linewidths=1.2, transform=PROJ, zorder=12, label=lbl)
    plotted_types.add(ftype)
    short = name if len(name) < 22 else name[:20] + '…'
    dx, dy, ha, va = COMPETITOR_LABEL_OFFSETS.get(name, (0, -0.008, 'center', 'top'))
    t = ax.text(lng + dx, lat + dy, short, fontsize=6.2, ha=ha, va=va,
                color='#1a1a1a', transform=PROJ, zorder=13)
    t.set_path_effects([pe.withStroke(linewidth=2, foreground='white')])

# ─── candidate sites ────────────────────────────────────────────────────────
# Short display names + manual stacked offsets for the 3 Truganina sites,
# which sit close together and would otherwise overlap.
SITE_SHORT_NAMES = {
    'Foundation at Truganina (Dexus industrial estate)': 'Foundation at Truganina',
    'Industrial/Warehouse Space – 355 Palmers Rd': '355 Palmers Rd',
    'Industrial/Warehouse Space – 42 Sunline Drive': '42 Sunline Dr',
    'Warehouse/Showroom/Retail Space – 14 Tallis Circuit': '14 Tallis Cct',
    'Land/Development Site – Lot 3-4, 440 Black Forest Rd / 323 Greens Rd': 'Lot 3-4 Black Forest Rd',
    'Mambourin Town Centre (future precinct)': 'Mambourin Town Centre',
    'Manor Lakes Central (retail space for lease)': 'Manor Lakes Central',
    '440 & 462 Ballan Rd / 2 Hirata Blvd (recently sold, market signal only)': '440/462 Ballan Rd (SOLD)',
    '819 Ballan Rd, Manor Lakes (large vacant parcel)': '819 Ballan Rd',
}
SITE_LABEL_OFFSETS = {
    'Foundation at Truganina (Dexus industrial estate)':   (0, 0.014, 'center', 'bottom'),
    'Industrial/Warehouse Space – 355 Palmers Rd':          (-0.014, 0.001, 'right', 'center'),
    'Industrial/Warehouse Space – 42 Sunline Drive':        (0.014, 0.001, 'left', 'center'),
    'Warehouse/Showroom/Retail Space – 14 Tallis Circuit':  (0, -0.013, 'center', 'top'),
    'Manor Lakes Central (retail space for lease)':         (0.020, 0.004, 'left', 'center'),
    '440 & 462 Ballan Rd / 2 Hirata Blvd (recently sold, market signal only)': (0.024, -0.020, 'left', 'top'),
    '819 Ballan Rd, Manor Lakes (large vacant parcel)':     (0.030, 0.002, 'left', 'center'),
}
# Sites that are confirmed NOT available (e.g. sold off-market) get a distinct
# grey "X" marker regardless of their verified flag, so the map never implies
# they're a live option.
SITE_UNAVAILABLE = {'440 & 462 Ballan Rd / 2 Hirata Blvd (recently sold, market signal only)'}

plotted_site_types = set()
for name, lat, lng, stype, size_sqm, verified in sites:
    lat, lng = float(lat), float(lng)
    cfg = SITE_CFG.get(stype, SITE_CFG['warehouse_lease'])
    lbl = cfg['label'] if stype not in plotted_site_types else '_nolegend_'
    if name in SITE_UNAVAILABLE:
        marker_style, marker_color, marker_alpha = 'x', '#757575', 0.9
        lbl = '_nolegend_'
    else:
        marker_style = '^' if verified else 'v'
        marker_color, marker_alpha = cfg['color'], (1.0 if verified else 0.55)
    ax.scatter(lng, lat, c=marker_color, marker=marker_style, s=170,
               edgecolors='white', linewidths=1.3, transform=PROJ, zorder=12,
               alpha=marker_alpha, label=lbl)
    plotted_site_types.add(stype)
    short = SITE_SHORT_NAMES.get(name, name if len(name) < 26 else name[:24] + '…')
    size_str = ' ({} sqm)'.format(size_sqm) if size_sqm else ''
    label_color = '#757575' if name in SITE_UNAVAILABLE else '#0d3d56'
    dx, dy, ha, va = SITE_LABEL_OFFSETS.get(name, (0, 0.009, 'center', 'bottom'))
    t = ax.text(lng + dx, lat + dy, short + size_str, fontsize=6.0, ha=ha, va=va,
                color=label_color, fontweight='bold', transform=PROJ, zorder=13)
    t.set_path_effects([pe.withStroke(linewidth=2, foreground='white')])

# ─── legend ────────────────────────────────────────────────────────────────
legend_handles = [mpatches.Patch(facecolor='none', edgecolor='none', label='── TOP RANKED SUBURBS ──')]
for name, rank, score, lat, lng, is_corr, min_dist in suburbs[:5]:
    color = RANK_COLORS[(rank - 1) % len(RANK_COLORS)]
    legend_handles.append(mpatches.Patch(
        facecolor=color, alpha=0.75, edgecolor='white',
        label='#{}  {}  ({:.1f}/100)'.format(rank, name, float(score)),
    ))

legend_handles.append(mpatches.Patch(facecolor='none', edgecolor='none', label=' '))
legend_handles.append(mpatches.Patch(facecolor='none', edgecolor='none', label='── EXISTING COMPETITORS ──'))
for ftype, cfg in COMPETITOR_CFG.items():
    if ftype in plotted_types:
        legend_handles.append(mpatches.Patch(facecolor=cfg['color'], edgecolor='white', label=cfg['label']))

legend_handles.append(mpatches.Patch(facecolor='none', edgecolor='none', label=' '))
legend_handles.append(mpatches.Patch(facecolor='none', edgecolor='none', label='── CANDIDATE SITES (▲ verified / ▽ unverified) ──'))
for stype, cfg in SITE_CFG.items():
    if stype in plotted_site_types:
        legend_handles.append(mpatches.Patch(facecolor=cfg['color'], edgecolor='white', label=cfg['label']))
if any(s[0] in SITE_UNAVAILABLE for s in sites):
    legend_handles.append(mpatches.Patch(facecolor='#757575', edgecolor='white', label='✕ Sold / not available (context only)'))

leg = ax.legend(
    handles=legend_handles, loc='upper left', fontsize=7.6,
    framealpha=0.94, edgecolor='#aaaaaa', handlelength=1.1,
    borderpad=0.9, labelspacing=0.45,
)

# ─── title & footnote ──────────────────────────────────────────────────────
ax.set_title(
    'Wyndham Growth Corridor — Play Centre Feasibility Analysis\n'
    'Competitors, Candidate Sites &amp; Ranked Suburbs vs the User-Marked Target Zone'.replace('&amp;', '&'),
    fontsize=13.5, fontweight='bold', pad=10, color='#1a1a1a',
)

fig.text(
    0.01, 0.005,
    'Scoring weights: family population 30% · growth/corridor 25% · supply gap 25% · road access 10% · site availability 10%\n'
    f'Data: web search July 2026 ({len(competitors)} competitors, {len(sites)} candidate sites) — unverified sites need agent confirmation before relying on them',
    fontsize=6.3, color='#666666', va='bottom',
)

plt.tight_layout(pad=0.6)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playcentre_map.png')
fig.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved: {out}")
plt.close(fig)
