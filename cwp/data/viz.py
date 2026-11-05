"""
cwp.data.viz — visualisations CWP : thème Plotly sombre, cartes OpenStreetMap (Leaflet/folium),
graphe de relations (vis-network), cartes HTML (profil, KPI, jauge).

Couleurs : palette catégorielle validée (contraste ≥ 3:1 sur le fond CWP #0a1a2a, séparation
daltonisme ΔE ≥ 8), statuts réservés aux niveaux de risque, toujours accompagnés d'un libellé.
"""
from __future__ import annotations

import html
import json

import pandas as pd

SURFACE = "#0a1a2a"
BG = "#050b14"
INK = "#cfe3f5"
INK2 = "#8aa4ba"
MUTED = "#52708a"
GRID = "#13293d"
CAT = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
STATUS = {"Faible": "#0ca30c", "Modéré": "#fab219", "Élevé": "#d03b3b"}
STATUS_ICON = {"Faible": "●", "Modéré": "▲", "Élevé": "■"}
# rampe séquentielle à une teinte (rouge), du fond vers le vif : « plus clair = plus de risque »
SEQ_RISK = [[0, "#1b2a38"], [0.25, "#4a2a30"], [0.5, "#83303a"], [0.75, "#c23d42"], [1, "#ff7a6e"]]
SEQ_BLUE = [[0, "#14304d"], [0.5, "#256abf"], [1, "#9ec5f4"]]
FONT = "Rajdhani, 'Segoe UI', sans-serif"


def theme(fig, height=420, legend=True, title=None):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family=FONT, color=INK, size=14), colorway=CAT,
        title=dict(text=title, font=dict(size=17, color=INK), x=0.01) if title else None,
        margin=dict(l=12, r=12, t=48 if title else 16, b=12), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK2), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#081626", bordercolor="#13405e", font=dict(family=FONT, color=INK)),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=INK2))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=INK2))
    return fig


# --------------------------------------------------------------------------- #
# Graphiques Plotly
# --------------------------------------------------------------------------- #
def world_risk_map(df: pd.DataFrame, col="score_risque", title="Score de risque pays (0–100)", height=520):
    import plotly.graph_objects as go
    d = df.copy()
    d[col] = pd.to_numeric(d[col], errors="coerce")
    hover = ("<b>%{customdata[0]}</b><br>Score : %{z:.0f}/100 · %{customdata[1]}"
             "<br>GAFI : %{customdata[2]}<br>Entités sanctionnées : %{customdata[3]}<extra></extra>")
    fig = go.Figure(go.Choropleth(
        locations=d.iso3, z=d[col], colorscale=SEQ_RISK, zmin=0, zmax=100, marker_line_color="#050b14",
        marker_line_width=0.4, customdata=d[["nom", "niveau", "gafi", "nb_entites_sanctionnees"]].values,
        hovertemplate=hover, colorbar=dict(title=dict(text="Score", font=dict(color=INK2)), thickness=10,
                                           tickfont=dict(color=INK2), len=0.7)))
    fig.update_geos(showframe=False, showcoastlines=False, bgcolor=SURFACE, landcolor="#0f2236",
                    showocean=True, oceancolor=BG, projection_type="natural earth", showcountries=True,
                    countrycolor="#050b14", lataxis_range=[-58, 84])
    return theme(fig, height=height, legend=False, title=title)


def bubble_map(counts: pd.DataFrame, title="Entités sanctionnées par pays", height=480):
    """counts : iso3, nom, n"""
    import plotly.graph_objects as go
    m = max(counts.n.max(), 1)
    fig = go.Figure(go.Scattergeo(
        locations=counts.iso3, text=counts.nom, mode="markers",
        marker=dict(size=(counts.n / m) ** 0.5 * 48 + 5, color=CAT[0], opacity=0.75,
                    line=dict(color=SURFACE, width=2)),
        customdata=counts.n, hovertemplate="<b>%{text}</b><br>%{customdata:,} entrées actives<extra></extra>"))
    fig.update_geos(showframe=False, bgcolor=SURFACE, landcolor="#0f2236", showocean=True, oceancolor=BG,
                    showcountries=True, countrycolor="#050b14", projection_type="natural earth",
                    lataxis_range=[-58, 84], showcoastlines=False)
    return theme(fig, height=height, legend=False, title=title)


def hbar(df, x, y, title=None, height=None, color=CAT[0], text=True):
    import plotly.graph_objects as go
    d = df.sort_values(x)
    fig = go.Figure(go.Bar(x=d[x], y=d[y], orientation="h", marker=dict(color=color, cornerradius=4),
                           text=d[x] if text else None, textposition="outside", textfont=dict(color=INK2),
                           hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>", cliponaxis=False))
    fig.update_layout(bargap=0.35)
    return theme(fig, height=height or max(260, 30 * len(d) + 70), legend=False, title=title)


def stacked_bar(df, x, y, color, title=None, height=380, order=None):
    import plotly.express as px
    fig = px.bar(df, x=x, y=y, color=color, color_discrete_sequence=CAT, category_orders={color: order} if order else None)
    fig.update_traces(marker_line_color=SURFACE, marker_line_width=2)
    fig.update_layout(bargap=0.3, barmode="stack")
    return theme(fig, height=height, title=title)


def line_trend(df, title="Inscriptions mensuelles sur les listes de sanctions", height=380):
    import plotly.graph_objects as go
    obs, prev = df[df.type == "observé"], df[df.type == "projection"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=obs.mois, y=obs.inscriptions, name="Observé", mode="lines",
                             line=dict(color=CAT[0], width=2), hovertemplate="%{x}<br>%{y:,} inscriptions<extra></extra>"))
    if not prev.empty:
        x = [obs.mois.iloc[-1]] + prev.mois.tolist()
        y = [obs.inscriptions.iloc[-1]] + prev.inscriptions.tolist()
        fig.add_trace(go.Scatter(x=x, y=y, name="Projection (régression)", mode="lines+markers",
                                 line=dict(color=CAT[1], width=2, dash="dot"), marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                                 hovertemplate="%{x}<br>≈ %{y:,.0f} (projection)<extra></extra>"))
    fig.update_layout(hovermode="x unified")
    return theme(fig, height=height, title=title)


def treemap(df, path, values, title=None, height=460):
    import plotly.express as px
    fig = px.treemap(df, path=path, values=values, color_discrete_sequence=CAT)
    fig.update_traces(marker=dict(line=dict(color=SURFACE, width=2)), textfont=dict(family=FONT),
                      hovertemplate="<b>%{label}</b><br>%{value:,} entrées<extra></extra>")
    return theme(fig, height=height, legend=False, title=title)


def scatter_segments(df, title="Carte de proximité des profils pays (ACP)", height=520):
    import plotly.express as px
    order = sorted(df.segment.unique())
    fig = px.scatter(df, x="acp_x", y="acp_y", color="segment", hover_name="nom", category_orders={"segment": order},
                     color_discrete_sequence=CAT, hover_data={"acp_x": False, "acp_y": False, "score_risque": True,
                                                              "gafi": True, "segment": False})
    fig.update_traces(marker=dict(size=10, line=dict(color=SURFACE, width=2)))
    for _, r in df.nlargest(12, "score_risque").iterrows():  # étiquettes sélectives : les plus risqués
        fig.add_annotation(x=r.acp_x, y=r.acp_y, text=r.nom, showarrow=False, yshift=12, font=dict(size=11, color=INK2))
    fig.update_xaxes(title="Composante 1", showticklabels=False)
    fig.update_yaxes(title="Composante 2", showticklabels=False)
    return theme(fig, height=height, title=title)


def heatmap(cm: pd.DataFrame, title="Matrice de confusion (validation croisée)", height=460):
    import plotly.graph_objects as go
    fig = go.Figure(go.Heatmap(z=cm.values, x=cm.columns, y=cm.index, colorscale=SEQ_BLUE, showscale=False,
                               text=cm.values, texttemplate="%{text}", textfont=dict(color=INK),
                               xgap=2, ygap=2, hovertemplate="Réel : %{y}<br>Prédit : %{x}<br>%{z}<extra></extra>"))
    fig.update_xaxes(title="Prédit", side="bottom")
    fig.update_yaxes(title="Réel", autorange="reversed")
    return theme(fig, height=height, legend=False, title=title)


def contributions_bar(contrib, height=None):
    import plotly.graph_objects as go
    if not contrib:
        return None
    d = pd.DataFrame(contrib, columns=["facteur", "points"]).sort_values("points")
    fig = go.Figure(go.Bar(x=d.points, y=d.facteur, orientation="h", marker=dict(color=CAT[1], cornerradius=4),
                           text=[f"+{p:g}" for p in d.points], textposition="outside", cliponaxis=False,
                           textfont=dict(color=INK2), hovertemplate="%{y}<br>+%{x} points<extra></extra>"))
    fig.update_xaxes(range=[0, max(70, d.points.max() * 1.25)], title="Points de risque")
    return theme(fig, height=height or 70 + 38 * len(d), legend=False, title="Facteurs du score (explicabilité)")


# --------------------------------------------------------------------------- #
# Cartes OpenStreetMap (Leaflet via folium)
# --------------------------------------------------------------------------- #
def osm_map(points: pd.DataFrame, center=None, zoom=None, color_col=None, label_col="nom",
            popup_cols=(), heat=False, height=540):
    """Carte Leaflet : fond sombre CARTO (données © OpenStreetMap) + couche OSM standard, regroupement,
    carte de chaleur optionnelle. Renvoie le HTML à afficher avec components.html."""
    import folium
    from folium.plugins import Fullscreen, HeatMap, MarkerCluster, MiniMap

    pts = points.dropna(subset=["lat", "lon"]).copy()
    pts = pts[(pts.lat.astype(str) != "") & (pts.lon.astype(str) != "")]
    pts["lat"], pts["lon"] = pts.lat.astype(float), pts.lon.astype(float)
    if center is None:
        center = [pts.lat.mean(), pts.lon.mean()] if len(pts) else [18.5, -72.3]
    m = folium.Map(location=center, zoom_start=zoom or (12 if len(pts) and pts.lat.std() < 0.3 else 3),
                   tiles=None, control_scale=True, prefer_canvas=True)
    folium.TileLayer("CartoDB dark_matter", name="Sombre (CARTO · OSM)").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap standard").add_to(m)
    folium.TileLayer("CartoDB positron", name="Clair (CARTO · OSM)").add_to(m)
    cats = list(dict.fromkeys(pts[color_col])) if color_col and color_col in pts else []
    cmap = {c: CAT[i % len(CAT)] for i, c in enumerate(cats)}
    groups = {}
    for c in cats or ["Points"]:
        fg = folium.FeatureGroup(name=f"{c}", show=True).add_to(m)
        groups[c] = MarkerCluster(options=dict(maxClusterRadius=40, showCoverageOnHover=False)).add_to(fg)
    for _, r in pts.iterrows():
        c = r[color_col] if cats else "Points"
        pop = "".join(f"<div><b>{html.escape(str(k))}</b> : {html.escape(str(r[k]))}</div>" for k in popup_cols
                      if k in r and str(r[k]))
        folium.CircleMarker(
            [r.lat, r.lon], radius=7, color="#0a1a2a", weight=2, fill=True, fill_color=cmap.get(c, CAT[0]),
            fill_opacity=0.95, tooltip=html.escape(str(r.get(label_col, "")) or str(c)),
            popup=folium.Popup(f"<div style='font-family:sans-serif;font-size:13px;min-width:180px'>"
                               f"<div style='font-weight:700;margin-bottom:4px'>{html.escape(str(r.get(label_col, '')))}</div>"
                               f"{pop}</div>", max_width=320)).add_to(groups[c])
    if heat and len(pts) > 3:
        HeatMap(pts[["lat", "lon"]].values.tolist(), name="Densité", radius=18, blur=22, show=False,
                gradient={0.3: "#256abf", 0.6: "#c98500", 1: "#e66767"}).add_to(m)
    if len(pts) > 1:
        m.fit_bounds([[pts.lat.min(), pts.lon.min()], [pts.lat.max(), pts.lon.max()]], padding=(30, 30))
    folium.LayerControl(collapsed=False).add_to(m)
    Fullscreen(position="topleft", title="Plein écran", title_cancel="Quitter").add_to(m)
    MiniMap(toggle_display=True, tile_layer="CartoDB dark_matter").add_to(m)
    if cats:
        items = "".join(f"<div style='margin:2px 0'><span style='display:inline-block;width:10px;height:10px;"
                        f"border-radius:50%;background:{cmap[c]};margin-right:6px'></span>{html.escape(str(c))}</div>"
                        for c in cats[:12])
        m.get_root().html.add_child(folium.Element(
            f"<div style='position:absolute;bottom:24px;left:12px;z-index:9999;background:#0a1a2aee;color:#cfe3f5;"
            f"border:1px solid #13405e;border-radius:10px;padding:8px 12px;font:13px sans-serif'>{items}</div>"))
    return m.get_root().render()


# --------------------------------------------------------------------------- #
# Graphe de relations (vis-network)
# --------------------------------------------------------------------------- #
GROUP_STYLE = {
    "entite": dict(color="#f5c542", shape="hexagon", size=34),
    "sanction": dict(color="#e66767", shape="diamond", size=20),
    "programme": dict(color="#9085e9", shape="dot", size=14),
    "pays": dict(color="#3987e5", shape="dot", size=16),
    "alias": dict(color="#52708a", shape="dot", size=10),
    "ppe": dict(color="#d55181", shape="star", size=20),
    "groupe": dict(color="#199e70", shape="square", size=18),
    "dirigeant": dict(color="#c98500", shape="triangle", size=14),
    "presse": dict(color="#d95926", shape="dot", size=11),
}
GROUP_LABEL = {"entite": "Entité analysée", "sanction": "Inscription sur liste", "programme": "Programme / régime",
               "pays": "Pays", "alias": "Alias", "ppe": "Fonction PPE", "groupe": "Lien de groupe (LEI)",
               "dirigeant": "Dirigeant", "presse": "Article de presse"}


def _txt(v) -> str:
    """Convertit en texte sûr (les valeurs manquantes pandas — NaN, None, NA — deviennent "")."""
    try:
        if v is None or pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "<na>", "nat") else s


def network_html(nodes: list[dict], edges: list[dict], height=560) -> str:
    """nodes : {id, label, group, title}; edges : {from, to, label}."""
    for n in nodes:
        n["id"] = _txt(n.get("id")) or f"n{id(n)}"
        n["label"] = _txt(n.get("label")) or "—"
        n["title"] = _txt(n.get("title")) or n["label"]
        n["group"] = _txt(n.get("group")) or "alias"
    edges = [dict(e, **{"from": _txt(e.get("from")), "to": _txt(e.get("to")), "label": _txt(e.get("label"))}) for e in edges]
    vn = [dict(id=n["id"], label=n["label"][:42], title=n["title"],
               **{k: v for k, v in GROUP_STYLE.get(n["group"], GROUP_STYLE["alias"]).items() if k != "color"},
               color=dict(background=GROUP_STYLE.get(n["group"], GROUP_STYLE["alias"])["color"], border="#0a1a2a",
                          highlight=dict(background="#ffffff", border="#f5c542")))
          for n in nodes]
    ve = [dict(**{"from": e["from"], "to": e["to"]}, label=e.get("label", ""), arrows="", width=1.5,
               color=dict(color="#2a4a66", highlight="#f5c542"), font=dict(color="#8aa4ba", size=11, strokeWidth=0))
          for e in edges]
    used = list(dict.fromkeys(n["group"] for n in nodes))
    legend = "".join(f"<span class='lg'><i style='background:{GROUP_STYLE[g]['color']}'></i>{GROUP_LABEL[g]}</span>"
                     for g in used if g in GROUP_STYLE)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/standalone/umd/vis-network.min.js"></script>
<style>body{{margin:0;background:{SURFACE};font-family:Rajdhani,'Segoe UI',sans-serif;color:{INK}}}
#g{{height:{height - 46}px;border:1px solid #13405e;border-radius:12px;background:radial-gradient(circle at 50% 40%,#0e2238,{SURFACE})}}
.bar{{display:flex;flex-wrap:wrap;gap:6px 14px;padding:8px 4px;font-size:13px;color:{INK2}}}
.lg i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}}</style></head>
<body><div class="bar">{legend}</div><div id="g"></div><script>
const nodes=new vis.DataSet({json.dumps(vn)});const edges=new vis.DataSet({json.dumps(ve)});
new vis.Network(document.getElementById('g'),{{nodes,edges}},{{
 nodes:{{font:{{color:'{INK}',size:14,face:'Rajdhani, Segoe UI, Arial, sans-serif',strokeWidth:3,strokeColor:'{SURFACE}'}},borderWidth:2}},
 interaction:{{hover:true,tooltipDelay:80,navigationButtons:false}},
 physics:{{solver:'forceAtlas2Based',forceAtlas2Based:{{gravitationalConstant:-60,springLength:110}},stabilization:{{iterations:220}}}}}});
</script></body></html>"""


def profile_graph(p: dict) -> tuple[list, list]:
    nodes, edges = [dict(id="E", label=p["nom"], group="entite", title=f"{p['nom']} · score {p['score']}/100")], []
    seen = {"E"}

    def add(id_, label, group, src="E", elabel="", title=None):
        id_, label, elabel, title = _txt(id_), _txt(label), _txt(elabel), _txt(title)
        if not label or id_.endswith("-"):
            return
        if id_ not in seen:
            nodes.append(dict(id=id_, label=label, group=group, title=title or label)); seen.add(id_)
        edges.append({"from": src, "to": id_, "label": elabel})

    if p.get("pays"):
        add(f"P-{p['pays']}", p.get("pays_nom") or p["pays"], "pays", elabel="pays")
    hits = p.get("hits", pd.DataFrame())
    for i, h in hits.head(12).iterrows() if not hits.empty else []:
        if h.liste == "PPE (Wikidata)":
            continue
        hid = f"H-{h.uid}"
        add(hid, f"{h.liste} — {h.nom}", "sanction", elabel=f"{h.score:.0f} %",
            title=f"{h.liste} · {h.nom} · correspondance {h.score:.0f} % ({h.niveau})")
        for prg in str(h.programme).split(" | ")[:3]:
            if prg:
                add(f"G-{prg}", prg, "programme", src=hid)
        for c in str(h.pays).split(" | ")[:3]:
            if c:
                from .countries import nom
                add(f"P-{c}", nom(c), "pays", src=hid)
        if h.nature == "alias":
            add(f"A-{h.variante}", h.variante, "alias", src=hid, elabel="alias")
    ppe = p.get("ppe_df", pd.DataFrame())
    for _, r in ppe.head(8).iterrows() if not ppe.empty else []:
        add(f"F-{r.get('fonction', '')}", r.get("fonction", "") or "Fonction publique", "ppe",
            elabel="en fonction" if r.get("en_fonction") == "oui" else "ancienne")
    if p.get("lei_parent"):
        add("L-parent", p["lei_parent"], "groupe", elabel="mère directe")
    if p.get("lei_parent_ultime") and p.get("lei_parent_ultime") != p.get("lei_parent"):
        add("L-ultime", p["lei_parent_ultime"], "groupe", elabel="mère ultime")
    for d in str(p.get("dirigeants", "")).split(" | ")[:8]:
        if d:
            add(f"D-{d}", d, "dirigeant", elabel="dirigeant")
    pr = p.get("presse", pd.DataFrame())
    for _, r in pr.head(6).iterrows() if not pr.empty else []:
        add(f"N-{r.uid}", f"{r.categorie} · {r.media}", "presse", elabel=r.date, title=r.titre)
    return nodes, edges


# --------------------------------------------------------------------------- #
# Blocs HTML (rendus avec st.markdown, stylés par CSS_EXTRA)
# --------------------------------------------------------------------------- #
CSS_EXTRA = """<style>
.kgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:6px 0 14px}
.kt{background:linear-gradient(135deg,#0a1f33,#0d1530);border:1px solid #13405e;border-radius:14px;padding:14px 16px;position:relative;overflow:hidden}
.kt:before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:var(--acc,#00d4ff)}
.kt .l{font-family:'Share Tech Mono';font-size:.68rem;letter-spacing:.14em;color:#8aa4ba;text-transform:uppercase}
.kt .v{font-family:'Share Tech Mono';font-size:1.9rem;color:#e8f4ff;line-height:1.15;margin-top:4px}
.kt .s{font-size:.85rem;color:#8aa4ba}
.pf{display:grid;grid-template-columns:220px 1fr;gap:20px;background:linear-gradient(120deg,#0b1d31,#0a1528 60%,#160f24);
    border:1px solid #13405e;border-radius:18px;padding:20px 24px;margin-bottom:14px}
@media(max-width:800px){.pf{grid-template-columns:1fr}}
.pf h2{margin:0;color:#e8f4ff!important;letter-spacing:.06em!important;font-size:1.9rem}
.pf .sub{font-family:'Share Tech Mono';color:#8aa4ba;font-size:.8rem;letter-spacing:.1em;margin:4px 0 10px;text-align:left}
.badge{display:inline-block;font-family:'Share Tech Mono';font-size:.75rem;padding:3px 10px;border-radius:20px;margin:0 6px 6px 0;border:1px solid}
.gauge{width:200px;height:200px;border-radius:50%;display:grid;place-items:center;margin:auto}
.gauge .in{width:150px;height:150px;border-radius:50%;background:#0a1a2a;display:grid;place-items:center;text-align:center}
.gauge .n{font-family:'Share Tech Mono';font-size:2.6rem;color:#e8f4ff;line-height:1}
.gauge .t{font-size:.95rem;font-weight:700;letter-spacing:.08em}
.fl{display:flex;justify-content:space-between;border-bottom:1px solid #12263a;padding:6px 0;font-size:.98rem}
.fl span:first-child{color:#8aa4ba}
.srcline{font-family:'Share Tech Mono';font-size:.7rem;color:#52708a;margin-top:8px}
.sect{font-family:'Share Tech Mono';font-size:.75rem;letter-spacing:.2em;color:#f5c542;border-bottom:1px solid #f5c54255;padding-bottom:6px;margin:18px 0 10px;text-transform:uppercase}
</style>"""


def kpis(items: list[tuple]) -> str:
    """items : (libellé, valeur, sous-titre, couleur d'accent)"""
    cells = "".join(f"<div class='kt' style='--acc:{a or '#00d4ff'}'><div class='l'>{html.escape(l)}</div>"
                    f"<div class='v'>{html.escape(str(v))}</div><div class='s'>{html.escape(s or '')}</div></div>"
                    for l, v, s, a in items)
    return f"<div class='kgrid'>{cells}</div>"


def badge(text, color):
    return f"<span class='badge' style='color:{color};border-color:{color}'>{html.escape(text)}</span>"


def profile_header(p: dict) -> str:
    col = STATUS.get(p["niveau"], "#8aa4ba")
    pct = p["score"]
    gauge = (f"<div class='gauge' style='background:conic-gradient({col} {pct * 3.6}deg,#13293d 0)'>"
             f"<div class='in'><div><div class='n'>{pct:.0f}</div><div class='t' style='color:{col}'>"
             f"{STATUS_ICON[p['niveau']]} RISQUE {p['niveau'].upper()}</div>"
             f"<div class='srcline'>sur 100</div></div></div></div>")
    from .countries import flag_emoji
    badges = badge(p["type"], "#00d4ff")
    if p.get("pays"):
        badges += badge(f"{flag_emoji(p['pays'])} {p.get('pays_nom', p['pays'])}", "#8aa4ba")
    for l in p["listes_touchees"]:
        badges += badge(f"⚠ {l}", "#e66767")
    if p["ppe"]:
        badges += badge("★ PPE" + (" en fonction" if p["ppe_en_fonction"] else ""), "#d55181")
    if p.get("pays_gafi") and p["pays_gafi"] != "Aucune":
        badges += badge(f"GAFI : {p['pays_gafi']}", "#fab219")
    if p["nb_presse_negative"]:
        badges += badge(f"📰 {p['nb_presse_negative']} article(s) négatif(s)", "#d95926")
    facts = [("Vigilance recommandée", p["vigilance"]),
             ("Meilleure correspondance sanctions", f"{p['meilleur_score_sanctions']:.0f} %" if p["meilleur_score_sanctions"] else "aucune"),
             ("Correspondances (sanctions + PPE)", len(p["hits"])),
             ("LEI", p.get("lei") or "—"), ("SIREN", p.get("siren") or "—"),
             ("Adresse", p.get("adresse") or (p.get("geo") or {}).get("label", "—") or "—"),
             ("Analyse du", p["date"])]
    rows = "".join(f"<div class='fl'><span>{html.escape(k)}</span><span>{html.escape(str(v))[:90]}</span></div>"
                   for k, v in facts)
    return (f"<div class='pf'>{gauge}<div><h2>{html.escape(p['nom'])}</h2>"
            f"<div class='sub'>PROFIL D'ENTITÉ · FILTRAGE SANCTIONS · PPE · PRESSE · REGISTRES · RISQUE PAYS</div>"
            f"{badges}<div style='margin-top:8px'>{rows}</div></div></div>")
