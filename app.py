import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from flask import Flask, render_template, url_for

app = Flask(__name__)

# ============================================================
# Static reference data
# ============================================================

TEAM_TO_CODE = {
    'Mexico': 'MEX', 'South Africa': 'RSA', 'Korea Republic': 'KOR',
    'Czechia': 'CZE', 'Canada': 'CAN', 'Bosnia & Herz.': 'BIH',
    'United States': 'USA', 'Paraguay': 'PAR', 'Qatar': 'QAT',
    'Switzerland': 'SUI', 'Brazil': 'BRA', 'Morocco': 'MAR',
    'Haiti': 'HAI', 'Scotland': 'SCO', 'Australia': 'AUS',
    'Türkiye': 'TUR', 'Germany': 'GER', 'Curaçao': 'CUW',
    'Netherlands': 'NED', 'Japan': 'JPN', "Côte d'Ivoire": 'CIV',
    'Ecuador': 'ECU', 'Sweden': 'SWE', 'Tunisia': 'TUN',
    'Belgium': 'BEL', 'Egypt': 'EGY', 'Spain': 'ESP',
    'Cabo Verde': 'CPV', 'IR Iran': 'IRN', 'New Zealand': 'NZL',
    'Saudi Arabia': 'KSA', 'Uruguay': 'URU', 'France': 'FRA',
    'Senegal': 'SEN', 'Iraq': 'IRQ', 'Norway': 'NOR',
    'Argentina': 'ARG', 'Algeria': 'ALG', 'Austria': 'AUT',
    'Jordan': 'JOR', 'Portugal': 'POR', 'Congo DR': 'COD',
    'England': 'ENG', 'Croatia': 'CRO', 'Ghana': 'GHA',
    'Panama': 'PAN', 'Uzbekistan': 'UZB', 'Colombia': 'COL',
}

KIT_MANUFACTURERS = {
    'MEX': 'Adidas', 'RSA': 'Adidas', 'KOR': 'Nike', 'CZE': 'Puma',
    'CAN': 'Nike', 'BIH': 'Kelme', 'USA': 'Nike', 'PAR': 'Puma',
    'QAT': 'Adidas', 'SUI': 'Puma', 'BRA': 'Nike', 'MAR': 'Puma',
    'HAI': 'Saeta', 'SCO': 'Adidas', 'AUS': 'Nike', 'TUR': 'Nike',
    'GER': 'Adidas', 'CUW': 'Adidas', 'NED': 'Nike', 'JPN': 'Adidas',
    'CIV': 'Puma', 'ECU': 'Marathon', 'SWE': 'Adidas', 'TUN': 'Kappa',
    'BEL': 'Adidas', 'EGY': 'Puma', 'ESP': 'Adidas', 'CPV': 'Capelli',
    'IRN': 'Majid', 'NZL': 'Puma', 'KSA': 'Adidas', 'URU': 'Nike',
    'FRA': 'Nike', 'SEN': 'Puma', 'IRQ': 'Jako', 'NOR': 'Nike',
    'ARG': 'Adidas', 'ALG': 'Adidas', 'AUT': 'Puma', 'JOR': 'Kelme',
    'POR': 'Puma', 'COD': 'Umbro', 'ENG': 'Nike', 'CRO': 'Nike',
    'GHA': 'Puma', 'PAN': 'Reebok', 'UZB': '7Saber', 'COL': 'Adidas',
}

ALL_BRANDS = sorted(set(KIT_MANUFACTURERS.values()))
CODE_TO_TEAM = {v: k for k, v in TEAM_TO_CODE.items()}

# Update team_code / image once winners are known. Images live in static/assets/awards/.
AWARDS = {
    "champions": {"team_code": "ESP", "image": "assets/awards/champions.jpg"},
    "individual": [
        {"label": "Golden Ball", "team_code": "ESP", "image": "assets/awards/golden_ball.jpg"},
        {"label": "Golden Boot", "team_code": "FRA", "image": "assets/awards/golden_boot.jpg"},
        {"label": "Golden Glove", "team_code": "ESP", "image": "assets/awards/golden_glove.jpg"},
        {"label": "Young Player", "team_code": "ESP", "image": "assets/awards/young_player.jpg"},
    ],
}

BRAND_COLORS = {
    'Adidas': '#75AADB', 'Nike': '#003189', 'Puma': '#FF0000',
    'Kelme': '#E30613', 'Saeta': '#00209F', 'Marathon': '#FFD100',
    'Kappa': '#E70013', 'Capelli': '#003893', 'Majid': '#239F40',
    'Jako': '#007A3D', 'Reebok': '#CE1126', 'Umbro': '#007FFF',
    '7Saber': '#1EB53A',
}

PLOTLY_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', size=12, color='#97969b'),
    title_font=dict(family='IBM Plex Mono', size=13, color='#f2f0ea'),
    margin=dict(t=56, b=64, l=8, r=8),
    height=400,
    bargap=0.32,
    bargroupgap=0.12,
    hovermode='closest',
    hoverlabel=dict(
        bgcolor='#151517',
        bordercolor='rgba(232,179,74,0.5)',
        font=dict(family='Inter', size=12, color='#f2f0ea'),
    ),
    uniformtext=dict(minsize=10, mode='hide'),
    xaxis=dict(
        title=None, showgrid=False, showline=False,
        tickfont=dict(family='Inter', size=11, color='#888'),
    ),
    yaxis=dict(
        title=None, showgrid=True,
        gridcolor='rgba(255,255,255,0.04)',
        griddash='dot',
        showline=False,
        zeroline=True, zerolinecolor='rgba(232,179,74,0.18)', zerolinewidth=1.5,
        tickfont=dict(family='Inter', size=11, color='#5a5a5f'),
    ),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', size=11, color='#aaa'),
        orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
    ),
    modebar=dict(remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                          'autoScale2d', 'resetScale2d', 'toImage', 'sendDataToCloud',
                          'toggleHover', 'resetViews', 'toggleSpikelines']),
)

# ============================================================
# Data loading (cached in-process so it only downloads/parses once)
# ============================================================

_data_cache = {}


def load_data():
    if 'df' in _data_cache:
        return _data_cache['df']

    df = pd.read_csv("data/matches.csv")
    df['date'] = pd.to_datetime(df['date'])
    df[['home_offsides', 'away_offsides']] = df[['home_offsides', 'away_offsides']].fillna(0)
    df['home_team'] = df['home_team'].map(TEAM_TO_CODE)
    df['away_team'] = df['away_team'].map(TEAM_TO_CODE)
    df['home_kit'] = df['home_team'].map(KIT_MANUFACTURERS)
    df['away_kit'] = df['away_team'].map(KIT_MANUFACTURERS)

    def get_winner(row):
        if row['home_score'] > row['away_score']:
            return row['home_team']
        elif row['home_score'] < row['away_score']:
            return row['away_team']
        else:
            return 'draw'

    df['winner'] = df.apply(get_winner, axis=1)
    _data_cache['df'] = df
    return df


# ============================================================
# Image helpers (still used for story rows / awards / champions banner)
# ============================================================

def logo_url(brand):
    """Static URL for a brand logo, or None if the file doesn't exist yet."""
    if not brand:
        return None
    path = Path(app.static_folder) / "assets" / "logos" / f"{brand}.png"
    if not path.exists():
        return None
    return url_for('static', filename=f"assets/logos/{brand}.png")


def award_image_url(rel_path):
    """Static URL for an award/champions photo, or None if not uploaded yet."""
    path = Path(app.static_folder) / rel_path
    if not path.exists():
        return None
    return url_for('static', filename=rel_path)


# ============================================================
# Chart helpers
# ============================================================

def rotate_xaxis_labels(fig):
    """Show brand names as -90deg rotated tick labels instead of logo images."""
    fig.update_layout(
        xaxis=dict(
            tickangle=-90,
            showticklabels=True,
        ),
        margin=dict(t=56, b=110, l=8, r=8),  # extra bottom room for rotated labels
    )
    return fig


def apply_layout(fig, title=''):
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(
            text=title.upper(),
            font=dict(family='IBM Plex Mono', size=13, color='#f2f0ea'),
            x=0.01, xanchor='left',
            pad=dict(b=18),
        ))
    fig.update_traces(
        selector=dict(type='bar'),
        marker_line_width=1,
        marker_line_color='rgba(255,255,255,0.08)',
        textfont=dict(family='Inter', size=13, color='#fff'),
        opacity=0.94,
    )
    try:
        fig.update_traces(selector=dict(type='bar'), marker_cornerradius=6)
    except Exception:
        pass
    return fig


def brand_colors_for(series):
    return [BRAND_COLORS.get(b, '#888888') for b in series]


def reindex_brands(df_agg, value_col):
    return (df_agg.set_index('brand').reindex(ALL_BRANDS, fill_value=0)
            .reset_index().rename(columns={'index': 'brand'}).sort_values(value_col, ascending=False))


def bar_chart(df_plot, x, y, title, text=None, color_series=None):
    t = text if text is not None else df_plot[y]
    fig = px.bar(df_plot, x=x, y=y, text=t, custom_data=[df_plot[x]])
    if color_series is not None:
        fig.update_traces(marker_color=brand_colors_for(color_series), textposition='outside')
    else:
        fig.update_traces(textposition='outside')
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>' + title + ': %{y}<extra></extra>')
    fig.update_layout(xaxis={'categoryorder': 'total descending'}, bargap=0.4)
    apply_layout(fig, title)
    rotate_xaxis_labels(fig)
    return fig


def fig_json(fig):
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


# ============================================================
# Build the whole dashboard payload for one request
# ============================================================

def build_dashboard():
    df = load_data()
    dff = df

    # ---- Hero metrics ----
    total_matches = len(df)
    total_goals = int(df['home_score'].sum() + df['away_score'].sum())
    top_brand = pd.Series(KIT_MANUFACTURERS).value_counts().idxmax()
    top_brand_count = int(pd.Series(KIT_MANUFACTURERS).value_counts().max())
    most_wins_brand = pd.concat([
        df[df['winner'] != 'draw'].groupby('home_kit').apply(
            lambda x: (x['winner'] == x['home_team']).sum(), include_groups=False),
        df[df['winner'] != 'draw'].groupby('away_kit').apply(
            lambda x: (x['winner'] == x['away_team']).sum(), include_groups=False),
    ]).groupby(level=0).sum().idxmax()

    metrics = [
        {"label": "Matches Played", "value": total_matches, "sub": "Group Stage"},
        {"label": "Total Goals", "value": total_goals, "sub": f"{total_goals / total_matches:.1f} per game"},
        {"label": "Most Teams", "value": top_brand, "sub": f"{top_brand_count} nations"},
        {"label": "Most Wins", "value": most_wins_brand, "sub": "Leading brand"},
        {"label": "Brands", "value": len(ALL_BRANDS), "sub": "Kit suppliers"},
    ]

    # ---- Awards / hero section ----
    champ = AWARDS["champions"]
    champ_brand = KIT_MANUFACTURERS.get(champ["team_code"])
    champions = {
        "name": CODE_TO_TEAM.get(champ["team_code"], champ["team_code"]),
        "image_url": award_image_url(champ["image"]),
        "logo_url": logo_url(champ_brand),
    }
    awards = []
    for a in AWARDS["individual"]:
        brand = KIT_MANUFACTURERS.get(a["team_code"])
        awards.append({
            "label": a["label"],
            "image_url": award_image_url(a["image"]),
            "logo_url": logo_url(brand),
        })

    # ---- Tournament story ----
    team_counts_s = pd.Series(KIT_MANUFACTURERS).value_counts()
    avg_teams_s = team_counts_s.mean()

    story_wins_s = pd.concat([
        df[df['winner'] != 'draw'].groupby('home_kit').apply(
            lambda x: (x['winner'] == x['home_team']).sum(), include_groups=False),
        df[df['winner'] != 'draw'].groupby('away_kit').apply(
            lambda x: (x['winner'] == x['away_team']).sum(), include_groups=False),
    ]).groupby(level=0).sum().reindex(ALL_BRANDS, fill_value=0)

    story_games_s = pd.concat([
        df.groupby('home_kit').size(),
        df.groupby('away_kit').size(),
    ]).groupby(level=0).sum().reindex(ALL_BRANDS, fill_value=0)

    story_win_rate_s = (story_wins_s / story_games_s.replace(0, float('nan')) * 100).round(1).fillna(0)

    story_goals_s = pd.concat([
        df.groupby('home_kit')['home_score'].sum(),
        df.groupby('away_kit')['away_score'].sum(),
    ]).groupby(level=0).sum().reindex(ALL_BRANDS, fill_value=0)
    story_goals_pg_s = (story_goals_s / story_games_s.replace(0, float('nan'))).round(2).fillna(0)

    story_conceded_s = pd.concat([
        df.groupby('away_kit')['home_score'].sum(),
        df.groupby('home_kit')['away_score'].sum(),
    ]).groupby(level=0).sum().reindex(ALL_BRANDS, fill_value=0)
    story_conceded_pg_s = (story_conceded_s / story_games_s.replace(0, float('nan'))).round(2).fillna(99)

    story_cards_s = pd.concat([
        df.groupby('home_kit')[['home_cards_yellow', 'home_cards_red']].sum().rename(
            columns={'home_cards_yellow': 'yellow', 'home_cards_red': 'red'}),
        df.groupby('away_kit')[['away_cards_yellow', 'away_cards_red']].sum().rename(
            columns={'away_cards_yellow': 'yellow', 'away_cards_red': 'red'}),
    ]).groupby(level=0).sum().reindex(ALL_BRANDS, fill_value=0)
    story_cards_s['total'] = story_cards_s['yellow'] + story_cards_s['red']

    story_poss_s = pd.concat([
        df.groupby('home_kit')['home_possession'].mean(),
        df.groupby('away_kit')['away_possession'].mean(),
    ]).groupby(level=0).mean().reindex(ALL_BRANDS)

    leader_brand = team_counts_s.idxmax()
    leader_teams = int(team_counts_s.max())
    total_teams = len(KIT_MANUFACTURERS)

    wins_leader = story_wins_s.idxmax()
    wins_leader_count = int(story_wins_s.max())

    eligible_underdogs = story_win_rate_s[
        (team_counts_s.reindex(ALL_BRANDS, fill_value=0) <= avg_teams_s) & (story_games_s >= 2)
    ]
    underdog_brand = eligible_underdogs.idxmax() if len(eligible_underdogs) else story_win_rate_s.idxmax()
    underdog_rate = eligible_underdogs.max() if len(eligible_underdogs) else story_win_rate_s.max()
    underdog_teams = int(team_counts_s.get(underdog_brand, 0))

    attack_brand = story_goals_pg_s.idxmax()
    attack_value = story_goals_pg_s.max()

    defense_brand = story_conceded_pg_s.idxmin()
    defense_value = story_conceded_pg_s.min()

    dirty_brand = story_cards_s['total'].idxmax()
    dirty_value = int(story_cards_s['total'].max())

    poss_brand = story_poss_s.idxmax()
    poss_value = story_poss_s.max()

    story_chapters_raw = [
        ("Market Power", leader_brand,
         f"<b>{leader_brand}</b> dresses more nations than any rival, outfitting <b>{leader_teams} of the {total_teams}</b> "
         f"teams at the tournament — the widest reach of any manufacturer before a ball was even kicked."),
        ("On The Scoreboard", wins_leader,
         f"When it comes to actual results, <b>{wins_leader}</b> leads the pack with <b>{wins_leader_count} wins</b> "
         f"across its roster — proof that its kit deals are backed up by performances on the pitch."),
        ("The Underdog", underdog_brand,
         f"With just <b>{underdog_teams} team{'s' if underdog_teams != 1 else ''}</b> in the tournament, <b>{underdog_brand}</b> "
         f"is quietly posting a <b>{underdog_rate:.0f}% win rate</b> — punching well above its weight against manufacturers with "
         f"far bigger rosters."),
        ("Most Attacking", attack_brand,
         f"Teams wearing <b>{attack_brand}</b> are the tournament's most dangerous going forward, averaging "
         f"<b>{attack_value:.2f} goals per game</b> — the best strike rate of any kit supplier."),
        ("Tightest Defense", defense_brand,
         f"At the other end of the pitch, <b>{defense_brand}</b>-sponsored sides have been the hardest to break down, "
         f"conceding just <b>{defense_value:.2f} goals per game</b> on average."),
        ("Most Cards", dirty_brand,
         f"Referees have had their whistles busy around <b>{dirty_brand}</b>, whose teams have picked up "
         f"<b>{dirty_value} cards</b> combined — the most of any brand in the group stage."),
        ("Possession Kings", poss_brand,
         f"<b>{poss_brand}</b> teams like to keep the ball, averaging <b>{poss_value:.1f}% possession</b> — "
         f"the highest share of any manufacturer's roster."),
    ]
    story_chapters = [
        {"tag": tag, "logo_url": logo_url(brand), "color": BRAND_COLORS.get(brand, '#e8b34a'), "text": text}
        for tag, brand, text in story_chapters_raw
    ]
    story_outro = (
        f"No single brand owns every category — the giants trade blows across attack, defense, and discipline, "
        f"while smaller suppliers like {underdog_brand} prove that a shirt deal with fewer teams can still deliver "
        f"an outsized story."
    )

    # ---- Market Share ----
    brand_counts = pd.Series(KIT_MANUFACTURERS).value_counts().reset_index()
    brand_counts.columns = ['brand', 'teams']

    fig_teams_per_brand = bar_chart(brand_counts, 'brand', 'teams', 'Teams per Brand', color_series=brand_counts['brand'])

    fig_market_share = px.pie(brand_counts, names='brand', values='teams',
                               color='brand', color_discrete_map=BRAND_COLORS, hole=0.6)
    pulls = [0.05 if v == brand_counts['teams'].max() else 0 for v in brand_counts['teams']]
    fig_market_share.update_traces(
        textinfo='label+value', textposition='inside',
        textfont=dict(family='Inter', size=11, color='#fff'),
        marker=dict(line=dict(color='#0a0e1a', width=3)),
        pull=pulls,
        hovertemplate='<b>%{label}</b><br>%{value} teams (%{percent})<extra></extra>',
    )
    fig_market_share.update_layout(
        showlegend=False,
        annotations=[dict(
            text=f"<b>{brand_counts['teams'].sum()}</b><br><span style='font-size:10px;letter-spacing:2px;color:#c9a84c;'>TEAMS</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(family='Inter', size=26, color='#fff'),
        )],
    )
    apply_layout(fig_market_share, 'Kit Market Share')

    # ---- Results ----
    home_wins = dff[dff['winner'] != 'draw'].groupby('home_kit').apply(
        lambda x: (x['winner'] == x['home_team']).sum(), include_groups=False).reset_index(name='wins')
    home_wins.columns = ['brand', 'wins']
    away_wins = dff[dff['winner'] != 'draw'].groupby('away_kit').apply(
        lambda x: (x['winner'] == x['away_team']).sum(), include_groups=False).reset_index(name='wins')
    away_wins.columns = ['brand', 'wins']
    total_wins = pd.concat([home_wins, away_wins]).groupby('brand')['wins'].sum().reset_index()
    total_wins = reindex_brands(total_wins, 'wins')

    home_draws = dff[dff['winner'] == 'draw'].groupby('home_kit').size().reset_index(name='draws')
    home_draws.columns = ['brand', 'draws']
    away_draws = dff[dff['winner'] == 'draw'].groupby('away_kit').size().reset_index(name='draws')
    away_draws.columns = ['brand', 'draws']
    total_draws = pd.concat([home_draws, away_draws]).groupby('brand')['draws'].sum().reset_index()
    total_draws = reindex_brands(total_draws, 'draws')

    home_loss = dff[dff['winner'] != 'draw'].groupby('home_kit').apply(
        lambda x: (x['winner'] == x['away_team']).sum(), include_groups=False).reset_index(name='losses')
    home_loss.columns = ['brand', 'losses']
    away_loss = dff[dff['winner'] != 'draw'].groupby('away_kit').apply(
        lambda x: (x['winner'] == x['home_team']).sum(), include_groups=False).reset_index(name='losses')
    away_loss.columns = ['brand', 'losses']
    total_losses = pd.concat([home_loss, away_loss]).groupby('brand')['losses'].sum().reset_index()
    total_losses = reindex_brands(total_losses, 'losses')

    games_played = pd.concat([
        dff.groupby('home_kit').size().reset_index(name='games').rename(columns={'home_kit': 'brand'}),
        dff.groupby('away_kit').size().reset_index(name='games').rename(columns={'away_kit': 'brand'}),
    ]).groupby('brand')['games'].sum().reset_index()
    games_played = reindex_brands(games_played, 'games')

    win_rate = total_wins.merge(games_played, on='brand')
    win_rate['win_rate'] = (win_rate['wins'] / win_rate['games'] * 100).round(1)
    win_rate = win_rate.sort_values('win_rate', ascending=False)

    fig_wins = bar_chart(total_wins, 'brand', 'wins', 'Wins', color_series=total_wins['brand'])
    fig_draws = bar_chart(total_draws, 'brand', 'draws', 'Draws', color_series=total_draws['brand'])
    fig_losses = bar_chart(total_losses, 'brand', 'losses', 'Losses', color_series=total_losses['brand'])
    fig_win_rate = bar_chart(win_rate, 'brand', 'win_rate', 'Win Rate %',
                              text=win_rate['win_rate'], color_series=win_rate['brand'])

    # ---- Goals ----
    home_goals = dff.groupby('home_kit')['home_score'].sum().reset_index()
    home_goals.columns = ['brand', 'goals']
    away_goals = dff.groupby('away_kit')['away_score'].sum().reset_index()
    away_goals.columns = ['brand', 'goals']
    total_goals_df = pd.concat([home_goals, away_goals]).groupby('brand')['goals'].sum().reset_index()
    total_goals_df = reindex_brands(total_goals_df, 'goals')

    home_conc = dff.groupby('away_kit')['home_score'].sum().reset_index()
    home_conc.columns = ['brand', 'conceded']
    away_conc = dff.groupby('home_kit')['away_score'].sum().reset_index()
    away_conc.columns = ['brand', 'conceded']
    total_conc = pd.concat([home_conc, away_conc]).groupby('brand')['conceded'].sum().reset_index()
    total_conc = reindex_brands(total_conc, 'conceded')

    goals_pg = total_goals_df.merge(games_played, on='brand')
    goals_pg['goals_per_game'] = (goals_pg['goals'] / goals_pg['games']).round(2)
    goals_pg = goals_pg.sort_values('goals_per_game', ascending=False)

    fig_goals = bar_chart(total_goals_df, 'brand', 'goals', 'Goals Scored', color_series=total_goals_df['brand'])
    fig_conceded = bar_chart(total_conc, 'brand', 'conceded', 'Goals Conceded', color_series=total_conc['brand'])
    fig_goals_pg = bar_chart(goals_pg, 'brand', 'goals_per_game', 'Goals per Game',
                              text=goals_pg['goals_per_game'], color_series=goals_pg['brand'])

    # ---- Performance ----
    home_poss = dff.groupby('home_kit')['home_possession'].mean().reset_index()
    home_poss.columns = ['brand', 'possession']
    away_poss = dff.groupby('away_kit')['away_possession'].mean().reset_index()
    away_poss.columns = ['brand', 'possession']
    total_poss = pd.concat([home_poss, away_poss]).groupby('brand')['possession'].mean().reset_index()
    total_poss = reindex_brands(total_poss, 'possession')
    total_poss = total_poss.sort_values('possession', ascending=False)

    home_shots = dff.groupby('home_kit')[['home_sot', 'home_total_shots']].mean().reset_index()
    home_shots.columns = ['brand', 'sot', 'total_shots']
    away_shots = dff.groupby('away_kit')[['away_sot', 'away_total_shots']].mean().reset_index()
    away_shots.columns = ['brand', 'sot', 'total_shots']
    total_shots = pd.concat([home_shots, away_shots]).groupby('brand')[['sot', 'total_shots']].mean().reset_index()
    total_shots = total_shots.set_index('brand').reindex(ALL_BRANDS, fill_value=0).reset_index()
    total_shots = total_shots.sort_values('total_shots', ascending=False)
    total_shots_melted = total_shots.melt(id_vars='brand', value_vars=['sot', 'total_shots'],
                                           var_name='metric', value_name='value')

    home_saves = dff.groupby('home_kit')['home_saves'].mean().reset_index()
    home_saves.columns = ['brand', 'saves']
    away_saves = dff.groupby('away_kit')['away_saves'].mean().reset_index()
    away_saves.columns = ['brand', 'saves']
    total_saves = pd.concat([home_saves, away_saves]).groupby('brand')['saves'].mean().reset_index()
    total_saves = reindex_brands(total_saves, 'saves')
    total_saves = total_saves.sort_values('saves', ascending=False)

    shots_pg = total_shots[['brand', 'total_shots']].copy()
    shots_pg = shots_pg.sort_values('total_shots', ascending=False)

    fig_possession = bar_chart(total_poss, 'brand', 'possession', 'Possession Share',
                                text=total_poss['possession'].round(1), color_series=total_poss['brand'])

    fig_shots = px.bar(total_shots_melted, x='brand', y='value', color='metric',
                        text=total_shots_melted['value'].round(1), barmode='stack',
                        color_discrete_map={'sot': '#c9a84c', 'total_shots': '#4a6fa5'})
    fig_shots.update_traces(textposition='inside', marker_line_width=1,
                             marker_line_color='rgba(255,255,255,0.08)',
                             textfont=dict(family='Inter', size=13, color='#fff'),
                             hovertemplate='<b>%{x}</b><br>%{data.name}: %{y}<extra></extra>')
    fig_shots.update_layout(xaxis={'categoryorder': 'total descending'}, bargap=0.4, legend=dict(title=None))
    for trace, label in zip(fig_shots.data, ['Shots on Target', 'Total Shots']):
        trace.name = label
    apply_layout(fig_shots, 'Shots & Shots on Target')
    try:
        fig_shots.update_traces(marker_cornerradius=6)
    except Exception:
        pass
    rotate_xaxis_labels(fig_shots)

    fig_shots_pg = bar_chart(shots_pg, 'brand', 'total_shots', 'Shots per Game',
                              text=shots_pg['total_shots'].round(1), color_series=shots_pg['brand'])
    fig_saves = bar_chart(total_saves, 'brand', 'saves', 'Saves per Game',
                           text=total_saves['saves'].round(1), color_series=total_saves['brand'])

    # ---- Discipline ----
    home_cards = dff.groupby('home_kit')[['home_cards_yellow', 'home_cards_red']].sum().reset_index()
    home_cards.columns = ['brand', 'yellow', 'red']
    away_cards = dff.groupby('away_kit')[['away_cards_yellow', 'away_cards_red']].sum().reset_index()
    away_cards.columns = ['brand', 'yellow', 'red']
    total_cards = pd.concat([home_cards, away_cards]).groupby('brand')[['yellow', 'red']].sum().reset_index()
    total_cards = total_cards.set_index('brand').reindex(ALL_BRANDS, fill_value=0).reset_index()
    total_cards = total_cards.sort_values('yellow', ascending=False)
    total_cards_melted = total_cards.melt(id_vars='brand', value_vars=['yellow', 'red'],
                                           var_name='card_type', value_name='count')

    home_fouls = dff.groupby('home_kit')['home_fouls'].mean().reset_index()
    home_fouls.columns = ['brand', 'fouls']
    away_fouls = dff.groupby('away_kit')['away_fouls'].mean().reset_index()
    away_fouls.columns = ['brand', 'fouls']
    total_fouls = pd.concat([home_fouls, away_fouls]).groupby('brand')['fouls'].mean().reset_index()
    total_fouls = reindex_brands(total_fouls, 'fouls')
    total_fouls = total_fouls.sort_values('fouls', ascending=False)

    fig_cards = px.bar(total_cards_melted, x='brand', y='count', color='card_type',
                        text='count', barmode='group',
                        color_discrete_map={'yellow': '#c9a84c', 'red': '#e85d5d'})
    fig_cards.update_traces(textposition='outside', marker_line_width=1,
                             marker_line_color='rgba(255,255,255,0.08)',
                             textfont=dict(family='Inter', size=13, color='#fff'),
                             hovertemplate='<b>%{x}</b><br>%{data.name}: %{y}<extra></extra>')
    fig_cards.update_layout(xaxis={'categoryorder': 'total descending'}, bargap=0.4, legend=dict(title=None))
    for trace, label in zip(fig_cards.data, ['Yellow Cards', 'Red Cards']):
        trace.name = label
    apply_layout(fig_cards, 'Disciplinary Record')
    try:
        fig_cards.update_traces(marker_cornerradius=6)
    except Exception:
        pass
    rotate_xaxis_labels(fig_cards)

    fig_fouls = bar_chart(total_fouls, 'brand', 'fouls', 'Fouls Committed per Game',
                           text=total_fouls['fouls'].round(1), color_series=total_fouls['brand'])

    # ---- Brand vs Brand ----
    matchups = dff.groupby(['home_kit', 'away_kit']).size().reset_index(name='games')
    matchups_sym = pd.concat([
        matchups,
        matchups.rename(columns={'home_kit': 'away_kit', 'away_kit': 'home_kit'}),
    ]).groupby(['home_kit', 'away_kit'])['games'].sum().reset_index()
    matrix_games = matchups_sym.pivot(index='home_kit', columns='away_kit', values='games').fillna(0)

    home_wins_hm = dff[dff['winner'] != 'draw'].groupby(['home_kit', 'away_kit']).apply(
        lambda x: (x['winner'] == x['home_team']).sum(), include_groups=False).reset_index(name='wins')
    away_wins_hm = dff[dff['winner'] != 'draw'].groupby(['away_kit', 'home_kit']).apply(
        lambda x: (x['winner'] == x['away_team']).sum(), include_groups=False).reset_index(name='wins')
    away_wins_hm.columns = ['home_kit', 'away_kit', 'wins']
    total_wins_hm = pd.concat([home_wins_hm, away_wins_hm]).groupby(['home_kit', 'away_kit'])['wins'].sum().reset_index()
    matrix_wins = total_wins_hm.pivot(index='home_kit', columns='away_kit', values='wins').fillna(0)

    fig_matchups = go.Figure(data=go.Heatmap(
        z=matrix_games.values,
        x=matrix_games.columns.tolist(),
        y=matrix_games.index.tolist(),
        text=matrix_games.values.astype(int),
        texttemplate='%{text}',
        textfont=dict(family='Inter', size=11, color='#fff'),
        colorscale=[[0, '#0f1a2e'], [0.5, '#2d4f7a'], [1, '#75AADB']],
        showscale=False,
        xgap=3, ygap=3,
        hovertemplate='<b>%{y} vs %{x}</b><br>%{z} matches<extra></extra>',
    ))
    fig_matchups.update_layout(yaxis=dict(autorange='reversed', side='right'))
    apply_layout(fig_matchups, 'Head-to-Head Matchups')

    fig_win_record = go.Figure(data=go.Heatmap(
        z=matrix_wins.values,
        x=matrix_wins.columns.tolist(),
        y=matrix_wins.index.tolist(),
        text=matrix_wins.values.astype(int),
        texttemplate='%{text}',
        textfont=dict(family='Inter', size=11, color='#fff'),
        colorscale=[[0, '#0f1a2e'], [0.5, '#a33a3a'], [1, '#FF0000']],
        showscale=False,
        xgap=3, ygap=3,
        hovertemplate='<b>%{y} beat %{x}</b><br>%{z} wins<extra></extra>',
    ))
    fig_win_record.update_layout(yaxis=dict(autorange='reversed', side='right'))
    apply_layout(fig_win_record, 'Head-to-Head Win Record')

    # ---- Section insights (one summary per report page) ----
    top_win_rate = win_rate.iloc[0]
    top_shots_pg = total_shots.sort_values('total_shots', ascending=False).iloc[0]
    top_fouls = total_fouls.iloc[0]  # already sorted descending

    off_diag_games = matchups_sym[matchups_sym['home_kit'] != matchups_sym['away_kit']]
    top_matchup = off_diag_games.sort_values('games', ascending=False).iloc[0] if len(off_diag_games) else None

    off_diag_wins = total_wins_hm[total_wins_hm['home_kit'] != total_wins_hm['away_kit']]
    top_h2h = off_diag_wins.sort_values('wins', ascending=False).iloc[0] if len(off_diag_wins) else None

    chart_sections = [
        {
            "id": "market", "title": "Market Share",
            "charts": ["teams_per_brand", "market_share"],
            "insight": (
                f"<b>{leader_brand}</b> outfits more nations than any rival, dressing "
                f"<b>{leader_teams} of the {total_teams}</b> teams at the tournament — "
                f"the widest reach of any manufacturer before a ball was kicked."
            ),
        },
        {
            "id": "results", "title": "Results",
            "charts": ["wins", "draws", "losses", "win_rate"],
            "insight": (
                f"<b>{wins_leader}</b> has the most wins on the board ({wins_leader_count}), but "
                f"<b>{top_win_rate['brand']}</b> converts best on a per-game basis at "
                f"<b>{top_win_rate['win_rate']:.0f}%</b>."
            ),
        },
        {
            "id": "goals", "title": "Goals",
            "charts": ["goals", "conceded", "goals_pg"],
            "insight": (
                f"<b>{attack_brand}</b> sides are the most dangerous going forward at "
                f"<b>{attack_value:.2f} goals/game</b>, while <b>{defense_brand}</b> has been hardest "
                f"to break down, conceding just <b>{defense_value:.2f}</b> per game."
            ),
        },
        {
            "id": "performance", "title": "Performance",
            "charts": ["possession", "shots", "shots_pg", "saves"],
            "insight": (
                f"<b>{poss_brand}</b> teams dominate the ball at <b>{poss_value:.1f}%</b> possession, and "
                f"<b>{top_shots_pg['brand']}</b> generates the most shots per game of any manufacturer."
            ),
        },
        {
            "id": "discipline", "title": "Discipline",
            "charts": ["cards", "fouls"],
            "insight": (
                f"<b>{dirty_brand}</b> sides lead in cards picked up ({dirty_value} combined), while "
                f"<b>{top_fouls['brand']}</b> commits the most fouls per game of any brand."
            ),
        },
        {
            "id": "brandvbrand", "title": "Brand vs Brand",
            "charts": ["matchups", "win_record"],
            "insight": (
                (
                    f"<b>{top_matchup['home_kit']}</b> and <b>{top_matchup['away_kit']}</b> have crossed paths "
                    f"more than any other pair ({int(top_matchup['games'])} matches), and "
                    f"<b>{top_h2h['home_kit']}</b> holds the edge over <b>{top_h2h['away_kit']}</b> with "
                    f"{int(top_h2h['wins'])} head-to-head wins."
                ) if top_matchup is not None and top_h2h is not None else
                "Head-to-head data will fill in as more brands face off across the group stage."
            ),
        },
    ]

    charts = {
        "teams_per_brand": fig_json(fig_teams_per_brand),
        "market_share": fig_json(fig_market_share),
        "wins": fig_json(fig_wins),
        "draws": fig_json(fig_draws),
        "losses": fig_json(fig_losses),
        "win_rate": fig_json(fig_win_rate),
        "goals": fig_json(fig_goals),
        "conceded": fig_json(fig_conceded),
        "goals_pg": fig_json(fig_goals_pg),
        "possession": fig_json(fig_possession),
        "shots": fig_json(fig_shots),
        "shots_pg": fig_json(fig_shots_pg),
        "saves": fig_json(fig_saves),
        "cards": fig_json(fig_cards),
        "fouls": fig_json(fig_fouls),
        "matchups": fig_json(fig_matchups),
        "win_record": fig_json(fig_win_record),
    }

    return {
        "metrics": metrics,
        "champions": champions,
        "awards": awards,
        "story_chapters": story_chapters,
        "story_outro": story_outro,
        "total_matches": total_matches,
        "total_goals": total_goals,
        "total_brands": len(ALL_BRANDS),
        "chart_sections": chart_sections,
        "charts": charts,
    }


@app.route("/")
def index():
    data = build_dashboard()
    return render_template("index.html", **data)


if __name__ == "__main__":
    app.run(debug=True)