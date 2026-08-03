# 2026 World Cup — Kit Manufacturer Analysis (Flask version)

This is the Flask/HTML/CSS port of the original Streamlit dashboard. Same data,
same look, same charts — just served as a normal web page instead of a Streamlit app.

## How it's structured

```
flask_app/
├── app.py                  # Flask routes + all data/aggregation logic (ported 1:1 from the Streamlit script)
├── requirements.txt
├── templates/
│   └── index.html          # Jinja2 template — hero, awards, story report, chart grid
└── static/
    ├── css/style.css        # All the styling (ported from the Streamlit inline <style> block)
    ├── js/                  # (empty — chart rendering script is inline in index.html)
    └── assets/
        ├── logos/            # Brand logos: Nike.png, Adidas.png, Puma.png, etc.
        └── awards/            # champions.jpg, golden_ball.jpg, golden_boot.jpg, golden_glove.jpg, young_player.jpg
```

## How the charts work

`app.py` builds each Plotly figure exactly like the Streamlit version did, then serializes it
to JSON (`plotly.utils.PlotlyJSONEncoder`) and passes it to the template. `index.html` loads
Plotly.js from a CDN and calls `Plotly.newPlot(...)` for each chart in the browser — so the
charts are still fully interactive (hover, zoom, etc.), they're just rendered client-side
instead of server-side.

## Setup

```bash
pip install -r requirements.txt
```

Drop your images into:
- `static/assets/logos/{Brand}.png` — one per brand (must match the exact brand names used in `KIT_MANUFACTURERS`, e.g. `Nike.png`, `Adidas.png`)
- `static/assets/awards/champions.jpg`, `golden_ball.jpg`, `golden_boot.jpg`, `golden_glove.jpg`, `young_player.jpg`

Missing images degrade gracefully — cards just show without a background photo or logo instead of erroring.

## Run it

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

## Updating award winners

Same as before — edit the `AWARDS` dict near the top of `app.py`:

```python
AWARDS = {
    "champions": {"team_code": "ESP", "image": "assets/awards/champions.jpg"},
    "individual": [
        {"label": "Golden Ball", "team_code": "ESP", "image": "assets/awards/golden_ball.jpg"},
        ...
    ],
}
```

## Notes / differences from the Streamlit version

- **Caching**: the original used `st.cache_data`; this version caches the loaded dataframe in
  a module-level dict (`_data_cache`) so `kagglehub.dataset_download` only runs once per process.
  Restart the server to force a refresh.
- **Layout**: Streamlit's `st.columns()` / `st.container(border=True)` became plain CSS grid
  (`.grid.grid-2`, `.grid.grid-4`) and a `.card` class.
- **Images**: logos are served as real static files (`/static/assets/logos/...`) instead of
  base64 data URIs — lighter HTML and the browser can cache them.
- This is a single-file Flask app (no blueprints/database) since the dashboard has one page and
  one data source — easy to extend if you want to add routes later (e.g. `/api/charts` for AJAX
  refresh, or a filter form that reloads a subset of matches).
