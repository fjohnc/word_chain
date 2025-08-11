
import streamlit as st
from dataclasses import dataclass
from typing import Set, Tuple, Dict, List
from datetime import date

# =========================================
# Data structures & core game logic
# =========================================

@dataclass(frozen=True)
class Tile:
    name: str
    tags: Set[str]

def normalize(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))

def is_real_tag(tag: str) -> bool:
    return not tag.startswith("decoy:")

class ChainReaction:
    def __init__(self, tiles: List[Tile], solution_edges: Set[Tuple[str, str]], max_degree: int = 2):
        self.tiles: Dict[str, Tile] = {t.name: t for t in tiles}
        self.edges: Set[Tuple[str, str]] = set()
        self.solution_edges = {normalize(*e) for e in solution_edges}
        self.max_degree = max_degree

    def degree(self, node: str) -> int:
        return sum(1 for e in self.edges if node in e)

    def share_tag(self, a: str, b: str, real_only: bool = False) -> Set[str]:
        shared = self.tiles[a].tags & self.tiles[b].tags
        if real_only:
            shared = {t for t in shared if is_real_tag(t)}
        return shared

    def can_connect(self, a: str, b: str, difficulty: str = "Easy") -> Tuple[bool, str]:
        if a not in self.tiles or b not in self.tiles:
            return False, "One or both tiles don't exist."
        if a == b:
            return False, "Cannot connect a tile to itself."
        edge = normalize(a, b)
        if edge in self.edges:
            return False, "Those tiles are already connected."
        if self.degree(a) >= self.max_degree or self.degree(b) >= self.max_degree:
            return False, "A tile would exceed the maximum of 2 connections."
        shared = self.share_tag(a, b, real_only=(difficulty == "Hard"))
        if difficulty == "Hard":
            if len(shared) != 1:
                return False, "Hard mode: tiles must share exactly one real tag."
        else:
            if not shared:
                return False, "Those tiles don't share a logical link (no common tag)."
        return True, ""

    def add_edge(self, a: str, b: str, difficulty: str = "Easy") -> Tuple[bool, str]:
        ok, msg = self.can_connect(a, b, difficulty)
        if ok:
            self.edges.add(normalize(a, b))
            shared = ", ".join(sorted(self.share_tag(a, b, real_only=(difficulty == "Hard"))))
            return True, f"Linked {a} ↔ {b}" + (f"  (shared tag: {shared})" if shared else "")
        return False, msg

    def remove_edge(self, a: str, b: str) -> Tuple[bool, str]:
        edge = normalize(a, b)
        if edge not in self.edges:
            return False, "That link doesn't exist."
        self.edges.remove(edge)
        return True, f"Removed link {a} – {b}."

    def is_complete_chain(self) -> Tuple[bool, str]:
        tiles = self.tiles
        edges = self.edges
        n = len(tiles)
        if len(edges) != n - 1:
            return False, "Not all tiles are connected into a single chain yet."
        # Build adjacency
        adj = {name: set() for name in tiles}
        for a, b in edges:
            adj[a].add(b); adj[b].add(a)
        # degrees
        degs = {k: len(v) for k, v in adj.items()}
        ones = [k for k, d in degs.items() if d == 1]
        twos = [k for k, d in degs.items() if d == 2]
        zeros = [k for k, d in degs.items() if d == 0]
        if zeros:
            return False, "Some tiles are isolated."
        if len(ones) != 2 or len(twos) != n - 2:
            return False, "Chain must have exactly two ends; others should have two links."
        # connectivity
        visited = set()
        start = ones[0]
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(adj[cur] - visited)
        if len(visited) != n:
            return False, "All tiles must be connected."
        return True, "Chain complete!"

    def give_hint(self) -> str:
        for a, b in sorted(self.solution_edges):
            if (a, b) not in self.edges:
                return f"Try linking: {a} ↔ {b}"
        return "No hints available."

    def auto_solve(self):
        self.edges = set(self.solution_edges)

# =========================================
# Multiple handcrafted puzzles
# =========================================

PUZZLES: List[Tuple[List[Tile], Set[Tuple[str, str]]]] = []

# Puzzle 1
tiles1 = [
    Tile("Dog", {"canine", "pet", "bone"}),
    Tile("Bone", {"bone", "calcium"}),
    Tile("Calcium", {"calcium", "milk"}),
    Tile("Milk", {"milk", "feline"}),
    Tile("Cat", {"feline", "fur"}),
    Tile("Fur", {"fur", "coat"}),
    Tile("Coat", {"coat", "winter"}),
    Tile("Winter", {"winter", "season"}),
]
sol1 = {("Dog","Bone"),("Bone","Calcium"),("Calcium","Milk"),
        ("Milk","Cat"),("Cat","Fur"),("Fur","Coat"),("Coat","Winter")}
PUZZLES.append((tiles1, sol1))

# Puzzle 2
tiles2 = [
    Tile("Sun", {"star", "sunlight"}),
    Tile("Light", {"sunlight", "photosynthesis", "illumination"}),
    Tile("Plant", {"photosynthesis", "green"}),
    Tile("Oxygen", {"oxygen", "gas"}),
    Tile("Human", {"breath", "person"}),
    Tile("Exercise", {"fitness", "breath"}),
    Tile("Health", {"fitness", "wellness"}),
    Tile("Longevity", {"wellness", "aging"}),
]
sol2 = {("Sun","Light"),("Light","Plant"),("Plant","Oxygen"),
        ("Oxygen","Human"),("Human","Exercise"),("Exercise","Health"),("Health","Longevity")}
PUZZLES.append((tiles2, sol2))

# Puzzle 3
tiles3 = [
    Tile("Wheat", {"grain", "flour"}),
    Tile("Flour", {"flour", "dough"}),
    Tile("Dough", {"dough", "yeast"}),
    Tile("Bread", {"yeast", "bakery"}),
    Tile("Sandwich", {"bakery", "lunch"}),
    Tile("Picnic", {"lunch", "outdoor"}),
    Tile("Sunset", {"outdoor", "evening"}),
    Tile("Stars", {"evening", "night"}),
]
sol3 = {("Wheat","Flour"),("Flour","Dough"),("Dough","Bread"),
        ("Bread","Sandwich"),("Sandwich","Picnic"),("Picnic","Sunset"),("Sunset","Stars")}
PUZZLES.append((tiles3, sol3))

# Puzzle 4
tiles4 = [
    Tile("Passport", {"id", "travel"}),
    Tile("Airport", {"travel", "flight"}),
    Tile("Plane", {"flight", "wing"}),
    Tile("Clouds", {"wing", "sky"}),
    Tile("Skyline", {"sky", "city"}),
    Tile("Hotel", {"city", "stay"}),
    Tile("Breakfast", {"stay", "meal"}),
    Tile("Coffee", {"meal", "caffeine"}),
]
sol4 = {("Passport","Airport"),("Airport","Plane"),("Plane","Clouds"),
        ("Clouds","Skyline"),("Skyline","Hotel"),("Hotel","Breakfast"),("Breakfast","Coffee")}
PUZZLES.append((tiles4, sol4))

# =========================================
# Helpers for decoys and puzzle building
# =========================================

def add_decoys_non_overlapping(tiles: List[Tile], n_decoys_each: int = 1, seed: int = 0) -> List[Tile]:
    import random
    random.seed(seed)
    new_tiles: List[Tile] = []
    for t in tiles:
        tags = set(t.tags)
        for _ in range(n_decoys_each):
            tags.add(f"decoy:{t.name}:{random.randint(1000,9999)}")
        new_tiles.append(Tile(t.name, tags))
    return new_tiles

def build_puzzle_by_index(idx: int, difficulty: str, seed: int) -> ChainReaction:
    base_tiles, base_solution = PUZZLES[idx % len(PUZZLES)]
    tiles = base_tiles
    if difficulty in ("Medium", "Hard"):
        tiles = add_decoys_non_overlapping(tiles, n_decoys_each=(1 if difficulty == "Medium" else 2), seed=seed)
    return ChainReaction(tiles, base_solution)

def daily_index(seed_offset: int = 0) -> int:
    return (date.today().toordinal() + seed_offset) % len(PUZZLES)

# =========================================
# Streamlit App
# =========================================

st.set_page_config(page_title="Word Chain — Logic Link Puzzle", page_icon="🧩", layout="wide")

# --- Session state init ---
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Easy"
if "seed" not in st.session_state:
    st.session_state.seed = 42
if "revealed_tags" not in st.session_state:
    st.session_state.revealed_tags = set()
if "puzzle_index" not in st.session_state:
    st.session_state.puzzle_index = 0
if "use_daily" not in st.session_state:
    st.session_state.use_daily = False
if "game" not in st.session_state:
    st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
if "message" not in st.session_state:
    st.session_state.message = ""

# UI header
st.title("🧩 Word Chain — Logic Link Puzzle")
st.caption("Link all tiles into a single chain. In **Hard**, each link must share exactly one *real* tag (decoys ignored).")

with st.sidebar:
    st.header("Setup")
    prev_diff = st.session_state.difficulty
    st.session_state.difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
                                               index=["Easy","Medium","Hard"].index(st.session_state.difficulty))
    # Rebuild puzzle if difficulty changed
    if st.session_state.difficulty != prev_diff:
        st.session_state.revealed_tags = set()
        st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
        st.session_state.message = ""

    st.session_state.use_daily = st.checkbox("Daily puzzle (rotates each day)", value=st.session_state.use_daily)
    if st.session_state.use_daily:
        idx = daily_index()
        if idx != st.session_state.puzzle_index:
            st.session_state.puzzle_index = idx
            st.session_state.revealed_tags = set()
            st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
            st.session_state.message = ""
        st.info(f"Today's puzzle: #{st.session_state.puzzle_index + 1} of {len(PUZZLES)}")
    else:
        st.session_state.seed = st.number_input("Seed (for decoys & consistency)", min_value=0, step=1, value=st.session_state.seed)

    colP1, colP2 = st.columns(2)
    with colP1:
        if st.button("◀ Prev puzzle", use_container_width=True, disabled=st.session_state.use_daily):
            st.session_state.puzzle_index = (st.session_state.puzzle_index - 1) % len(PUZZLES)
            st.session_state.revealed_tags = set()
            st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
            st.session_state.message = ""
    with colP2:
        if st.button("Next puzzle ▶", use_container_width=True, disabled=st.session_state.use_daily):
            st.session_state.puzzle_index = (st.session_state.puzzle_index + 1) % len(PUZZLES)
            st.session_state.revealed_tags = set()
            st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
            st.session_state.message = ""

    if st.button("♻️ New Puzzle", use_container_width=True):
        st.session_state.revealed_tags = set()
        st.session_state.game = build_puzzle_by_index(st.session_state.puzzle_index, st.session_state.difficulty, st.session_state.seed)
        st.session_state.message = "New puzzle loaded."

    st.markdown("---")
    st.header("Actions")
    tiles_list = sorted(list(st.session_state.game.tiles.keys()))
    colA, colB = st.columns(2)
    with colA:
        a = st.selectbox("Tile A", options=tiles_list, index=0, key="sel_a")
    with colB:
        b = st.selectbox("Tile B", options=tiles_list, index=1, key="sel_b")

    link_col, unlink_col = st.columns(2)
    with link_col:
        if st.button("Link A ↔ B", use_container_width=True):
            ok, msg = st.session_state.game.add_edge(a, b, st.session_state.difficulty)
            st.session_state.message = msg
    with unlink_col:
        if st.button("Unlink A — B", use_container_width=True):
            ok, msg = st.session_state.game.remove_edge(a, b)
            st.session_state.message = msg

    st.markdown("---")
    if st.button("🔍 Hint", use_container_width=True):
        st.session_state.message = st.session_state.game.give_hint()
    if st.button("✅ Check", use_container_width=True):
        ok, msg = st.session_state.game.is_complete_chain()
        st.session_state.message = msg
        if ok:
            st.balloons()
    if st.button("✨ Auto-solve", use_container_width=True):
        st.session_state.game.auto_solve()
        st.session_state.message = "Filled in the intended solution."
    if st.button("🧼 Reset links", use_container_width=True):
        st.session_state.game.edges = set()
        st.session_state.message = "Cleared all links."

    if st.session_state.difficulty in ("Medium", "Hard"):
        st.markdown("---")
        st.subheader("Inspect (reveal tags for a single tile)")
        inspect_tile = st.selectbox("Tile", options=tiles_list, key="inspect_tile")
        if st.button("👁️ Reveal selected tile", use_container_width=True):
            st.session_state.revealed_tags.add(inspect_tile)
            st.session_state.message = f"Revealed tags for {inspect_tile}"

# Feedback toast
if st.session_state.message:
    st.toast(st.session_state.message)

# ---------- Rendering helpers (strict) ----------

def display_rows() -> List[Dict[str, str]]:
    """
    Build the table to display. In Medium/Hard, never leak tags for non-revealed tiles.
    """
    rows: List[Dict[str, str]] = []
    diff = st.session_state.difficulty
    revealed = st.session_state.revealed_tags
    for name, t in st.session_state.game.tiles.items():
        if diff == "Easy":
            tags_txt = ", ".join(sorted(t.tags))
        elif name in revealed:
            tags_txt = ", ".join(sorted(t.tags)) + "  👁️"
        else:
            tags_txt = "••• hidden (reveal via Inspect)"
        rows.append({
            "Tile": name,
            "Tags": tags_txt,
            "Links": st.session_state.game.degree(name)
        })
    return rows

# ---------- Layout ----------

left, right = st.columns([1, 1])

with left:
    st.subheader(f"Tiles — Puzzle #{st.session_state.puzzle_index + 1} of {len(PUZZLES)}")
    st.dataframe(display_rows(), use_container_width=True, hide_index=True)

with right:
    st.subheader("Current Links")
    if not st.session_state.game.edges:
        st.write("*(no links yet)*")
    else:
        for a, b in sorted(st.session_state.game.edges):
            shared = ", ".join(sorted(st.session_state.game.share_tag(a, b, real_only=(st.session_state.difficulty=='Hard'))))
            st.write(f"• **{a} ↔ {b}**  — _shared tag_: {shared if shared else '—'}")

st.markdown("---")
st.caption("Daily mode rotates puzzles by date. Easy shows tags; Medium/Hard hide them until inspected. "
           "Hard requires exactly one shared real tag per link. Decoy tags add noise without changing logic.")
