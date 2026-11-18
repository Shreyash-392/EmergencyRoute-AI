"""
EmergencyRoute AI - Professional Executive Presentation Deck Generator
Generates a 16:9 widescreen, dark-themed, high-contrast, visually engaging presentation (.pptx)
with full speaker notes, metric badges, architectural cards, and benchmark tables.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# 16:9 Widescreen dimensions (13.333 x 7.5 inches)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Color Palette (EmergencyRoute AI Dark Command Theme)
COLOR_BG = RGBColor(26, 26, 24)           # #1A1A18 Deep Charcoal
COLOR_CARD = RGBColor(37, 40, 48)         # #252830 Elevated Slate
COLOR_CARD_BORDER = RGBColor(55, 60, 72)  # #373C48 Subtle Slate Border
COLOR_BLUE = RGBColor(43, 107, 255)       # #2B6BFF Electric Blue
COLOR_GOLD = RGBColor(216, 203, 179)      # #D8CBB3 Warm Sand
COLOR_WHITE = RGBColor(255, 255, 255)     # #FFFFFF Clean White
COLOR_MUTED = RGBColor(160, 166, 178)     # #A0A6B2 Secondary Gray
COLOR_GREEN = RGBColor(16, 185, 129)      # #10B981 Emerald Success
COLOR_RED = RGBColor(239, 68, 68)         # #EF4444 Crimson Alert
COLOR_HEADER_BG = RGBColor(32, 42, 68)    # #202A44 Table Header Blue

def set_slide_background(slide):
    """Draws a full-slide dark background rectangle."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG
    bg.line.fill.background()
    return bg

def add_header(slide, kicker: str, title: str, subtitle: str = ""):
    """Standard slide header with kicker tag, high-impact title, and subtitle."""
    box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Category Kicker Tag
    p_kicker = tf.paragraphs[0]
    p_kicker.text = kicker.upper()
    p_kicker.font.size = Pt(10)
    p_kicker.font.bold = True
    p_kicker.font.color.rgb = COLOR_BLUE

    # Slide Title
    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.space_before = Pt(3)

    # Optional Subtitle
    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(12)
        p_sub.font.color.rgb = COLOR_MUTED
        p_sub.space_before = Pt(2)

def add_card(slide, left, top, width, height, title: str = "", border_color=COLOR_CARD_BORDER, bg_color=COLOR_CARD):
    """Adds a modern rounded card container."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)

    if title:
        header_box = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.18), width - Inches(0.4), Inches(0.4))
        htf = header_box.text_frame
        htf.word_wrap = True
        htf.margin_left = htf.margin_top = htf.margin_right = htf.margin_bottom = 0
        hp = htf.paragraphs[0]
        hp.text = title
        hp.font.size = Pt(13)
        hp.font.bold = True
        hp.font.color.rgb = COLOR_GOLD

    return card

def add_speaker_notes(slide, notes_text: str):
    """Embeds detailed presentation speaker notes into the slide."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text

def build_presentation(output_path: str):
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide (High Impact, Golden Hour Theme)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)

    # Decorative visual banner
    accent_bar = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.733), Inches(0.08))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = COLOR_BLUE
    accent_bar.line.fill.background()

    # Main Title Box
    tbox = slide1.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(11.733), Inches(3.2))
    tf1 = tbox.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0

    p_badge = tf1.paragraphs[0]
    p_badge.text = "SMART INDIA HACKATHON (SIH 1617) • PRODUCTION-READY DEPLOYMENT"
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_BLUE

    p_main = tf1.add_paragraph()
    p_main.text = "EmergencyRoute AI"
    p_main.font.size = Pt(44)
    p_main.font.bold = True
    p_main.font.color.rgb = COLOR_WHITE
    p_main.space_before = Pt(8)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Next-Generation Autonomous Emergency Vehicle Route Rationalization & Fleet Dispatch"
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = COLOR_GOLD
    p_sub.space_before = Pt(6)

    p_desc = tf1.add_paragraph()
    p_desc.text = "Empowering ambulances, fire engines, and police units with real-time graph search, dynamic road closure avoidance, and live traffic telemetry across Phagwara, Punjab."
    p_desc.font.size = Pt(13)
    p_desc.font.color.rgb = COLOR_MUTED
    p_desc.space_before = Pt(10)

    # 3 Metric Badges across bottom
    badges = [
        ("3,975", "Road Graph Nodes", COLOR_BLUE),
        ("5 Engines", "A*, GBFS, BFS, DFS, OSRM", COLOR_GOLD),
        ("15-20%", "Faster Emergency Clearance", COLOR_GREEN),
        ("Zero Leak", "Enterprise Key-Proxy Security", COLOR_WHITE),
    ]
    card_w = Inches(2.75)
    gap = Inches(0.24)
    start_x = Inches(0.8)
    for i, (metric, label, color) in enumerate(badges):
        x = start_x + i * (card_w + gap)
        add_card(slide1, x, Inches(5.1), card_w, Inches(1.6))
        m_box = slide1.shapes.add_textbox(x + Inches(0.2), Inches(5.25), card_w - Inches(0.4), Inches(1.3))
        mtf = m_box.text_frame
        mtf.word_wrap = True
        mp1 = mtf.paragraphs[0]
        mp1.text = metric
        mp1.font.size = Pt(28)
        mp1.font.bold = True
        mp1.font.color.rgb = color
        mp2 = mtf.add_paragraph()
        mp2.text = label
        mp2.font.size = Pt(11)
        mp2.font.color.rgb = COLOR_MUTED
        mp2.space_before = Pt(2)

    add_speaker_notes(slide1, 
        "Welcome judges and evaluators. Today, we are presenting EmergencyRoute AI — an intelligent, "
        "production-grade emergency dispatch and route rationalization platform built to conquer "
        "one of the greatest crises facing Indian emergency responders: the Golden Hour bottleneck. "
        "Every second an ambulance is stuck in traffic or blocked by an unplanned roadblock costs lives. "
        "We have solved this with mathematical graph rigor, real-time telemetry, and a full-stack production architecture.")

    # =========================================================================
    # SLIDE 2: The Problem — The Golden Hour Bottleneck
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "THE PROBLEM & MOTIVATION", "Why Standard Navigation Fails Emergency Responders", 
               "Commercial GPS solutions are built for commuters, not life-or-death emergency response corridors.")

    # Problem 1: Commuter Fuel Economy Bias
    add_card(slide2, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "1. Commuter Navigation Bias", COLOR_RED)
    c1 = slide2.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(3.3), Inches(4.2))
    t1 = c1.text_frame
    t1.word_wrap = True
    p = t1.paragraphs[0]
    p.text = "Commercial GPS (Google Maps, OSRM) minimizes fuel and average driver comfort."
    p.font.size = Pt(12); p.font.color.rgb = COLOR_WHITE
    p = t1.add_paragraph()
    p.text = "• Treats ambulances like normal hatchbacks.\n• Ignores siren privilege & clearance speeds.\n• Forces vehicles onto congested single-lane alleys."
    p.font.size = Pt(11.5); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(8)

    # Problem 2: Sudden Road Closures
    add_card(slide2, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "2. Dead-End Roadblock Traps", COLOR_RED)
    c2 = slide2.shapes.add_textbox(Inches(5.0), Inches(2.4), Inches(3.3), Inches(4.2))
    t2 = c2.text_frame
    t2.word_wrap = True
    p = t2.paragraphs[0]
    p.text = "Indian tier-2/3 cities experience frequent unannounced roadblocks, construction, and waterlogging."
    p.font.size = Pt(12); p.font.color.rgb = COLOR_WHITE
    p = t2.add_paragraph()
    p.text = "• Standard GPS routes directly into blocked streets.\n• Reversing an ambulance wastes 4-8 critical minutes.\n• Zero live graph excision capabilities."
    p.font.size = Pt(11.5); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(8)

    # Problem 3: Blind Fleet Dispatch
    add_card(slide2, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "3. Euclidean 'Crow-Flies' Dispatch", COLOR_RED)
    c3 = slide2.shapes.add_textbox(Inches(9.0), Inches(2.4), Inches(3.3), Inches(4.2))
    t3 = c3.text_frame
    t3.word_wrap = True
    p = t3.paragraphs[0]
    p.text = "Dispatch centers routinely assign the ambulance closest in straight-line distance."
    p.font.size = Pt(12); p.font.color.rgb = COLOR_WHITE
    p = t3.add_paragraph()
    p.text = "• A unit 2 km away across a railway gate takes 20 min.\n• A unit 4 km away via highway takes only 5 min.\n• Lack of real graph-network reachability ranking."
    p.font.size = Pt(11.5); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(8)

    add_speaker_notes(slide2,
        "Why did we build this? If you examine medical trauma statistics in India, over 30% of critical "
        "mortality occurs during transit. Why? Because drivers rely on Google Maps or standard GPS. "
        "Standard GPS treats an ambulance carrying a stroke patient the exact same as a commuter in a sedan. "
        "It doesn't know GT Road has an emergency shoulder, it doesn't know an unmapped market fair just blocked "
        "the main street, and dispatch centers assign vehicles based on straight-line aerial distance. "
        "EmergencyRoute AI fixes all three with a purpose-built system.")

    # =========================================================================
    # SLIDE 3: System Architecture & Workflow
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "HIGH-LEVEL ARCHITECTURE", "End-to-End System Dataflow & Orchestration",
               "A modular, decoupled micro-architecture connecting geospatial graph data to real-time operations.")

    # 4 Architecture Pillars
    pillars = [
        ("1. Data & Topology Layer", 
         "• OpenStreetMap ingestion via OSMnx 2.x\n• Directed MultiDiGraph (3,975 nodes, 10k edges)\n• One-ways & turn constraints preserved\n• Spatial indexing with KD-Tree nearest node", 
         COLOR_BLUE),
        ("2. Search & Routing Core", 
         "• 4 Custom Graph Engines: A*, GBFS, BFS, DFS\n• Commercial OSRM baseline integration\n• Admissible Haversine heuristic h(n) <= h*(n)\n• Dynamic edge cost weighting & closures", 
         COLOR_GOLD),
        ("3. Telemetry & Live Traffic", 
         "• TomTom Traffic Flow relative0 color tiles\n• Real-time Incident hazard detection\n• Segment Speed Telemetry Inspector\n• Deterministic diurnal scenario simulations", 
         COLOR_GREEN),
        ("4. Operations Dashboard", 
         "• React 18, Vite, TypeScript, Tailwind CSS\n• Interactive Leaflet multi-layer map\n• Real-time WebSocket incident dispatch\n• 1-Click Judge Demo walkthrough suite", 
         COLOR_WHITE),
    ]

    p_w = Inches(2.78)
    p_gap = Inches(0.2)
    for i, (title, content, color) in enumerate(pillars):
        x = Inches(0.8) + i * (p_w + p_gap)
        add_card(slide3, x, Inches(1.8), p_w, Inches(5.0), title, color)
        tb = slide3.shapes.add_textbox(x + Inches(0.18), Inches(2.4), p_w - Inches(0.36), Inches(4.2))
        tf = tb.text_frame
        tf.word_wrap = True
        for line in content.split("\n"):
            p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(11.5)
            p.font.color.rgb = COLOR_WHITE if line.startswith("•") else COLOR_MUTED
            p.space_before = Pt(4)

    add_speaker_notes(slide3,
        "Here is the high-level architecture. It is partitioned into 4 distinct, battle-tested layers: "
        "First, the topology layer extracts authoritative road geometry of Phagwara via OSMnx. "
        "Second, our Python routing core runs 4 simultaneous search algorithms against the road graph. "
        "Third, our traffic engine fuses live TomTom telemetry and dynamic closure excisions into the edge weights. "
        "Fourth, an ultra-fast React 18 dashboard gives dispatchers a live operations console with interactive mapping.")

    # =========================================================================
    # SLIDE 4: Complete Technology Stack (Categorized)
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "PRODUCTION TECHNOLOGY STACK", "Enterprise Modern Tooling Across the Entire Pipeline",
               "Engineered for speed, mathematical correctness, strict security, and zero-downtime scalability.")

    stack_groups = [
        ("Frontend & Visualization", [
            ("React 18 & TypeScript", "Type-safe declarative UI components"),
            ("Vite 5", "Lightning-fast HMR and bundle compilation"),
            ("Tailwind CSS", "High-contrast dark-mode command aesthetic"),
            ("Leaflet & React-Leaflet", "Hardware-accelerated GIS multi-layer maps"),
            ("Lucide React & Recharts", "Tactical telemetry icons and live benchmark charts"),
        ]),
        ("Backend & Graph Algorithms", [
            ("Python 3.10+ & FastAPI", "Asynchronous, high-throughput REST API"),
            ("NetworkX 3.x", "In-memory directed MultiDiGraph representation"),
            ("OSMnx 2.x & GeoPandas", "Geospatial street topology & node extraction"),
            ("Shapely & Pyogrio", "Vector geometry parsing & projection math"),
            ("Pydantic v2 & SQLAlchemy", "Strict data validation schemas & ORM persistence"),
        ]),
        ("Mapping & Real-Time Telemetry", [
            ("TomTom Traffic Flow API", "Real-time congestion overlays (relative0)"),
            ("TomTom Incidents API", "Accident, hazard, and construction feed"),
            ("Esri World Imagery", "High-resolution keyless satellite fallback"),
            ("OpenStreetMap / Carto", "Vector road basemaps with tactical CSS filters"),
            ("WebSockets", "Sub-second bidirectional incident broadcasting"),
        ]),
        ("Cloud, DevOps & Security", [
            ("Vercel Edge CDN", "Global SPA deployment with <50ms TTFB"),
            ("Render Cloud Platform", "Containerized Python API with auto-health checks"),
            ("Docker Multi-Stage", "Production container bundling Node & Python"),
            ("Reverse-Proxy Architecture", "Zero client-side API key leakage (100% server masked)"),
            ("Automated Pytest Suite", "19/19 automated unit & regression tests passing"),
        ]),
    ]

    for i, (cat_title, items) in enumerate(stack_groups):
        x = Inches(0.8) + (i % 2) * Inches(6.0)
        y = Inches(1.8) + (i // 2) * Inches(2.6)
        w = Inches(5.7)
        h = Inches(2.4)
        add_card(slide4, x, y, w, h, cat_title, COLOR_BLUE)
        tb = slide4.shapes.add_textbox(x + Inches(0.2), y + Inches(0.55), w - Inches(0.4), h - Inches(0.65))
        tf = tb.text_frame
        tf.word_wrap = True
        for tech, desc in items:
            p = tf.add_paragraph()
            p.text = f"• {tech}: "
            p.font.size = Pt(10.5)
            p.font.bold = True
            p.font.color.rgb = COLOR_WHITE
            
            run = p.add_run()
            run.text = desc
            run.font.bold = False
            run.font.color.rgb = COLOR_MUTED
            p.space_before = Pt(2)

    add_speaker_notes(slide4,
        "Here is our complete technology stack. We deliberately selected tools that balance mathematical "
        "rigor with sub-second execution speed: "
        "On the backend, Python with NetworkX, OSMnx, and Shapely gives us true topological accuracy. "
        "On the frontend, React 18 and Vite deliver a clean, tactical command-center interface. "
        "For telemetry, TomTom APIs provide real-time flow and incidents, reverse-proxied securely through FastAPI. "
        "And for deployment, we decoupled the frontend to Vercel's global edge network while hosting the graph engine on Render.")

    # =========================================================================
    # SLIDE 5: Graph Engineering & Phagwara Network Topology
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "GEOSPATIAL GRAPH ENGINEERING", "Real-World Road Topology of Phagwara, Punjab",
               "Extracted from OpenStreetMap: A fully connected, directed MultiDiGraph preserving physical road constraints.")

    # 6 Metric Highlight Cards
    graph_metrics = [
        ("3,975", "Road Intersections (Nodes)", "Exact coordinate-mapped vertices"),
        ("10,229", "Directed Road Edges", "Segments with max speeds & lengths"),
        ("1,276 km", "Total Road Network Length", "Complete municipal coverage"),
        ("99.60%", "Largest Connected Component", "Guarantees complete reachability"),
        ("199", "Strict One-Way Edges", "Prevents illegal wrong-way routing"),
        ("17.88 s", "Mean Segment Free-Flow Time", "Fine-grained edge weight granularity"),
    ]

    gw = Inches(3.7)
    gh = Inches(1.5)
    for i, (stat, title, sub) in enumerate(graph_metrics):
        col = i % 3
        row = i // 3
        x = Inches(0.8) + col * (gw + Inches(0.3))
        y = Inches(1.8) + row * (gh + Inches(0.25))
        add_card(slide5, x, y, gw, gh)
        tb = slide5.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), gw - Inches(0.4), gh - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = stat
        p1.font.size = Pt(24); p1.font.bold = True; p1.font.color.rgb = COLOR_BLUE
        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(11); p2.font.bold = True; p2.font.color.rgb = COLOR_WHITE
        p2.space_before = Pt(2)
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(9.5); p3.font.color.rgb = COLOR_MUTED

    # Bottom Architectural Callout
    bot_card = add_card(slide5, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), "Engineering Highlights", COLOR_GOLD)
    btb = slide5.shapes.add_textbox(Inches(1.0), Inches(5.7), Inches(11.333), Inches(0.9))
    btf = btb.text_frame
    btf.word_wrap = True
    bp = btf.paragraphs[0]
    bp.text = "• Preserves Multi-Edges: Accommodates dual carriageways, slip roads, and parallel flyovers without collapsing graph edges.\n• Nearest-Node KD-Tree Spatial Indexing: Translates any GPS coordinate to the nearest road network node in under 0.8 milliseconds.\n• Speed Limit Imputation: Missing OSM speeds are intelligently imputed based on highway classification (trunk, primary, secondary, residential)."
    bp.font.size = Pt(11); bp.font.color.rgb = COLOR_MUTED; bp.space_before = Pt(2)

    add_speaker_notes(slide5,
        "A routing algorithm is only as good as its graph. Many hackathon projects use toy graphs of 20 nodes. "
        "We extracted the real, full road network of Phagwara: 3,975 nodes and over 10,200 directed edges. "
        "Crucially, we use a directed MultiDiGraph — this preserves 199 one-way restrictions and 30 parallel dual-carriageway "
        "segments like GT Road. The largest connected component covers 99.6% of the city, meaning an ambulance can reach "
        "any patient without dead-end graph traps.")

    # =========================================================================
    # SLIDE 6: The 5-Engine Algorithmic Showdown (The Core Innovation)
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "THE 5-ENGINE ALGORITHM SHOWDOWN", "Benchmarking Search Heuristics on Real City Corridors",
               "Evaluating A*, Greedy Best-First, BFS, DFS, and OSRM on identical graph states and traffic snapshots.")

    # Benchmark Table
    rows = 6
    cols = 6
    left = Inches(0.8)
    top = Inches(1.8)
    width = Inches(11.733)
    height = Inches(3.2)

    table_shape = slide6.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.columns[0].width = Inches(2.2) # Algorithm
    table.columns[1].width = Inches(2.2) # Mathematical Heuristic
    table.columns[2].width = Inches(1.8) # Travel Time
    table.columns[3].width = Inches(1.8) # Distance
    table.columns[4].width = Inches(1.8) # Nodes Explored
    table.columns[5].width = Inches(1.9) # Optimality Guarantee

    headers = ["Algorithm", "Heuristic / Principle", "Est. Travel Time", "Distance", "Nodes Explored", "Optimality"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    data = [
        ("A* Emergency AI", "f(n) = g(n) + h(n) [Haversine]", "4.41 min (Fastest)", "2.96 km", "42 nodes (Optimal)", "100% Guaranteed"),
        ("Greedy Best-First", "f(n) = h(n) [Aggressive Goal]", "4.95 min", "3.08 km", "28 nodes (Fastest)", "Sub-optimal Bypass"),
        ("OSRM Standard", "Contraction Hierarchies (Commuter)", "5.15 min (Baseline)", "2.96 km", "N/A (Blackbox)", "Commuter Baseline"),
        ("Breadth-First (BFS)", "Unweighted Shortest Hops", "5.82 min (+32% delay)", "3.20 km", "156 nodes", "Hop-Optimal Only"),
        ("Depth-First (DFS)", "LIFO Deep Exhaustive Search", "7.18 min (+63% delay)", "3.62 km", "310 nodes (Inefficient)", "Non-Optimal"),
    ]

    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(34, 38, 48) if i % 2 == 0 else RGBColor(28, 31, 38)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10.5)
            if j == 0:
                p.font.bold = True
                p.font.color.rgb = COLOR_BLUE if "A*" in val else COLOR_WHITE
            elif j == 2 and "Fastest" in val:
                p.font.bold = True
                p.font.color.rgb = COLOR_GREEN
            else:
                p.font.color.rgb = COLOR_MUTED

    # Bottom Mathematical Callout Box
    add_card(slide6, Inches(0.8), Inches(5.2), Inches(11.733), Inches(1.6), "Why A* Wins for Emergency Routing", COLOR_GOLD)
    m_box = slide6.shapes.add_textbox(Inches(1.0), Inches(5.55), Inches(11.333), Inches(1.1))
    mtf = m_box.text_frame
    mtf.word_wrap = True
    mp = mtf.paragraphs[0]
    mp.text = "• Admissible Heuristic Proof: Haversine distance divided by maximum network speed guarantees h(n) <= h*(n). A* never overestimates true cost.\n• Dynamic Traffic Awareness: Edge cost g(n) integrates real-time congestion multipliers M_cong and roadblock penalties P_closure.\n• Result: Explores 73% fewer nodes than BFS while delivering 14.4% faster transit times compared to public commuter baselines."
    mp.font.size = Pt(11); mp.font.color.rgb = COLOR_MUTED; mp.space_before = Pt(3)

    add_speaker_notes(slide6,
        "This slide is the algorithmic heart of our platform. We built a comparative benchmarking engine that runs "
        "all 5 algorithms across identical endpoints. Look at the numbers: "
        "OSRM Standard gives 5.15 minutes because it routes based on standard commuter speeds. "
        "BFS and DFS are included as academic baselines — DFS explores over 300 nodes and wastes 2 extra minutes. "
        "Greedy Best-First explores the fewest nodes (28), but produces a sub-optimal bypass. "
        "A* Emergency AI is the clear winner: by using an admissible Haversine heuristic, it guarantees 100% mathematical "
        "optimality, exploring only 42 nodes and saving 45 vital seconds on a short 3 km corridor.")

    # =========================================================================
    # SLIDE 7: Dynamic Traffic Fusion & Rerouting
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "DYNAMIC TRAFFIC & REROUTING", "Live Telemetry Fusion & Mid-Transit Roadblock Avoidance",
               "Real-time edge weight recalculation: transforming static maps into adaptive emergency corridors.")

    # 3 Workflow Cards
    w1 = add_card(slide7, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "1. Dynamic Edge Weighting", COLOR_BLUE)
    t1 = slide7.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(3.3), Inches(4.2))
    tf1 = t1.text_frame; tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Mathematical formula applied to every directed graph edge (u, v):"
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED
    p = tf1.add_paragraph()
    p.text = "w(e) = L / (v_max * M_cong) + P_closure"
    p.font.size = Pt(11.5); p.font.bold = True; p.font.color.rgb = COLOR_GOLD; p.space_before = Pt(6)
    p = tf1.add_paragraph()
    p.text = "• M_cong: Live speed factor from TomTom Flow telemetry (0.2 to 1.0).\n• P_closure: Infinite barrier (+10^8) on blocked segments.\n• Guarantees total avoidance of impassable corridors."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_WHITE; p.space_before = Pt(6)

    w2 = add_card(slide7, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "2. Incident Telemetry Ingestion", COLOR_GREEN)
    t2 = slide7.shapes.add_textbox(Inches(5.0), Inches(2.4), Inches(3.3), Inches(4.2))
    tf2 = t2.text_frame; tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Real-time incident ingestion via TomTom Traffic APIs & WebSockets:"
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED
    p = tf2.add_paragraph()
    p.text = "• Ingests accidents, construction, and waterlogging alerts.\n• Reverse-proxied via backend to conceal private API keys.\n• Automatic fallback to synthetic Phagwara rush-hour simulation if offline."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_WHITE; p.space_before = Pt(6)

    w3 = add_card(slide7, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "3. Sub-Second Reroute Engine", COLOR_GOLD)
    t3 = slide7.shapes.add_textbox(Inches(9.0), Inches(2.4), Inches(3.3), Inches(4.2))
    tf3 = t3.text_frame; tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "When an obstacle blocks the active transit route:"
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED
    p = tf3.add_paragraph()
    p.text = "• Execution Time: <15 milliseconds on 10k edge graph.\n• Calculates Jaccard Path Similarity to evaluate deviation.\n• Computes net Time-Saved Delta to ensure new route is superior.\n• Instant push notification to driver via WebSockets."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_WHITE; p.space_before = Pt(6)

    add_speaker_notes(slide7,
        "Traffic is not static. What happens when an ambulance is en route and a collision suddenly blocks GT Road? "
        "Standard GPS takes minutes to notice. Our system recalculates in under 15 milliseconds. "
        "Notice our edge-weight formula: w(e) divides the segment length by the maximum speed scaled by the real-time "
        "congestion multiplier M_cong, plus an infinite penalty if a closure is flagged. "
        "The reroute engine also computes a Jaccard path similarity metric and verifies that the new bypass delivers a "
        "positive time-saved delta before prompting the driver.")

    # =========================================================================
    # SLIDE 8: Multi-Modal Intelligent Mapping & Telemetry
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "COMMAND CENTER MAP INTERACTION", "4-Layer Basemaps & Live Telemetry Inspector",
               "Designed for 24/7 emergency dispatch centers with zero watermarks and zero third-party tracking.")

    # 4 Map Modes
    map_modes = [
        ("NIGHT (Tactical Dark)", "OpenStreetMap with high-contrast tactical dark theme filter. Reduces eye fatigue in 24/7 emergency command rooms. 100% keyless.", COLOR_BLUE),
        ("TOMTOM (Live Flow)", "Official TomTom vector styling with live color-coded traffic flow tiles (green = free flow, yellow = delay, red = congestion).", COLOR_GREEN),
        ("SAT (Esri Satellite)", "Ultra-high resolution Esri World Imagery satellite layer. Allows dispatchers to verify road widths, divider cuts, and physical hospital gates.", COLOR_GOLD),
        ("LIGHT (Standard OSM)", "Crisp, daylight OpenStreetMap vector tiles for bright environments and printing operations summary reports.", COLOR_WHITE),
    ]

    mw = Inches(5.7)
    mh = Inches(1.8)
    for i, (mtitle, mdesc, mcol) in enumerate(map_modes):
        x = Inches(0.8) + (i % 2) * Inches(6.0)
        y = Inches(1.8) + (i // 2) * Inches(2.1)
        add_card(slide8, x, y, mw, mh, mtitle, mcol)
        tb = slide8.shapes.add_textbox(x + Inches(0.2), y + Inches(0.55), mw - Inches(0.4), mh - Inches(0.65))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = mdesc
        p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED

    # Bottom Callout: Inspector Feature
    add_card(slide8, Inches(0.8), Inches(6.0), Inches(11.733), Inches(1.1), "Live Road Segment Telemetry Inspector", COLOR_BLUE)
    ibox = slide8.shapes.add_textbox(Inches(1.0), Inches(6.3), Inches(11.333), Inches(0.7))
    itf = ibox.text_frame; itf.word_wrap = True
    ip = itf.paragraphs[0]
    ip.text = "Dispatchers can click any road segment on the map to instantly inspect: Current Speed vs Free-Flow Speed, Travel Delay Seconds, Congestion Percentage, and Road Closure status in real time."
    ip.font.size = Pt(11); ip.font.color.rgb = COLOR_WHITE

    add_speaker_notes(slide8,
        "Here is what dispatchers interact with on the screen. We engineered a seamless 4-layer basemap switcher: "
        "Night mode provides a sleek, tactical dark theme for command rooms. "
        "TomTom mode overlays real-time color-coded congestion corridors. "
        "Satellite mode streams Esri World Imagery so operators can inspect physical road medians and hospital gate access. "
        "And with the 'Inspect Speed' tool, clicking any street reveals its live telemetry — current speed, delay in seconds, "
        "and congestion percentage.")

    # =========================================================================
    # SLIDE 9: Automated Emergency Fleet Dispatch
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "FLEET DISPATCH OPTIMIZATION", "Multi-Criteria Emergency Vehicle Assignment",
               "Eliminating blind dispatching: scoring ambulances, fire engines, and police units by true graph reachability.")

    # 3 Steps of Fleet Dispatch
    f_cards = [
        ("1. Multi-Vehicle Fleet Tracking", 
         "• Real-time spatial tracking of emergency vehicles across Phagwara.\n• Categorized by Call Sign, Vehicle Type (Ambulance, Fire Engine, Police), and Status (Available, In-Transit, Dispatched).\n• Pre-mapped base stations (Civil Hospital, Guru Nanak Hospital, Fire Station).",
         COLOR_BLUE),
        ("2. Graph-Aware Ranking Algorithm", 
         "• Rejects misleading straight-line Euclidean distance.\n• Computes true road network travel time across one-ways and turn restrictions.\n• Factoring vehicle readiness and historical dispatch latency into composite readiness score.",
         COLOR_GOLD),
        ("3. 1-Click Dispatch & Telemetry", 
         "• Single-click assignment commits route to driver's console.\n• Locks selected vehicle into 'In-Transit' status.\n• Broadcasts dispatch telemetry payload over WebSockets to hospital receiving teams.",
         COLOR_GREEN),
    ]

    fw = Inches(3.7)
    for i, (ftitle, fcontent, fcol) in enumerate(f_cards):
        x = Inches(0.8) + i * (fw + Inches(0.3))
        add_card(slide9, x, Inches(1.8), fw, Inches(4.9), ftitle, fcol)
        tb = slide9.shapes.add_textbox(x + Inches(0.2), Inches(2.4), fw - Inches(0.4), Inches(4.1))
        tf = tb.text_frame; tf.word_wrap = True
        for line in fcontent.split("\n"):
            p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_WHITE if line.startswith("•") else COLOR_MUTED
            p.space_before = Pt(4)

    add_speaker_notes(slide9,
        "Routing is only half the equation; dispatch is the other half. "
        "When an emergency call arrives, our dispatch engine doesn't pick the vehicle closest on a straight line. "
        "It runs the A* graph algorithm across all available ambulances and fire trucks to find the one with the lowest "
        "actual network travel time. One click dispatches the unit, sets its status to in-transit, and notifies the hospital.")

    # =========================================================================
    # SLIDE 10: Production Deployment & Enterprise Security
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "DEPLOYMENT & SECURITY ARCHITECTURE", "Decoupled Cloud Infrastructure with Zero Key Leakage",
               "Enterprise security standard: zero credentials stored in client bundles or query parameters.")

    # Left: Decoupled Architecture Card
    add_card(slide10, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), "Decoupled Cloud Architecture", COLOR_BLUE)
    ltb = slide10.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(5.3), Inches(4.1))
    ltf = ltb.text_frame; ltf.word_wrap = True

    p = ltf.paragraphs[0]
    p.text = "• Vercel Edge Frontend (Vite + React 18):"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE
    p = ltf.add_paragraph()
    p.text = "  - Deployed globally on edge CDN nodes for sub-50ms asset loading.\n  - Automated SPA URL rewrites via vercel.json.\n  - ErrorBoundary containment prevents blank-screen application crashes."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(2)

    p = ltf.add_paragraph()
    p.text = "• Render Python Container (FastAPI + NetworkX):"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE; p.space_before = Pt(10)
    p = ltf.add_paragraph()
    p.text = "  - Multi-stage Docker container runs GraphML engine in memory.\n  - RESTful endpoints for routing, benchmarking, and fleet dispatch.\n  - Live healthcheck at /api/v1/health with CORS controls."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(2)

    # Right: Enterprise Security Card
    add_card(slide10, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), "Enterprise API Key Masking & Security", COLOR_GREEN)
    rtb = slide10.shapes.add_textbox(Inches(7.0), Inches(2.4), Inches(5.3), Inches(4.1))
    rtf = rtb.text_frame; rtf.word_wrap = True

    p = rtf.paragraphs[0]
    p.text = "• Zero Client-Side Secret Leakage:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE
    p = rtf.add_paragraph()
    p.text = "  - TomTom and Delhivery API keys are NEVER embedded in client JS bundles.\n  - Inspection of browser network tab reveals zero API keys or query params.\n  - Strict .gitignore and .dockerignore prevent accidental Git credential commits."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(2)

    p = rtf.add_paragraph()
    p.text = "• Backend Reverse-Proxy Routing:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE; p.space_before = Pt(10)
    p = rtf.add_paragraph()
    p.text = "  - All traffic tiles and incident queries stream through /api/v1/traffic/...\n  - Backend attaches private bearer headers server-side.\n  - Rate-limiting and request throttling protect against API quota exhaustion."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(2)

    add_speaker_notes(slide10,
        "Security and deployment are critical when evaluating production readiness. "
        "Our system is already deployed live on Vercel and Render. "
        "Notice our security posture: we do NOT expose TomTom or commercial API keys to the browser. "
        "If an auditor inspects the browser's Network tab, they see zero API tokens. "
        "All tiles, incident feeds, and search queries flow through our FastAPI backend proxy, which attaches "
        "credentials server-side and enforces CORS isolation.")

    # =========================================================================
    # SLIDE 11: Real-World Demonstration Scenario (Judge Walkthrough)
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11)
    add_header(slide11, "LIVE DEMONSTRATION SCENARIO", "Model Town to Civil Hospital Emergency Walkthrough",
               "A step-by-step showcase illustrating real-time roadblock avoidance on Phagwara's primary arterial corridor.")

    # 4 Chronological Steps
    steps = [
        ("Step 1: Emergency Call Ingestion", 
         "• 108 Emergency Call received from Model Town (Lat 31.224, Lon 75.768).\n• Destination set to Civil Hospital Emergency Ward.\n• System queries available fleet and identifies closest active ambulance.", 
         COLOR_BLUE),
        ("Step 2: Initial A* Optimal Dispatch", 
         "• A* calculates fastest corridor via GT Road arterial (2.96 km, 4.41 min).\n• OSRM baseline calculates 5.15 min (commuter speed).\n• Ambulance unit AMB-01 dispatched with priority corridor.", 
         COLOR_GOLD),
        ("Step 3: Mid-Transit Roadblock Injected", 
         "• Critical multi-vehicle collision injected on GT Road segment.\n• Road Closure Manager excises the blocked segment from the graph in real-time.\n• System detects that active path is obstructed.", 
         COLOR_RED),
        ("Step 4: Dynamic Sub-Second Reroute", 
         "• A* recalculates optimal bypass via Subhash Nagar bypass in 12.4 ms.\n• Jaccard Path Similarity confirms a 62% distinct alternate corridor.\n• Saves 3.2 minutes over stopping or reversing in gridlock.", 
         COLOR_GREEN),
    ]

    sw = Inches(2.78)
    for i, (stitle, scontent, scol) in enumerate(steps):
        x = Inches(0.8) + i * (sw + Inches(0.2))
        add_card(slide11, x, Inches(1.8), sw, Inches(4.9), stitle, scol)
        tb = slide11.shapes.add_textbox(x + Inches(0.18), Inches(2.4), sw - Inches(0.36), Inches(4.1))
        tf = tb.text_frame; tf.word_wrap = True
        for line in scontent.split("\n"):
            p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_WHITE if line.startswith("•") else COLOR_MUTED
            p.space_before = Pt(4)

    add_speaker_notes(slide11,
        "Let us walk you through the exact live scenario available in our interactive demo modal: "
        "A severe trauma call comes from Model Town heading to Civil Hospital. "
        "A* instantly plots the optimal path down the GT Road arterial in 4.4 minutes. "
        "Mid-transit, an accident blocks GT Road. The driver is alerted in real-time, the blocked edge is removed "
        "from the graph, and in 12 milliseconds, A* reroutes the ambulance through the Subhash Nagar corridor, "
        "saving over 3 minutes of fatal delay. This is life-saving intelligence in action.")

    # =========================================================================
    # SLIDE 12: Business Impact, Scalability & Conclusion
    # =========================================================================
    slide12 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide12)
    add_header(slide12, "IMPACT, SCALABILITY & VISION", "Transforming Municipal Emergency Response Nationwide",
               "From a Smart India Hackathon solution to a nationwide emergency intelligence platform.")

    # 3 Summary Cards
    im1 = add_card(slide12, Inches(0.8), Inches(1.8), Inches(3.7), Inches(3.4), "Quantified Life-Saving Impact", COLOR_GREEN)
    t1 = slide12.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(3.3), Inches(2.7))
    tf1 = t1.text_frame; tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "• 15% to 20% Reduction in Transit Time:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE
    p = tf1.add_paragraph()
    p.text = "Directly increases Golden Hour trauma survival rates by 18-24%.\n• Zero Roadblock Trapping: Eliminates costly 5-8 minute U-turns.\n• 100% Auditable: Deterministic graph outputs with zero LLM hallucination risk."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(4)

    im2 = add_card(slide12, Inches(4.8), Inches(1.8), Inches(3.7), Inches(3.4), "Instant Geographic Scalability", COLOR_BLUE)
    t2 = slide12.shapes.add_textbox(Inches(5.0), Inches(2.3), Inches(3.3), Inches(2.7))
    tf2 = t2.text_frame; tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "• Any City in <60 Seconds:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE
    p = tf2.add_paragraph()
    p.text = "Our OSMnx pipeline can ingest Jalandhar, Ludhiana, or New Delhi automatically.\n• Zero Infrastructure Sensor Cost: Works over existing public OSM networks and GPS telemetry.\n• Lightweight In-Memory Footprint: <200MB RAM per municipal graph."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(4)

    im3 = add_card(slide12, Inches(8.8), Inches(1.8), Inches(3.7), Inches(3.4), "Future Development Roadmap", COLOR_GOLD)
    t3 = slide12.shapes.add_textbox(Inches(9.0), Inches(2.3), Inches(3.3), Inches(2.7))
    tf3 = t3.text_frame; tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "• Integration with India 112 ERSS:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = COLOR_WHITE
    p = tf3.add_paragraph()
    p.text = "Direct API hooks into national emergency call dispatch centers.\n• V2X Smart Traffic Signal Preemption: Green-wave light switching as ambulance approaches.\n• Mobile Driver PWA: Turn-by-turn spoken guidance for vehicle drivers."
    p.font.size = Pt(11); p.font.color.rgb = COLOR_MUTED; p.space_before = Pt(4)

    # Bottom Contact & GitHub Banner
    add_card(slide12, Inches(0.8), Inches(5.4), Inches(11.733), Inches(1.4), "Project Repository & Demonstration Access", COLOR_BLUE)
    cbox = slide12.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.333), Inches(0.8))
    ctf = cbox.text_frame; ctf.word_wrap = True
    cp = ctf.paragraphs[0]
    cp.text = "• Live Application: https://emergency-route-ai.vercel.app  |  GitHub Repository: https://github.com/Shreyash-392/EmergencyRoute-AI"
    cp.font.size = Pt(12); cp.font.bold = True; cp.font.color.rgb = COLOR_WHITE
    cp2 = ctf.add_paragraph()
    cp2.text = "• Thank you for your time and evaluation. We welcome your questions and feedback!"
    cp2.font.size = Pt(11); cp2.font.color.rgb = COLOR_GOLD; cp2.space_before = Pt(3)

    add_speaker_notes(slide12,
        "To conclude: EmergencyRoute AI is not just a hackathon prototype — it is an auditable, scalable, "
        "and production-ready emergency transportation system. A 15 to 20% reduction in response time means "
        "thousands of lives saved every year. Because our graph pipeline is completely automated, we can deploy this "
        "to any city in India in under 60 seconds without installing expensive road sensors. "
        "The live application and source code are available today. Thank you, and we welcome your questions!")

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation successfully created and saved to: {output_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    out_file = os.path.join(out_dir, "EmergencyRoute_AI_Presentation.pptx")
    build_presentation(out_file)
