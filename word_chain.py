
import streamlit as st
from dataclasses import dataclass
from typing import Set, Tuple, Dict, List
from datetime import date
import random

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
            if len(shared) != 1:
                return False, "Hard mode: tiles must share exactly one tag."
        else:
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
        adj = {name: set() for name in tiles}
        for a, b in edges:
            adj[a].add(b); adj[b].add(a)
        degs = {k: len(v) for k, v in adj.items()}
        ones = [k for k, d in degs.items() if d == 1]
        twos = [k for k, d in degs.items() if d == 2]
        zeros = [k for k, d in degs.items() if d == 0]
        if zeros:
            return False, "Some tiles are isolated."
        if len(ones) != 2 or len(twos) != n - 2:
            return False, "Chain must have exactly two ends; others should have two links."
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
# Puzzle generation
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
    Tile("Spring", {"season", "flowers"}),
    Tile("Flowers", {"flowers", "gift"}),
    Tile("Gift", {"gift", "birthday"}),
    Tile("Birthday", {"birthday", "cake"}),
]

BASE_SOLUTION = {
    ("Dog", "Bone"),
    ("Bone", "Calcium"),
    ("Calcium", "Milk"),
    ("Milk", "Cat"),
    ("Cat", "Fur"),
    ("Fur", "Coat"),
    ("Coat", "Winter"),
    ("Winter", "Spring"),
    ("Spring", "Flowers"),
    ("Flowers", "Gift"),
    ("Gift", "Birthday"),
}

def build_puzzle(difficulty: str, seed: int, size: int) -> ChainReaction:
    random.seed(seed)
    tiles = random.sample(BASE_TILES, size)
    solution_edges = {e for e in BASE_SOLUTION if e[0] in [t.name for t in tiles] and e[1] in [t.name for t in tiles]}
    return ChainReaction(tiles, solution_edges)

# =========================================
# Streamlit App
# =========================================

st.set_page_config(page_title="Word Chain — Logic Link Puzzle", page_icon="🧩", layout="wide")

# --- Session state init ---
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Easy"
if "seed" not in st.session_state:
    st.session_state.seed = 42
if "size" not in st.session_state:
    st.session_state.size = 8
if "revealed_tags" not in st.session_state:
    st.session_state.revealed_tags = set()
if "game" not in st.session_state:
    st.session_state.game = build_puzzle(st.session_state.difficulty, st.session_state.seed, st.session_state.size)
if "message" not in st.session_state:
    st.session_state.message = ""

def new_game(seed: int):
    st.session_state.seed = seed
    st.session_state.revealed_tags = set()
    st.session_state.game = build_puzzle(st.session_state.difficulty, st.session_state.seed, st.session_state.size)
    st.session_state.message = ""

st.title("🧩 Word Chain — Logic Link Puzzle")
st.caption("Link all tiles into a single chain. Each valid link must share tags. "
           "On **Hard**, links must share **exactly one** tag. Each tile can have at most two links, "
           "and the final chain must have exactly two endpoints.")

with st.sidebar:
    st.header("Setup")
    st.session_state.difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=["Easy","Medium","Hard"].index(st.session_state.difficulty))
    st.session_state.size = st.selectbox("Puzzle size", [8, 10, 12], index=[8,10,12].index(st.session_state.size))

    if st.button("♻️ Random Puzzle", use_container_width=True):
        new_game(random.randint(0, 99999))

    if st.button("📅 Daily Puzzle", use_container_width=True):
        today_seed = int(date.today().strftime("%Y%m%d"))
        new_game(today_seed)

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

# Feedback toast
if st.session_state.message:
    st.toast(st.session_state.message)

# Layout
left, right = st.columns([1, 1])

with left:
    st.subheader("Tiles")
    rows = []
    for name, t in st.session_state.game.tiles.items():
        rows.append({
            "Tile": name,
            "Tags": ", ".join(sorted(t.tags)),
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
st.caption("Tips: Try the daily puzzle for a consistent challenge or random for variety.")
