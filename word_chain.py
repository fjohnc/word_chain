
import streamlit as st
from dataclasses import dataclass
from typing import Set, Tuple, Dict, List

# =========================================
# Data structures & core game logic
# =========================================

@dataclass(frozen=True)
class Tile:
    name: str
    tags: Set[str]

def normalize(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))

class ChainReaction:
    def __init__(self, tiles: List[Tile], solution_edges: Set[Tuple[str, str]], max_degree: int = 2):
        self.tiles: Dict[str, Tile] = {t.name: t for t in tiles}
        self.edges: Set[Tuple[str, str]] = set()
        self.solution_edges = {normalize(*e) for e in solution_edges}
        self.max_degree = max_degree

    def degree(self, node: str) -> int:
        return sum(1 for e in self.edges if node in e)

    def share_tag(self, a: str, b: str) -> Set[str]:
        return self.tiles[a].tags & self.tiles[b].tags

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
        shared = self.share_tag(a, b)
        if difficulty == "Hard":
            # Hard rule: exactly one shared tag
            if len(shared) != 1:
                return False, "Hard mode: tiles must share exactly one tag."
        else:
            # Easy/Medium: at least one shared tag
            if not shared:
                return False, "Those tiles don't share a logical link (no common tag)."
        return True, ""

    def add_edge(self, a: str, b: str, difficulty: str = "Easy") -> Tuple[bool, str]:
        ok, msg = self.can_connect(a, b, difficulty)
        if ok:
            self.edges.add(normalize(a, b))
            shared = ", ".join(sorted(self.share_tag(a, b)))
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
# Puzzle definition & helpers
# =========================================

BASE_TILES = [
    Tile("Dog", {"canine", "pet", "bone"}),
    Tile("Bone", {"bone", "calcium"}),
    Tile("Calcium", {"calcium", "milk"}),
    Tile("Milk", {"milk", "feline"}),
    Tile("Cat", {"feline", "fur"}),
    Tile("Fur", {"fur", "coat"}),
    Tile("Coat", {"coat", "winter"}),
    Tile("Winter", {"winter", "season"}),
]

BASE_SOLUTION = {
    ("Dog", "Bone"),
    ("Bone", "Calcium"),
    ("Calcium", "Milk"),
    ("Milk", "Cat"),
    ("Cat", "Fur"),
    ("Fur", "Coat"),
    ("Coat", "Winter"),
}

def add_decoys_non_overlapping(tiles: List[Tile], n_decoys_each: int = 1, seed: int = 0) -> List[Tile]:
    """
    Adds decoy tags that DO NOT create extra overlaps between different tiles.
    This increases visual noise when tags are revealed, without enabling the
    trivial "scan duplicates" tactic.
    """
    import random
    random.seed(seed)
    new_tiles: List[Tile] = []
    for t in tiles:
        tags = set(t.tags)  # copy original tags
        for _ in range(n_decoys_each):
            tags.add(f"decoy:{t.name}:{random.randint(1000,9999)}")
        new_tiles.append(Tile(t.name, tags))
    return new_tiles

def build_puzzle(difficulty: str, seed: int) -> 'ChainReaction':
    tiles = BASE_TILES
    if difficulty in ("Medium", "Hard"):
        tiles = add_decoys_non_overlapping(tiles, n_decoys_each=(1 if difficulty == "Medium" else 2), seed=seed)
    return ChainReaction(tiles, BASE_SOLUTION)

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
if "game" not in st.session_state:
    st.session_state.game = build_puzzle(st.session_state.difficulty, st.session_state.seed)
if "message" not in st.session_state:
    st.session_state.message = ""

# Ensure puzzle exists on first load
if not getattr(st.session_state, "game", None) or not st.session_state.game.tiles:
    st.session_state.game = build_puzzle(st.session_state.difficulty, st.session_state.seed)

st.title("🧩 Word Chain — Logic Link Puzzle")
st.caption("Link all tiles into a single chain. Each valid link must share tags. "
           "On **Hard**, links must share **exactly one** tag. Each tile can have at most two links, "
           "and the final chain must have exactly two endpoints.")

with st.sidebar:
    st.header("Setup")
    st.session_state.difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(st.session_state.difficulty))
    st.session_state.seed = st.number_input("Seed (for consistent puzzles)", min_value=0, step=1, value=st.session_state.seed)
    if st.button("♻️ New Puzzle", use_container_width=True):
        st.session_state.revealed_tags = set()
        st.session_state.game = build_puzzle(st.session_state.difficulty, st.session_state.seed)
        st.session_state.message = ""
        st.experimental_rerun()

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

    # Inspect-to-reveal (Medium/Hard)
    if st.session_state.difficulty in ("Medium", "Hard"):
        st.markdown("---")
        st.subheader("Inspect")
        inspect_tile = st.selectbox("Reveal tags for:", options=tiles_list, key="inspect_tile")
        if st.button("👁️ Reveal", use_container_width=True):
            st.session_state.revealed_tags.add(inspect_tile)
            st.session_state.message = f"Revealed tags for {inspect_tile}"

# Feedback toast
if st.session_state.message:
    st.toast(st.session_state.message)

# Helpers to show tags depending on difficulty and reveals
def visible_tags(tile_name: str, tags: Set[str]) -> str:
    diff = st.session_state.difficulty
    if diff == "Easy":
        return ", ".join(sorted(tags))
    # Medium/Hard: only revealed tiles show tags
    if tile_name in st.session_state.revealed_tags:
        return ", ".join(sorted(tags)) + "  👁️"
    return "••• hidden (reveal via Inspect)"

# Layout
left, right = st.columns([1, 1])

with left:
    st.subheader("Tiles")
    rows = []
    for name, t in st.session_state.game.tiles.items():
        rows.append({
            "Tile": name,
            "Tags": visible_tags(name, t.tags),
            "Links": st.session_state.game.degree(name)
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

with right:
    st.subheader("Current Links")
    if not st.session_state.game.edges:
        st.write("*(no links yet)*")
    else:
        for a, b in sorted(st.session_state.game.edges):
            shared = ", ".join(sorted(st.session_state.game.share_tag(a, b)))
            st.write(f"• **{a} ↔ {b}**  — _shared tag_: {shared if shared else '—'}")

st.markdown("---")
st.caption("Tips: In Medium/Hard, inspect tiles to reveal tags. In Hard, each link must share exactly one tag. "
           "Use the seed to keep puzzles consistent for daily challenges.")
