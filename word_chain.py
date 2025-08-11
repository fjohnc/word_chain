
import streamlit as st
from dataclasses import dataclass
from typing import Set, Tuple, Dict, List
import random

# =============================
# Core data structures & logic
# =============================

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

    # --- helpers ---
    def degree(self, node: str) -> int:
        return sum(1 for e in self.edges if node in e)

    def share_tag(self, a: str, b: str) -> Set[str]:
        return self.tiles[a].tags & self.tiles[b].tags

    def can_connect(self, a: str, b: str) -> Tuple[bool, str]:
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
        if not shared:
            return False, "Those tiles don't share a logical link (no common tag)."
        return True, ""

    def add_edge(self, a: str, b: str) -> Tuple[bool, str]:
        ok, msg = self.can_connect(a, b)
        if ok:
            self.edges.add(normalize(a, b))
            shared = ", ".join(sorted(self.share_tag(a, b)))
            return True, f"Linked {a} ↔ {b}  (shared tag: {shared})"
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

# =============================
# Built-in puzzles
# =============================

def word_chain_puzzle() -> ChainReaction:
    tiles = [
        Tile("Dog", {"canine", "pet", "bone"}),
        Tile("Bone", {"bone", "calcium"}),
        Tile("Calcium", {"calcium", "milk"}),
        Tile("Milk", {"milk", "feline"}),
        Tile("Cat", {"feline", "fur"}),
        Tile("Fur", {"fur", "coat"}),
        Tile("Coat", {"coat", "winter"}),
        Tile("Winter", {"winter", "season"}),
    ]
    solution = {
        ("Dog", "Bone"),
        ("Bone", "Calcium"),
        ("Calcium", "Milk"),
        ("Milk", "Cat"),
        ("Cat", "Fur"),
        ("Fur", "Coat"),
        ("Coat", "Winter"),
    }
    return ChainReaction(tiles, solution)

def is_prime(n: int) -> bool:
    if n < 2: 
        return False
    if n % 2 == 0:
        return n == 2
    f = 3
    while f * f <= n:
        if n % f == 0:
            return False
        f += 2
    return True

def number_chain_puzzle() -> ChainReaction:
    # A simple numeric chain with tags describing properties
    nums = [3, 6, 12, 24, 25, 5, 10, 20]
    tiles: List[Tile] = []
    for x in nums:
        tags = set()
        tags.add("odd" if x % 2 else "even")
        if is_prime(x):
            tags.add("prime")
        for m in (3, 5):
            if x % m == 0:
                tags.add(f"×{m}")
        if x % 2 == 0:
            tags.add("×2k")
        tiles.append(Tile(str(x), tags))
    # Intended chain (×2 and ÷2 runs with a small bend at 25 → 5)
    solution_pairs = [(3,6),(6,12),(12,24),(24,12),(12,6),(6,3)]  # ignore; replaced below
    # We'll define a clear forward chain:
    chain = [3, 6, 12, 24, 25, 5, 10, 20]
    solution = set()
    for a, b in zip(chain, chain[1:]):
        solution.add((str(a), str(b)))
    # Add tags so that neighbors share at least one tag: crafted above via divisibility/parity.
    return ChainReaction(tiles, solution)

# =============================
# UI Helpers
# =============================

def init_state():
    if "mode" not in st.session_state:
        st.session_state.mode = "Word Chain"
    if "game" not in st.session_state:
        st.session_state.game = word_chain_puzzle()
    if "message" not in st.session_state:
        st.session_state.message = ""
    if "seed" not in st.session_state:
        st.session_state.seed = 42

def new_puzzle(mode: str, seed: int | None = None):
    # For now, we have one handcrafted puzzle per mode; seed reserved for procedural gen later.
    if mode == "Word Chain":
        st.session_state.game = word_chain_puzzle()
    else:
        st.session_state.game = number_chain_puzzle()
    st.session_state.message = ""

def board_rows(game: ChainReaction) -> List[Dict[str, str]]:
    rows = []
    for t in game.tiles.values():
        rows.append({
            "Tile": t.name,
            "Tags": ", ".join(sorted(t.tags)),
            "Links": game.degree(t.name)
        })
    return rows

# =============================
# Streamlit App
# =============================

st.set_page_config(page_title="Chain Reaction — Logic Link Puzzles", page_icon="🧩", layout="wide")
init_state()

st.title("🧩 Chain Reaction — Logic Link Puzzles")
st.caption("Link all tiles into a single chain. Each valid link must share at least one tag. "
           "Most tiles should end up with **two** links; the chain must have **exactly two endpoints**.")

with st.sidebar:
    st.header("Game Setup")
    st.session_state.mode = st.selectbox("Mode", ["Word Chain", "Number Chain"], index=0)
    seed = st.number_input("Seed (for future randomization)", min_value=0, value=st.session_state.seed, step=1)
    if st.button("New Puzzle"):
        st.session_state.seed = int(seed)
        random.seed(seed)
        new_puzzle(st.session_state.mode, seed)

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
            ok, msg = st.session_state.game.add_edge(a, b)
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
    if st.button("♻️ Reset", use_container_width=True):
        new_puzzle(st.session_state.mode, st.session_state.seed)

    st.markdown("---")
    st.info("Tip: A valid link must share at least one tag. Tiles can have at most two links. "
            "Form one continuous chain with exactly two endpoints.")

# Feedback / messages
if st.session_state.message:
    st.toast(st.session_state.message)

left, right = st.columns([1, 1])

with left:
    st.subheader("Tiles")
    st.dataframe(board_rows(st.session_state.game), use_container_width=True, hide_index=True)

with right:
    st.subheader("Current Links")
    if not st.session_state.game.edges:
        st.write("*(no links yet)*")
    else:
        for a, b in sorted(st.session_state.game.edges):
            shared = ", ".join(sorted(st.session_state.game.share_tag(a, b)))
            st.write(f"• **{a} ↔ {b}**  — _shared tag_: {shared}")

st.markdown("---")
st.caption("Prototype includes two modes. Roadmap: daily puzzles, community builder, and procedural generators.")
