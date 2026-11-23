import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_light_deck(output_path="EmergencyRoute_AI_Presentation.pptx"):
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Clean Professional Light Mode Palette
    BG_LIGHT = RGBColor(248, 250, 252)       # Slate 50 (Crisp Light Background)
    CARD_BG = RGBColor(255, 255, 255)        # Pure White Card
    CARD_BORDER = RGBColor(226, 232, 240)    # Slate 200 Card Border
    CARD_BORDER_ACCENT = RGBColor(203, 213, 225) # Slate 300
    TEXT_HEAD = RGBColor(15, 23, 42)         # Slate 900 (High contrast dark)
    TEXT_BODY = RGBColor(51, 65, 85)         # Slate 700 (Body text)
    TEXT_MUTED = RGBColor(100, 116, 139)     # Slate 500 (Subtext)
    
    # Premium Visual Accents (High visibility on white)
    ACCENT_BLUE = RGBColor(37, 99, 235)      # Royal Blue (#2563EB)
    ACCENT_GREEN = RGBColor(16, 185, 129)    # Emerald (#10B981)
    ACCENT_AMBER = RGBColor(217, 119, 6)     # Amber (#D97706)
    ACCENT_CYAN = RGBColor(8, 145, 178)      # Cyan (#0891B2)
    ACCENT_PURPLE = RGBColor(147, 51, 234)   # Purple (#9333EA)
    ROW_BG_ALT = RGBColor(241, 245, 249)     # Slate 100 for table alternating rows

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_LIGHT

    def add_header(slide, title_text, category_text="EMERGENCYROUTE AI • HIERARCHICAL SYSTEM ARCHITECTURE"):
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_HEAD

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
        return shape

    slide_layout = prs.slide_layouts[6] # Blank canvas

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Light Mode)
    # =========================================================================
    s1 = prs.slides.add_slide(slide_layout)
    set_slide_background(s1)

    # Decorative accent bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(0.15), Inches(3.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_BLUE
    bar.line.fill.background()

    # Title text frame
    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(11), Inches(3.5))
    tf = t_box.text_frame
    tf.word_wrap = True

    p_badge = tf.paragraphs[0]
    p_badge.text = "DATA STRUCTURES & ALGORITHMS CAPSTONE • LIVE DEMO DEFENSE"
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = ACCENT_BLUE

    p_main = tf.add_paragraph()
    p_main.text = "EmergencyRoute AI"
    p_main.font.size = Pt(46)
    p_main.font.bold = True
    p_main.font.color.rgb = TEXT_HEAD

    p_sub = tf.add_paragraph()
    p_sub.text = "Optimal Emergency Vehicle Routing on Road Networks Using Graph Search"
    p_sub.font.size = Pt(20)
    p_sub.font.bold = True
    p_sub.font.color.rgb = ACCENT_BLUE

    p_desc = tf.add_paragraph()
    p_desc.text = "A full-stack hierarchical GIS platform comparing BFS, DFS, Greedy Best-First, and A* on OpenStreetMap road graphs with dynamic traffic."
    p_desc.font.size = Pt(13)
    p_desc.font.color.rgb = TEXT_MUTED

    # Bottom Meta Cards (Light Mode)
    meta_items = [
        ("CORE ALGORITHMS", "BFS • DFS • Greedy • A*", ACCENT_BLUE),
        ("DATASET & TOPOLOGY", "OpenStreetMap (Phagwara Network)", ACCENT_GREEN),
        ("MAPPING & GIS", "TomTom Live Vector & Traffic Flow", ACCENT_AMBER),
        ("PRODUCTION STACK", "React 18 • TypeScript • FastAPI", ACCENT_CYAN)
    ]
    for idx, (lbl, val, col) in enumerate(meta_items):
        col_w = Inches(2.75)
        col_x = Inches(0.8) + idx * Inches(2.95)
        add_card(s1, col_x, Inches(5.4), col_w, Inches(1.3))
        tb = s1.shapes.add_textbox(col_x + Inches(0.15), Inches(5.45), col_w - Inches(0.3), Inches(1.2))
        tf_m = tb.text_frame
        tf_m.word_wrap = True
        p1 = tf_m.paragraphs[0]
        p1.text = lbl
        p1.font.size = Pt(9)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf_m.add_paragraph()
        p2.text = val
        p2.font.size = Pt(12)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_HEAD

    s1.notes_slide.notes_text_frame.text = (
        "Good morning / afternoon everyone. Today I am presenting EmergencyRoute AI, an emergency dispatch and routing system. "
        "Unlike commercial applications that treat ambulances like standard commuters, our system implements and rigorously compares four "
        "fundamental DSA graph algorithms—BFS, DFS, Greedy Best-First, and A*—on real-world road networks with dynamic traffic weights. "
        "Today, we will trace the complete system hierarchy starting directly from the interactive visual map interface down to the algorithmic mechanics."
    )

    # =========================================================================
    # SLIDE 2: INTERACTIVE MAP & SPATIAL INTERFACE (Map at the Beginning!)
    # =========================================================================
    s2 = prs.slides.add_slide(slide_layout)
    set_slide_background(s2)
    add_header(s2, "Interactive Map Engine & Spatial Telemetry Interface", "LEVEL 1: USER-FACING GIS CENTRIC DISPATCH")

    # 3 Feature Cards on Left
    left_cards = [
        ("TomTom Vector Basemap (Default)", "High-contrast urban vector tiles optimized for high-speed readability, displaying municipal arterial roads, street names, and critical hospital landmarks.", ACCENT_BLUE),
        ("Real-Time Traffic Flow & Incident Layer", "Direct integration with TomTom Traffic Flow API streaming live road speeds, traffic delays, and emergency road incident hazard markers across Phagwara.", ACCENT_GREEN),
        ("Multi-Layer Operational Switching", "Seamless one-click switching between TomTom Light, Tactical Night Mode, Esri High-Resolution Satellite imagery, and OpenStreetMap Vector maps.", ACCENT_CYAN)
    ]
    for idx, (title, desc, col) in enumerate(left_cards):
        top_y = Inches(1.6) + idx * Inches(1.75)
        add_card(s2, Inches(0.8), top_y, Inches(5.7), Inches(1.55))
        tb = s2.shapes.add_textbox(Inches(1.05), top_y + Inches(0.15), Inches(5.2), Inches(1.25))
        tf_m = tb.text_frame
        tf_m.word_wrap = True
        p1 = tf_m.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf_m.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_BODY

    # Right Card: Interactive Dispatch Pinning & Universal Search
    add_card(s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tb_pin = s2.shapes.add_textbox(Inches(7.1), Inches(1.85), Inches(5.1), Inches(4.7))
    tf_p = tb_pin.text_frame
    tf_p.word_wrap = True

    p = tf_p.paragraphs[0]
    p.text = "DISPATCH CONTROLS & GEOCODING"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf_p.add_paragraph()
    p.text = (
        "1. Universal Location Search (TomTom Geocoding):\n"
        "   • As-you-type fuzzy address and landmark autocomplete.\n"
        "   • High-contrast opaque dropdown for instant selection of hospitals, universities, and stations.\n\n"
        "2. Interactive 'Find on Map' Pin Dropper:\n"
        "   • One-click mode allowing dispatchers to click anywhere on Phagwara map.\n"
        "   • Automatically captures coordinates and snaps to the nearest drivable intersection.\n\n"
        "3. Live Draggable Waypoint Pins:\n"
        "   • Dispatchers can drag Origin (A) and Destination (B) markers across the city.\n"
        "   • Recalculates and re-renders all 4 algorithms on drag-end with zero latency.\n\n"
        "4. Synchronized Multi-Path Visualization:\n"
        "   • Visualizes all 4 paths simultaneously with distinct color coding and dashed overlays for instant visual auditing."
    )
    p.font.size = Pt(11.5)
    p.font.color.rgb = TEXT_BODY

    s2.notes_slide.notes_text_frame.text = (
        "We begin our technical presentation with the primary dispatch interface that first responders interact with. "
        "Our system features a TomTom Vector map as its primary layer, giving crisp clarity over Phagwara's roads. "
        "Dispatchers can switch between Day Vector, Night Tactical, and Satellite views, and toggle live TomTom traffic flow. "
        "We integrated TomTom fuzzy geocoding for universal address search, alongside our 'Find on Map' tool that lets dispatchers "
        "click anywhere or drag markers A and B directly across the map, instantly triggering our background graph solvers."
    )

    # =========================================================================
    # SLIDE 3: ROAD NETWORK TOPOLOGY & OPENSTREETMAP DATASET
    # =========================================================================
    s3 = prs.slides.add_slide(slide_layout)
    set_slide_background(s3)
    add_header(s3, "Road Network Topology & OpenStreetMap Dataset", "LEVEL 2: THE UNDERLYING MATHEMATICAL GRAPH")

    # 4 Stat Cards
    stats = [
        ("TOTAL VERTICES (NODES)", "3,975", "Intersections, roundabouts & terminal dead-ends", ACCENT_BLUE),
        ("DIRECTED EDGES", "10,229", "Drivable street segments with directional constraints", ACCENT_GREEN),
        ("GRAPH DATA STRUCTURE", "MultiDiGraph", "NetworkX directed graph supporting parallel road lanes", ACCENT_CYAN),
        ("SPATIAL SNAPPING", "SciPy KDTree", "O(log N) nearest-intersection coordinate projection", ACCENT_AMBER),
    ]
    for idx, (title, num, sub, col) in enumerate(stats):
        col_w = Inches(2.75)
        col_x = Inches(0.8) + idx * Inches(2.95)
        add_card(s3, col_x, Inches(1.6), col_w, Inches(1.9))
        tb = s3.shapes.add_textbox(col_x + Inches(0.15), Inches(1.75), col_w - Inches(0.3), Inches(1.6))
        tf_s = tb.text_frame
        tf_s.word_wrap = True
        p1 = tf_s.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(9)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf_s.add_paragraph()
        p2.text = num
        p2.font.size = Pt(28)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_HEAD
        p3 = tf_s.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(10)
        p3.font.color.rgb = TEXT_MUTED

    # Bottom Half: Graph Modeling Details
    add_card(s3, Inches(0.8), Inches(3.8), Inches(11.7), Inches(3.0))
    tb_bot = s3.shapes.add_textbox(Inches(1.1), Inches(4.0), Inches(11.1), Inches(2.6))
    tf_b = tb_bot.text_frame
    tf_b.word_wrap = True

    p = tf_b.paragraphs[0]
    p.text = "GRAPH EXTRACTION & ACCESSIBILITY CONSTRAINTS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_b.add_paragraph()
    p.text = "Mathematical Graph: G = (V, E) where V are road junctions and E are drivable directed segments"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = TEXT_HEAD

    p = tf_b.add_paragraph()
    p.text = (
        "• Data Extraction: Extracted real-world drivable road infrastructure of Phagwara, Punjab using OSMnx and Overpass API.\n"
        "• Topological Correctness: Filters out non-drivable paths (footways, steps, cycleways) while preserving multi-lane dual carriageways and service roads.\n"
        "• Directional Attributes: Directed edges enforce one-way restrictions, median barriers, and mandatory turns to prevent illegal ambulance maneuvers.\n"
        "• Sub-Millisecond Node Snapping: Raw GPS coordinates from user clicks snap into the graph in <1 ms using a 2D Euclidean KDTree."
    )
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY

    s3.notes_slide.notes_text_frame.text = (
        "Descending from the visual map to the data layer: the city of Phagwara is modeled as a NetworkX MultiDiGraph containing "
        "3,975 vertices and 10,229 directed edges extracted directly from OpenStreetMap. "
        "This is not a simplistic grid graph; it captures real one-way streets, turn restrictions, and road classifications. "
        "When a dispatcher clicks on a building or street, our KDTree spatial index projects that coordinate to the exact nearest "
        "traversable road intersection in under one millisecond."
    )

    # =========================================================================
    # SLIDE 4: MATHEMATICAL EDGE COST MODEL & TRAFFIC WEIGHTS
    # =========================================================================
    s4 = prs.slides.add_slide(slide_layout)
    set_slide_background(s4)
    add_header(s4, "Dynamic Edge Cost Formulation & Traffic Weighting", "LEVEL 3: WEIGHTED COST MATRICES")

    # Formula Card Across Top
    add_card(s4, Inches(0.8), Inches(1.6), Inches(11.7), Inches(1.7))
    tb_eq = s4.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(11.1), Inches(1.4))
    tf_eq = tb_eq.text_frame
    tf_eq.word_wrap = True

    p = tf_eq.paragraphs[0]
    p.text = "PRIMARY OBJECTIVE FUNCTION: DYNAMIC TRAVEL TIME COST"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf_eq.add_paragraph()
    p.text = "Cost(u, v) = [ Length(u, v) / FreeFlowSpeed(u, v) ] × TrafficMultiplier(u, v) + ObstaclePenalty"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_eq.add_paragraph()
    p.text = "Minimizing total path cost evaluates true time-to-hospital, combining road segment distance, speed class, and congestion."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_MUTED

    # 3 Cost Factor Breakdown Cards Below
    factors = [
        ("1. Road Tier Free-Flow Speeds", [
            "Motorway / NH44: 65 km/h",
            "Primary Arterial: 45 km/h",
            "Secondary Urban: 35 km/h",
            "Residential Street: 25 km/h",
            "Narrow Service Lane: 15 km/h"
        ], ACCENT_BLUE),
        ("2. Synthetic & Dynamic Traffic", [
            "Free Flow (Late Night): 1.05x",
            "Normal Operating: 1.25x",
            "Moderate Flow: 1.50x",
            "Peak Rush Hour: 2.20x - 2.80x",
            "Multipliers applied per edge class"
        ], ACCENT_GREEN),
        ("3. Dynamic Incident / Obstacle Penalty", [
            "Road Closures: weight = 10^9",
            "Severe Collisions: 5.0x penalty",
            "Flooding / Construction: 4.0x penalty",
            "Guarantees automatic bypass",
            "Prunes blocked edges in priority queue"
        ], ACCENT_AMBER),
    ]

    for idx, (title, items, col) in enumerate(factors):
        col_w = Inches(3.7)
        col_x = Inches(0.8) + idx * Inches(4.0)
        add_card(s4, col_x, Inches(3.55), col_w, Inches(3.3))
        tb = s4.shapes.add_textbox(col_x + Inches(0.15), Inches(3.7), col_w - Inches(0.3), Inches(3.0))
        tf_f = tb.text_frame
        tf_f.word_wrap = True

        p1 = tf_f.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = col

        for item in items:
            p_it = tf_f.add_paragraph()
            p_it.text = f"• {item}"
            p_it.font.size = Pt(10.5)
            p_it.font.color.rgb = TEXT_BODY

    s4.notes_slide.notes_text_frame.text = (
        "Now into the mathematical cost formulation: In emergency medicine, distance in kilometers does not save lives—time in minutes does. "
        "Our cost function divides road length by its free-flow speed tier, then multiplies by synthetic or live traffic weights. "
        "A residential shortcut that is geographically short might have a 25 km/h speed limit and 2.5x rush-hour congestion, "
        "making the main highway significantly faster. When an incident or road closure occurs, an obstacle penalty of 10 to the 9th is added, "
        "instantly pruning that road from the algorithm's priority queue."
    )

    # =========================================================================
    # SLIDE 5: THE 4 DSA GRAPH ALGORITHMS DEEP-DIVE
    # =========================================================================
    s5 = prs.slides.add_slide(slide_layout)
    set_slide_background(s5)
    add_header(s5, "Core Algorithms Deep-Dive: Comparative Mechanics", "LEVEL 4: GRAPH SEARCH ENGINE COMPARISON")

    algos = [
        ("A* Search (A-Star)", "PROVABLY OPTIMAL", ACCENT_BLUE,
         "f(n) = g(n) + h(n)",
         "Priority Queue (Min-Heap)",
         "Guaranteed Optimal (Admissible)",
         "Evaluates cumulative traffic-weighted cost g(n) + admissible Haversine heuristic h(n). Prunes sub-optimal search branches; undisputed gold standard for emergency dispatch."),
        ("Greedy Best-First", "FASTEST EXPLORATION", ACCENT_AMBER,
         "f(n) = h(n)",
         "Priority Queue (Heuristic)",
         "Suboptimal (Greedy Trap)",
         "Directly selects nodes nearest to target based purely on geometric distance h(n). Ultra-low latency and minimal expansions, but prone to traffic dead-ends."),
        ("Breadth-First (BFS)", "FEWEST ROAD SEGMENTS", ACCENT_CYAN,
         "Level-Order Traversal",
         "FIFO Queue (First-In-First-Out)",
         "Optimal for Unweighted Hops",
         "Explores all neighbor intersections level by level. Guarantees minimum turn/hop count on unweighted graphs, but ignores road lengths and congestion."),
        ("Depth-First (DFS)", "UNBOUNDED BASELINE", ACCENT_PURPLE,
         "Deep Corridor Traversal",
         "LIFO Stack (Backtracking)",
         "Highly Suboptimal",
         "Dives deeply along the first encountered road corridor before backtracking. Serves as our control baseline to demonstrate spatial search failure.")
    ]

    for idx, (name, tag, col, formula, frontier, optimality, desc) in enumerate(algos):
        col_w = Inches(2.75)
        col_x = Inches(0.8) + idx * Inches(2.95)
        add_card(s5, col_x, Inches(1.6), col_w, Inches(5.2))
        tb = s5.shapes.add_textbox(col_x + Inches(0.15), Inches(1.8), col_w - Inches(0.3), Inches(4.8))
        tf_a = tb.text_frame
        tf_a.word_wrap = True

        p1 = tf_a.paragraphs[0]
        p1.text = tag
        p1.font.size = Pt(9)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf_a.add_paragraph()
        p2.text = name
        p2.font.size = Pt(16)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_HEAD

        p3 = tf_a.add_paragraph()
        p3.text = f"\nEvaluation Metric:\n{formula}"
        p3.font.size = Pt(11)
        p3.font.bold = True
        p3.font.color.rgb = ACCENT_AMBER

        p4 = tf_a.add_paragraph()
        p4.text = f"\nFrontier Data Structure:\n{frontier}"
        p4.font.size = Pt(10)
        p4.font.color.rgb = TEXT_BODY

        p5 = tf_a.add_paragraph()
        p5.text = f"\nOptimality Guarantee:\n{optimality}"
        p5.font.size = Pt(10)
        p5.font.bold = True
        p5.font.color.rgb = col

        p6 = tf_a.add_paragraph()
        p6.text = f"\n{desc}"
        p6.font.size = Pt(10)
        p6.font.color.rgb = TEXT_MUTED

    s5.notes_slide.notes_text_frame.text = (
        "Here are the four algorithms that form the analytical core of our project. "
        "A* combines g(n)—the exact elapsed traffic travel time—with h(n)—the Haversine great-circle distance divided by maximum road speed. "
        "Because our heuristic never overestimates the true remaining time, A* is mathematically guaranteed to be optimal. "
        "Greedy Best-First only looks at h(n): it rushes directly towards the destination, expanding very few nodes, but often lands in congested bottlenecks. "
        "BFS uses a FIFO queue to guarantee the fewest intersections, but treats a highway and a 15 km/h alleyway the same. "
        "DFS uses a LIFO stack, diving endlessly down dead-ends and serving as our unbounded comparison baseline."
    )

    # =========================================================================
    # SLIDE 6: EMPIRICAL BENCHMARK RESULTS & SEARCH EFFICIENCY
    # =========================================================================
    s6 = prs.slides.add_slide(slide_layout)
    set_slide_background(s6)
    add_header(s6, "Empirical Benchmark Results & Search Efficiency", "LEVEL 5: ALGORITHMIC AUDIT ON MODEL TOWN → CIVIL HOSPITAL")

    # Table Shape
    rows, cols = 5, 6
    tbl_shape = s6.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.6))
    table = tbl_shape.table

    table.columns[0].width = Inches(2.5) # Algorithm
    table.columns[1].width = Inches(1.8) # Travel Time
    table.columns[2].width = Inches(1.8) # Distance
    table.columns[3].width = Inches(1.8) # Cost
    table.columns[4].width = Inches(2.0) # Nodes Explored
    table.columns[5].width = Inches(1.8) # Latency

    headers = ["ALGORITHM", "EST. TIME", "DISTANCE", "PATH COST", "NODES EXP.", "LATENCY"]
    data = [
        ["A* Search (Optimal)", "5.17 min", "2.72 km", "542.5", "184 nodes", "11.8 ms"],
        ["Greedy Best-First", "8.14 min", "3.41 km", "712.0", "42 nodes", "5.4 ms"],
        ["Breadth-First (BFS)", "7.67 min", "3.22 km", "680.4", "618 nodes", "18.2 ms"],
        ["Depth-First (DFS)", "125.0 min", "62.4 km", "12,480", "1,440 nodes", "44.6 ms"],
    ]

    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(226, 232, 240) # Slate 200 header
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_HEAD

    for row_idx, row_data in enumerate(data):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = ROW_BG_ALT if row_idx % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.bold = (col_idx == 0 or (row_idx == 0 and col_idx == 1))
            if row_idx == 0 and col_idx == 1:
                p.font.color.rgb = ACCENT_GREEN
            elif col_idx == 0:
                p.font.color.rgb = TEXT_HEAD
            else:
                p.font.color.rgb = TEXT_BODY

    # Bottom 3 Insight Cards
    insights = [
        ("Key Finding 1: A* Saves Critical Time", "A* achieves the fastest travel time (5.17 min) by steering around congested Patel Nagar corridors, saving ~3 minutes compared to Greedy and BFS.", ACCENT_GREEN),
        ("Key Finding 2: Greedy Latency Tradeoff", "Greedy BFS expanded only 42 nodes (77% fewer than A*), executing in 5.4 ms. However, its path cost was 31% worse because it blindly targeted the goal.", ACCENT_AMBER),
        ("Key Finding 3: BFS & DFS Spatial Failure", "BFS found fewer intersections but slower travel time due to stop-and-go streets. DFS failed drastically, traversing 62 km because it lacks any cost-awareness.", ACCENT_PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(insights):
        col_w = Inches(3.7)
        col_x = Inches(0.8) + idx * Inches(4.0)
        add_card(s6, col_x, Inches(4.5), col_w, Inches(2.3))
        tb = s6.shapes.add_textbox(col_x + Inches(0.15), Inches(4.65), col_w - Inches(0.3), Inches(2.0))
        tf_i = tb.text_frame
        tf_i.word_wrap = True
        p1 = tf_i.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf_i.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_BODY

    s6.notes_slide.notes_text_frame.text = (
        "Here are the empirical benchmark numbers from our live system audit on the route from Model Town to Civil Hospital Phagwara. "
        "A* is the undisputed winner for emergency vehicles: it reached the hospital in 5.17 minutes, exploring 184 nodes in 11.8 ms. "
        "Greedy Best-First was the fastest computationally—expanding only 42 nodes in 5.4 ms—but its path took 8.14 minutes because it got trapped in secondary roads. "
        "BFS produced a 7.67-minute route, expanding over 600 nodes. And DFS produced a 62-kilometer catastrophe. "
        "These empirical results validate that A* with admissible heuristics is the single best choice for emergency navigation."
    )

    # =========================================================================
    # SLIDE 7: SYSTEM ARCHITECTURE & PRODUCTION TECH STACK
    # =========================================================================
    s7 = prs.slides.add_slide(slide_layout)
    set_slide_background(s7)
    add_header(s7, "System Architecture & Production Tech Stack", "LEVEL 6: FULL-STACK ENGINEERING PIPELINE")

    tiers = [
        ("FRONTEND INTERFACE", ACCENT_BLUE, [
            ("Framework", "React 18 + TypeScript"),
            ("Styling", "Tailwind CSS (Edge-to-Edge Glass)"),
            ("GIS Visualizer", "Leaflet.js + Custom Markers"),
            ("Build Pipeline", "Vite (HMR + Optimized Chunks)")
        ]),
        ("BACKEND GRAPH ENGINE", ACCENT_GREEN, [
            ("Web Framework", "FastAPI (Python 3.10 ASGI)"),
            ("Graph Engine", "NetworkX (MultiDiGraph)"),
            ("Spatial Lookup", "SciPy KDTree (Lat/Lng Snapping)"),
            ("Async Execution", "Uvicorn Concurrent Event Loop")
        ]),
        ("DATA & TELEMETRY", ACCENT_AMBER, [
            ("Street Network", "OpenStreetMap (Overpass / OSMnx)"),
            ("Mapping API", "TomTom Vector Map SDK"),
            ("Traffic Stream", "TomTom Live Traffic Flow API"),
            ("Live Push", "WebSocket Full-Duplex Channel")
        ])
    ]

    for idx, (tier_title, col, items) in enumerate(tiers):
        col_w = Inches(3.7)
        col_x = Inches(0.8) + idx * Inches(4.0)
        add_card(s7, col_x, Inches(1.6), col_w, Inches(5.2))
        tb = s7.shapes.add_textbox(col_x + Inches(0.15), Inches(1.8), col_w - Inches(0.3), Inches(4.8))
        tf_t = tb.text_frame
        tf_t.word_wrap = True

        p1 = tf_t.paragraphs[0]
        p1.text = tier_title
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = col

        for label, val in items:
            p_lbl = tf_t.add_paragraph()
            p_lbl.text = f"\n{label}:"
            p_lbl.font.size = Pt(11)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = TEXT_HEAD
            p_val = tf_t.add_paragraph()
            p_val.text = val
            p_val.font.size = Pt(11)
            p_val.font.color.rgb = TEXT_BODY

    s7.notes_slide.notes_text_frame.text = (
        "Our system architecture ties the entire hierarchy together across three decoupled production tiers: "
        "The frontend is built with React 18, TypeScript, and Tailwind CSS, using Leaflet for smooth 60 FPS GIS rendering. "
        "The backend is powered by FastAPI and NetworkX, delivering sub-20ms routing responses through SciPy KDTree spatial indexing. "
        "And the data layer connects directly to TomTom and OpenStreetMap, with WebSockets maintaining real-time updates for vehicle positions and road closures."
    )

    # =========================================================================
    # SLIDE 8: SUMMARY, FUTURE ROADMAP & LIVE DEMO
    # =========================================================================
    s8 = prs.slides.add_slide(slide_layout)
    set_slide_background(s8)
    add_header(s8, "Key Takeaways, Future Scope & Live Demo", "LEVEL 7: CONCLUSION & REAL-WORLD IMPACT")

    # Left Card: Achievements
    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tb_left = s8.shapes.add_textbox(Inches(1.1), Inches(1.85), Inches(5.1), Inches(4.7))
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True

    p = tf_l.paragraphs[0]
    p.text = "CORE ACHIEVEMENTS"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

    p = tf_l.add_paragraph()
    p.text = (
        "• 100% Academic Compliance: BFS, DFS, Greedy Best-First, and A* successfully implemented on a real-world OpenStreetMap road graph.\n\n"
        "• Proven Emergency Time Savings: A* algorithm consistently reduces travel time by 2.5 to 3.5 minutes compared to standard unweighted paths.\n\n"
        "• Interactive GIS Dispatch: Fully functional TomTom mapping interface with instant geocoding, draggable pins, and live traffic visualization.\n\n"
        "• Dynamic Hazard Tolerance: Immediate sub-second rerouting upon road closure or congestion spikes."
    )
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_BODY

    # Right Card: Future Scope & Live Demo
    add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tb_r = s8.shapes.add_textbox(Inches(7.1), Inches(1.85), Inches(5.1), Inches(4.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "NEXT-GENERATION ROADMAP"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_r.add_paragraph()
    p.text = (
        "1. V2X Smart Traffic Light Preemption:\n"
        "   Direct integration with municipal traffic signals to grant green-corridor priority to incoming ambulances.\n\n"
        "2. Multi-Agent Fleet Optimization:\n"
        "   Hungarian Algorithm / bipartite matching for dispatching the optimal ambulance among multiple hospital stations.\n\n"
        "3. Predictive Congestion Modeling:\n"
        "   LSTM neural networks forecasting road bottlenecks 15 minutes before they occur."
    )
    p.font.size = Pt(11.5)
    p.font.color.rgb = TEXT_BODY

    p = tf_r.add_paragraph()
    p.text = "\nLIVE DEMONSTRATION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf_r.add_paragraph()
    p.text = "Running live at http://localhost:5173\nReady for Interactive Testing & Questions."
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEXT_HEAD

    s8.notes_slide.notes_text_frame.text = (
        "To conclude, EmergencyRoute AI demonstrates that heuristic graph search applied to real city road infrastructure can save "
        "life-critical minutes in emergency response. Looking ahead, our next steps are connecting to municipal smart traffic lights for V2X "
        "green corridors and multi-vehicle dispatch optimization. Thank you very much for your time. I would now like to transition to our live "
        "demonstration at localhost:5173."
    )

    prs.save(output_path)
    print(f"Successfully generated Light Mode hierarchical presentation: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "EmergencyRoute_AI_Presentation.pptx"
    create_light_deck(out)
