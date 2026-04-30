"""
Chess Coach Dashboard for Zlatan_max
Auto-fetches chess.com data, runs daily curriculum, tracks progress.
Deploy on Streamlit Community Cloud (free).
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import json
from collections import Counter
import altair as alt

# ============================================================================
# CONFIG
# ============================================================================

USERNAME = "zlatan_max"
START_DATE = date(2026, 4, 30)  # Day 1 of the program
START_RATING = 800
TARGET_RATING = 1200
HEADERS = {"User-Agent": "ChessCoach/1.0 (personal training tool)"}

st.set_page_config(
    page_title="Chess Coach · Zlatan_max",
    page_icon="♞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# CURRICULUM (28 days, 800 -> 1200)
# ============================================================================

CURRICULUM = [
    {"day": 1, "week": 1, "phase": "Foundations", "title": "The Calculation Algorithm", "duration": "35 min",
     "big_idea": "Every move you play should pass through a 4-step filter. Skipping this is why you're 800 with a 1594 puzzle rating.",
     "lesson": "The filter, in order on every move: (1) CHECKS — does opponent have any check? Can I give one? (2) CAPTURES — what can be captured by either side? (3) THREATS — what is opponent threatening to do next move? (4) MY PLAN — only after the first three, what's my idea? Forcing moves first, plans second. At 800, players play their plan and ignore opponent's threats. That's the entire gap.",
     "drill": "Play 3 games at 15+10 (NOT 10+0). On every move, mentally say 'checks, captures, threats' before you commit. You will play slower. Good — you have increment.",
     "success": "You correctly stop a tactic at least 3 times across the games."},
    {"day": 2, "week": 1, "phase": "Foundations", "title": "The Blunder Check (CCT)", "duration": "30 min",
     "big_idea": "Once you've decided your move, BEFORE playing it, run one final check: does this move drop a piece or allow mate?",
     "lesson": "After choosing your move, look at it as if it were already played. Now check: (a) what's hanging? (b) what tactics did I just create for the opponent (pins, forks, discovered attacks targeting my pieces)? (c) any back-rank issue? Most 800 blunders happen in moves 15-25 when you THINK you have a plan and play it without re-checking. The pre-move check costs 5 seconds. Hanging a queen costs the game.",
     "drill": "20 puzzles on chess.com 'Puzzle Rush 3-min' AND 3 rated games at 15+10. After each game, identify your single worst move. Was it a CCT failure? A blunder check failure? Or something deeper?",
     "success": "Win-rate above 50% today, OR clear identification of the recurring failure mode."},
    {"day": 3, "week": 1, "phase": "Tactics", "title": "Pattern Pack 1: Forks & Double Attacks", "duration": "40 min",
     "big_idea": "At 800-1200, ~70% of decisive moments are tactical. Pattern recognition is faster than calculation.",
     "lesson": "Four fork patterns to drill until automatic: (1) Knight fork on f7/c7 with king on e8 — happens every 5th game with the Black king uncastled. (2) Knight fork from c7 hitting king on e8 and rook on a8 (royal fork). (3) Pawn fork — pawn push attacking two pieces. (4) Queen + bishop battery on the long diagonal forking king and rook.",
     "drill": "lichess.org/training/fork — 25 puzzles minimum. THEN 2 games at 15+10 actively looking for fork opportunities, especially knight forks involving f7/f2.",
     "success": "Spot at least one fork opportunity in your live games (whether you can execute or not)."},
    {"day": 4, "week": 1, "phase": "Tactics", "title": "Pattern Pack 2: Pins, Skewers, X-rays", "duration": "40 min",
     "big_idea": "Pieces that can't move are pieces you can attack again. This is how attacks build.",
     "lesson": "Pin: piece can't move because something more valuable sits behind. Absolute pin (against king) — pinned piece is functionally captured already. Once you pin, ATTACK THE PINNED PIECE WITH MORE PIECES. A pin without follow-up is decoration. Skewer: more valuable piece in front, less valuable behind. X-ray: attack through a piece, threatening what's beyond.",
     "drill": "lichess.org/training/pin (15 puzzles) AND lichess.org/training/skewer (15 puzzles). 2 games at 15+10. In every game, ask: 'is anything pinned?' If yes, 'how do I attack the pinned piece?'",
     "success": "Execute one pin-and-pile-on combination in a real game."},
    {"day": 5, "week": 1, "phase": "Tactics", "title": "Pattern Pack 3: Discovered Attacks & Removing the Defender", "duration": "40 min",
     "big_idea": "Most 800 games are decided by tactics one player saw and the other didn't. These two patterns are particularly hidden.",
     "lesson": "Discovered attack: move one piece, reveal an attack from another. The moving piece can do ANYTHING and the discovered attack still operates. Discovered checks are most powerful. Removing the defender: target isn't sufficiently defended if you can capture or distract the defender. Common pattern: opponent's knight defends a pawn near their king; trade the knight, the pawn falls.",
     "drill": "20 mixed-tactics puzzles on chess.com. 2 games at 15+10. After each game, scan the move list for any moment where you could have removed a key defender.",
     "success": "Find one game where you missed (or executed) a discovered attack or defender-removal."},
    {"day": 6, "week": 1, "phase": "Endgame", "title": "King Activity & The Opposition", "duration": "35 min",
     "big_idea": "In endgames, your king is your strongest piece. At 800, players' kings stay on the back rank in pawn endgames — and lose drawn positions.",
     "lesson": "When queens come off, march your king to the center IMMEDIATELY. The opposition: when kings face each other on the same file/rank/diagonal with one square between, the player NOT to move has the opposition. In K+P vs K endings, having the opposition WITH your king IN FRONT of the pawn = win.",
     "drill": "Set up on lichess.org/analysis vs Stockfish: (a) White Ke6 Pe5, Black Ke8, Black to move (White wins). (b) Same but White to move (draw). (c) White Kf6 Pe5 vs Black Ke8, White to move (wins). Play each 3 times. Then 2 rated games.",
     "success": "Win or correctly draw the practice positions without help."},
    {"day": 7, "week": 1, "phase": "Review", "title": "Week 1 Audit", "duration": "60 min",
     "big_idea": "Pattern detection over 7 days reveals your true weakness. This is where rating jumps come from.",
     "lesson": "Pull every loss from this week. For each: (1) at what move did the eval flip from equal/winning to losing? (2) was that move a CCT failure? a known tactical pattern? a positional misjudgment? a time scramble? Categorize all losses. The category with the most entries is your #1 problem to fix in week 2.",
     "drill": "After audit: write 3 sentences on what you'll do differently in week 2.",
     "success": "Clear written diagnosis of your dominant failure mode."},
    {"day": 8, "week": 2, "phase": "Openings", "title": "The London System (White, complete)", "duration": "45 min",
     "big_idea": "One opening for White, played the same way against everything. Saves you 200+ memorization hours.",
     "lesson": "The setup against ANY Black response: 1.d4 2.Nf3 3.Bf4 4.e3 5.Bd3 6.c3 7.Nbd2 8.O-O. Move order can flex. Then middlegame plan: (a) Push h3 to keep your bishop. (b) Aim for e4 break. (c) If Black plays ...c5, c3 already played — solid. (d) Knight maneuver Nd2-f1-g3 to attack kingside. The London at 800-1500 is a 200-rating-point shortcut.",
     "drill": "Play 4 games as White today, ALL with the London. Don't deviate even if you see a 'tactic' on move 5. Build muscle memory for the setup.",
     "success": "All 4 games reach the standard London setup by move 8."},
    {"day": 9, "week": 2, "phase": "Openings", "title": "Caro-Kann vs e4 (Black)", "duration": "40 min",
     "big_idea": "Solid defense, no early king attacks, healthy middlegame. Less popular than Sicilian = less prep from your opponents.",
     "lesson": "1.e4 c6 2.d4 d5. Three lines: (a) Advance 3.e5 — play 3...Bf5 (NOT ...c5 yet). (b) Exchange 3.exd5 cxd5 — symmetric, develop pieces. (c) Main line 3.Nc3 dxe4 4.Nxe4 — play 4...Bf5 attacking the knight. Common idea: get your light-square bishop OUTSIDE the pawn chain before playing ...e6.",
     "drill": "Play 3 games as Black against 1.e4 with the Caro-Kann.",
     "success": "Reach move 10 in all 3 games with solid pawn structure and your light-square bishop developed."},
    {"day": 10, "week": 2, "phase": "Openings", "title": "Slav Defense vs d4 (Black)", "duration": "40 min",
     "big_idea": "The Slav pairs naturally with the Caro-Kann — same pawn structure ideas, similar middlegame plans.",
     "lesson": "1.d4 d5 2.c4 c6. (a) Keep your light-square bishop active. (b) Play ...Bf5 or ...Bg4 early. (c) Develop ...Nf6, ...e6, ...Nbd7, ...Be7, castle. (d) The break ...e5 in the middlegame opens the position when ready.",
     "drill": "Play 3 games as Black vs 1.d4. If opponent plays anything else (1.Nf3, 1.c4), respond ...d5 ...c6 anyway.",
     "success": "Comfortable Black setup vs d4 in all 3 games."},
    {"day": 11, "week": 2, "phase": "Middlegame", "title": "Find The Worst Piece", "duration": "35 min",
     "big_idea": "When you don't know what to do, improve your worst piece. This generates 80% of correct middlegame plans.",
     "lesson": "Look at your position. Which of your pieces is least useful? That's your move. Maneuvers worth knowing: (a) Knight reroute — Nb1-d2-f1-g3. (b) Bishop redeployment via fianchetto. (c) Rook lift — Ra1-a3-h3 to attack. (d) Bringing the king up in the endgame.",
     "drill": "Play 3 games at 15+10. In each middlegame, pause at move 12-15 and explicitly ask 'what's my worst piece?' Move it.",
     "success": "Identify and improve your worst piece in at least 2 of 3 games."},
    {"day": 12, "week": 2, "phase": "Middlegame", "title": "Pawn Breaks", "duration": "40 min",
     "big_idea": "Closed positions are decided by pawn breaks. If you can't break, you can't make progress.",
     "lesson": "A pawn break challenges opponent's structure, opening lines for your pieces. Common: (a) f4-f5 in king's pawn games. (b) c5 break vs isolated d-pawn. (c) e4 break after London setup. (d) ...d5 or ...e5 break for Black against d4 setups. Before breaking, check: do MY pieces benefit from the lines that open?",
     "drill": "Play 3 games. In each, identify YOUR pawn break before move 15 and PLAN for it. Execute in at least 1 game.",
     "success": "Successfully execute a pawn break that improves your position."},
    {"day": 13, "week": 2, "phase": "Middlegame", "title": "Open Files & Outposts", "duration": "35 min",
     "big_idea": "Rooks belong on open files. Knights belong on outposts.",
     "lesson": "Open file = no pawns of either color. Semi-open = no friendly pawns. When pawns trade, ASK IMMEDIATELY: which file just opened? Get a rook there before opponent does. Outpost = a square in opponent's territory where you can place a knight that can't be attacked by an enemy pawn. Outposts on the 5th, 6th rank are devastating.",
     "drill": "Play 3 games. After every pawn trade, identify the newly open file. Play to occupy it. Identify any outpost; aim a knight there.",
     "success": "Place a rook on an open file or knight on an outpost in at least 2 games."},
    {"day": 14, "week": 2, "phase": "Review", "title": "Week 2 Audit & Rating Check", "duration": "60 min",
     "big_idea": "Two weeks in. If you're not at 900+, the curriculum is correct but execution is the issue. Adjust.",
     "lesson": "Review every loss. Are you reaching the middlegame in good shape? (Opening fixed?) Are you executing tactics when they appear? (Tactics fixed?) Are you generating middlegame plans? If openings still failing, repeat days 8-10. If tactics, more puzzles daily. If middlegame plans missing, slow down — play 30+0 a few times.",
     "drill": "Run chess.com Game Review on your top 3 games this week. Note one specific lesson from each.",
     "success": "Rating up by at least 50 points OR clear plan to fix the gap."},
    {"day": 15, "week": 3, "phase": "Endgame", "title": "K+R vs K Mate", "duration": "30 min",
     "big_idea": "If you can't mate K+R vs K in under 30 seconds without thinking, you'll stalemate or hang the rook.",
     "lesson": "Technique: (1) Use rook to confine the enemy king. (2) Bring your king up to support. (3) Drive the enemy king to the edge. (4) Deliver mate with king and rook coordinating. Key: enemy king should always be either in opposition with yours OR being driven toward an edge.",
     "drill": "chess.com Endgame Trainer (or lichess analysis vs Stockfish): K+R vs K, 10 reps. Should take under 1 minute each by rep 10. Then 3 rated games.",
     "success": "Mate in <30 seconds, no stalemates."},
    {"day": 16, "week": 3, "phase": "Endgame", "title": "K+Q vs K Mate (avoiding stalemate)", "duration": "25 min",
     "big_idea": "Easier than K+R but stalemates are MORE common because the queen has so much power.",
     "lesson": "Keep the queen a knight's-move away from the enemy king. Walk queen + king together, pushing the enemy king to the edge. Deliver mate with queen supported by king. STALEMATE TRAP: when enemy king is in the corner with nowhere to go and not in check. To avoid: only deliver check on the FINAL move (when king is supported).",
     "drill": "10 reps of K+Q vs K on chess.com Endgame Trainer. Then K+Q+R vs K (3 reps).",
     "success": "10 mates, 0 stalemates."},
    {"day": 17, "week": 3, "phase": "Endgame", "title": "King + Pawn Endings", "duration": "45 min",
     "big_idea": "Most endgames reduce to K+P. Knowing them turns 'lost' positions into draws and 'drawn' positions into wins.",
     "lesson": "Three positions cold: (1) K+P vs K with opposition. (2) Square rule: passed pawn — draw imaginary square from pawn to promotion square; if king can step in, he catches it. (3) Outside passed pawn wins: in K+P vs K+P, side with pawn farther from kings usually wins.",
     "drill": "Set up on lichess: White Kc1 Pa2, Black Ke3 — Black to move, can he catch? (Yes, just barely). Try with Black king on Ke4 (no). 5 K+P vs K positions. Then 2 rated games.",
     "success": "Correctly evaluate K+P endings without engine help."},
    {"day": 18, "week": 3, "phase": "Endgame", "title": "Rook Endgames Essentials", "duration": "45 min",
     "big_idea": "50%+ of master endgames are rook endgames. Even at 800, knowing two ideas changes outcomes immediately.",
     "lesson": "(1) LUCENA (winning): K+R+P vs K+R, your pawn on 7th, your king in front. 'Building a bridge' — use rook to shield king from checks while you promote. (2) PHILIDOR (drawing): defending K+R vs K+R+P. Keep rook on 6th rank to prevent enemy king advance. When pawn pushes to 6th, swing rook BEHIND for endless checks.",
     "drill": "Set up Lucena (White Ka8 Pa7 Rh1 vs Black Ke6 Rb8 — White to move). Play 3 times. Set up Philidor and defend 3 times.",
     "success": "Win Lucena, draw Philidor, both without engine."},
    {"day": 19, "week": 3, "phase": "Endgame", "title": "Trading into the Right Endgame", "duration": "35 min",
     "big_idea": "Knowing WHICH endgame to head into is more important than playing it perfectly.",
     "lesson": "(a) Up a pawn? Trade pieces, especially queens. Pawn endings usually winning with a pawn up. (b) Down a pawn but better activity? Keep pieces ON. (c) Bishop vs knight: open positions favor bishop, closed favor knight. (d) Same-color bishops up a pawn: often drawn. Opposite-color bishops up TWO pawns: can be drawn. (e) Rook endgames are notoriously drawish.",
     "drill": "Play 3 games at 15+10. In every position with potential trades, pause and ask: 'is the resulting endgame good for me?' before initiating.",
     "success": "Make at least 2 correct trade-or-keep decisions you can justify."},
    {"day": 20, "week": 3, "phase": "Endgame", "title": "The Active King", "duration": "30 min",
     "big_idea": "Once queens are off, your king becomes a fighting piece. Activate it or lose drawn positions.",
     "lesson": "When queens trade, the king's role flips: from hiding to attacking. Active king attacks pawns, supports your own pawns to promotion, blocks opponent's pawns, dominates the enemy king. Classic 800 mistake: keeping king on g1 'safe' deep into a pawn endgame while opponent's king marches to e4 and devours pawns.",
     "drill": "3 games at 15+10. The MOMENT queens come off (or by move 25 if no queens), bring your king to the center. Make this automatic.",
     "success": "King reaches at least the 3rd or 4th rank in every endgame you reach."},
    {"day": 21, "week": 3, "phase": "Review", "title": "Week 3 Audit", "duration": "60 min",
     "big_idea": "Endgame technique is the most common cause of 'I had a winning position and lost'. Check if you're now converting.",
     "lesson": "Pull every game this week that reached an endgame (move 30+). Did you know what you were doing? Did your king activate? Did you correctly evaluate the resulting endgame before trades? If you converted at least 70% of objectively winning endgames, the endgame work is paying off.",
     "drill": "List your endgame win rate this week. Note the specific positions you lost from winning.",
     "success": "Endgame conversion rate >70% from winning positions."},
    {"day": 22, "week": 4, "phase": "Attack", "title": "Greek Gift Sacrifice (Bxh7+)", "duration": "40 min",
     "big_idea": "Most attacks against the castled king have known patterns. The Greek Gift is the most common.",
     "lesson": "Conditions: (a) Black king on g8, pawn on h7, knight NOT on f6. (b) Your bishop on d3 with clean diagonal to h7. (c) Your knight on f3 ready to jump to g5 with check. (d) Your queen ready to swing to h5. The combo: Bxh7+ Kxh7, Ng5+ Kg6 (or Kg8 or Kh6 — each has a follow-up), Qh5+ and the attack crashes through.",
     "drill": "Set up the Greek Gift starting position and play it through against Stockfish 5 times. Then 3 rated games — actively look for the conditions.",
     "success": "Identify the Greek Gift conditions in at least one game."},
    {"day": 23, "week": 4, "phase": "Attack", "title": "Pawn Storms vs Opposite-Side Castling", "duration": "40 min",
     "big_idea": "When kings castle on opposite sides, it's a race. The first pawn storm to land wins.",
     "lesson": "(a) DON'T move pawns in front of YOUR king. (b) DO push pawns toward THEIR king (g4, h4, h5). (c) Open lines via pawn trades, then bring rooks/queen to attack. The first to land a piece on the 7th rank usually wins.",
     "drill": "Play 3 games. Try to castle long once if your London allows. If your opponent castles opposite, launch the storm.",
     "success": "Execute or witness one opposite-side castling pawn storm."},
    {"day": 24, "week": 4, "phase": "Attack", "title": "Removing the King's Defenders", "duration": "40 min",
     "big_idea": "The opponent's king is defended by 2-3 specific pieces. Eliminating them = the attack lands.",
     "lesson": "Identify the defenders: usually a knight on f6 (defending h7), bishop on g7 (defending dark squares), rook on f8 (defending f7 and back rank). Plans: trade the f6 knight, provoke ...g6 to weaken h6, double rooks on the f-file. Classic Pillsbury attack: knight on e5 + bishop on h7 + queen swinging over.",
     "drill": "In your next 3 games, when on the attack, target the f6 knight first.",
     "success": "Successfully trade off opponent's key defender in one game."},
    {"day": 25, "week": 4, "phase": "Defense", "title": "Defensive Resources", "duration": "35 min",
     "big_idea": "When attacked, most 800s panic. Calm defense draws or wins more often than counter-attack.",
     "lesson": "Three defensive ideas: (1) TRADE attackers — every piece traded reduces the attack. (2) BLOCK — interpose a piece to stop a check, even temporarily losing material. (3) RUN — sometimes the king can flee to safety. When threatened with mate-in-1: (a) block the mating square, (b) capture the mating piece, (c) give check that forces the attacker to deal with you first.",
     "drill": "Solve 15 'defensive' puzzles on lichess (search 'defensive moves' theme). 2 rated games where you actively defend at least once.",
     "success": "Convert one game where you were attacked into a draw or win."},
    {"day": 26, "week": 4, "phase": "Time", "title": "Time Management at 15+10", "duration": "30 min",
     "big_idea": "At 15+10, the increment means you literally cannot run out of time if you don't waste it. But spending 4 minutes on one move costs you the game later.",
     "lesson": "Targets: (a) Opening (memorized): 5 sec/move avg. Banking 7-10 minutes for the middlegame. (b) Middlegame: 30-60 sec/move on critical moves, snap moves on obvious ones. (c) Endgame: snap if you know the technique. The 4-minute rule: never spend more than 4 minutes on a single move; if you can't decide, you're missing something — pick the safest move and move on.",
     "drill": "Play 3 games at 15+10. Track your average time per move (visible in chess.com analysis).",
     "success": "Average time per move under 50 seconds. Zero time-pressure losses."},
    {"day": 27, "week": 4, "phase": "Synthesis", "title": "Prophylaxis", "duration": "40 min",
     "big_idea": "The single biggest mental habit separating 800 from 1500: thinking about opponent's plan, not just your own.",
     "lesson": "Before each move, ask: 'If it were my opponent's move right now, what's their best move?' Then either (a) prevent it, or (b) make sure your move is more valuable than letting them play it. Examples: opponent has Ng5 with attack ideas — play h6 first. Opponent's bishop heading to a strong diagonal — block it. Opponent's rook wants the open file — race them.",
     "drill": "Play 3 games at 15+10. On every move, before deciding, articulate (in your head) opponent's #1 threat. Address it.",
     "success": "Stop at least 3 of opponent's plans across the games."},
    {"day": 28, "week": 4, "phase": "Final", "title": "Day 28 — Where Are You?", "duration": "60 min",
     "big_idea": "The 28-day rating jump tells you what worked. The pattern of remaining losses tells you what's next.",
     "lesson": "Audit: (1) Rating change vs starting 800. Hit 1100? 1200? More? Less? (2) Win rate trajectory week by week. (3) Most common loss type now vs week 1. (4) Which curriculum days felt most impactful. If you hit 1200: design next 30-day plan focused on positional play, deeper opening prep, 30+0 games. If 1000-1150: another 14 days repeating tactics + endgames. If below 1000: slow down to 30+0.",
     "drill": "Write your own next-30-day plan based on the data.",
     "success": "Clear, written next-30-day plan."},
]

PHASE_COLORS = {
    "Foundations": "#c9302c",
    "Tactics": "#d4a017",
    "Openings": "#2d5d7b",
    "Middlegame": "#6b4c93",
    "Endgame": "#4a7c59",
    "Attack": "#a83232",
    "Defense": "#456b8c",
    "Time": "#8a6d3b",
    "Synthesis": "#5a4a7a",
    "Review": "#3a3a3a",
    "Final": "#1a1a1a",
}

# ============================================================================
# CHESS.COM API
# ============================================================================

@st.cache_data(ttl=600)  # cache 10 min
def fetch_player_stats(username):
    try:
        r = requests.get(f"https://api.chess.com/pub/player/{username}/stats", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=600)
def fetch_archives(username):
    try:
        r = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("archives", [])
    except Exception as e:
        return []

@st.cache_data(ttl=600)
def fetch_recent_games(username, n_months=2):
    archives = fetch_archives(username)
    if not archives:
        return []
    # take the most recent n months
    recent_urls = archives[-n_months:]
    all_games = []
    for url in recent_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            all_games.extend(r.json().get("games", []))
        except Exception:
            continue
    # newest first
    all_games.sort(key=lambda g: g.get("end_time", 0), reverse=True)
    return all_games

# ============================================================================
# ANALYSIS
# ============================================================================

def analyze_games(games, username):
    """Return a structured breakdown of the user's recent games."""
    rapid = [g for g in games if g.get("time_class") == "rapid"]
    blitz = [g for g in games if g.get("time_class") == "blitz"]

    if not rapid:
        return None

    rows = []
    for g in rapid:
        is_white = g["white"]["username"].lower() == username.lower()
        me = g["white"] if is_white else g["black"]
        opp = g["black"] if is_white else g["white"]
        my_result = me["result"]

        # classify result
        if my_result == "win":
            outcome = "win"
        elif my_result in ("agreed", "stalemate", "repetition", "insufficient", "50move", "timevsinsufficient"):
            outcome = "draw"
        else:
            outcome = "loss"

        rows.append({
            "end_time": datetime.fromtimestamp(g.get("end_time", 0)),
            "color": "white" if is_white else "black",
            "rating": me.get("rating"),
            "opp": opp["username"],
            "opp_rating": opp.get("rating"),
            "outcome": outcome,
            "result_detail": my_result,
            "time_control": g.get("time_control", ""),
            "url": g.get("url", ""),
            "rules": g.get("rules", "chess"),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("end_time")
    return df

def loss_pattern_breakdown(df):
    if df is None or df.empty:
        return None
    losses = df[df["outcome"] == "loss"]
    counts = losses["result_detail"].value_counts().to_dict()
    return counts

# ============================================================================
# UI HELPERS
# ============================================================================

def stat_card(label, value, sub=None, accent="#d4a017"):
    st.markdown(f"""
    <div style="padding:18px 20px;border:1px solid #d4cfc4;background:#faf7f0;border-top:3px solid {accent};margin-bottom:8px;">
        <div style="font-size:9px;letter-spacing:2px;color:#6b6356;text-transform:uppercase;font-family:Georgia,serif;">{label}</div>
        <div style="font-size:28px;color:#1a1a1a;margin-top:4px;font-family:'Cormorant Garamond',Georgia,serif;line-height:1;">{value}</div>
        {f'<div style="font-size:11px;color:#8a7e6b;margin-top:4px;font-style:italic;">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# CSS
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&display=swap');

.main, .stApp { background: #f5f1e8; font-family: Georgia, serif; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1rem; max-width: 1200px; }

h1, h2, h3 { font-family: 'Cormorant Garamond', Georgia, serif !important; font-weight: 400 !important; color: #1a1a1a; }

.stTabs [data-baseweb="tab-list"] { background: #1a1a1a; padding: 0 24px; gap: 24px; }
.stTabs [data-baseweb="tab"] { color: #8a7e6b; font-family: Georgia, serif; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; padding: 12px 0; }
.stTabs [aria-selected="true"] { color: #d4a017 !important; border-bottom-color: #d4a017 !important; }

.stButton > button { font-family: Georgia, serif; letter-spacing: 1.5px; text-transform: uppercase; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# COMPUTE STATE
# ============================================================================

today = date.today()
current_day = (today - START_DATE).days + 1
current_day = max(1, min(28, current_day))
days_remaining = max(0, 28 - current_day + 1)

stats = fetch_player_stats(USERNAME)
games = fetch_recent_games(USERNAME)
df = analyze_games(games, USERNAME)

current_rating = None
if stats and "chess_rapid" in stats:
    current_rating = stats["chess_rapid"].get("last", {}).get("rating")
best_rapid = stats.get("chess_rapid", {}).get("best", {}).get("rating") if stats else None
puzzle_rating = stats.get("tactics", {}).get("highest", {}).get("rating") if stats else None

rating_change = (current_rating - START_RATING) if current_rating else 0
to_target = max(0, TARGET_RATING - current_rating) if current_rating else TARGET_RATING - START_RATING

# ============================================================================
# HEADER
# ============================================================================

st.markdown(f"""
<div style="background:#1a1a1a;color:#f5f1e8;padding:24px 32px;border-bottom:4px double #d4a017;margin:-1rem -1rem 1rem -1rem;">
  <div style="font-size:10px;letter-spacing:3px;color:#d4a017;text-transform:uppercase;">The 800 → 1200 Project · 28 Days</div>
  <h1 style="font-family:'Cormorant Garamond',Georgia,serif;font-size:36px;font-weight:400;margin:4px 0 0;letter-spacing:-0.5px;color:#f5f1e8;">
    Daily Coaching Brief
  </h1>
  <div style="font-size:12px;color:#8a7e6b;margin-top:6px;font-style:italic;">
    {USERNAME} · Day {current_day} of 28 · Auto-synced with Chess.com
  </div>
</div>
""", unsafe_allow_html=True)

# Progress bar
if current_rating:
    pct = max(0, min(100, (current_rating - START_RATING) / (TARGET_RATING - START_RATING) * 100))
    st.markdown(f"""
    <div style="margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;font-size:10px;letter-spacing:1.5px;color:#6b6356;margin-bottom:6px;">
        <span>800 START</span>
        <span style="color:#1a1a1a;font-weight:600;">{current_rating} CURRENT ({rating_change:+d})</span>
        <span>1200 TARGET</span>
      </div>
      <div style="height:6px;background:#e8e2d4;position:relative;">
        <div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#c9302c,#d4a017,#4a7c59);"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TABS
# ============================================================================

tab_today, tab_progress, tab_games, tab_curriculum = st.tabs(["TODAY", "PROGRESS", "GAMES", "CURRICULUM"])

# ===== TODAY =====
with tab_today:
    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("Day", f"{current_day} / 28", f"{days_remaining} days remaining", "#d4a017")
    with c2: stat_card("Rapid Rating", current_rating if current_rating else "—", f"Best: {best_rapid}" if best_rapid else "—", "#4a7c59")
    with c3: stat_card("To 1200", to_target if current_rating else "—", "rating points", "#c9302c")
    with c4: stat_card("Puzzles", puzzle_rating if puzzle_rating else "—", "(true ceiling signal)", "#6b4c93")

    st.markdown("<br>", unsafe_allow_html=True)

    lesson = CURRICULUM[current_day - 1]
    color = PHASE_COLORS[lesson["phase"]]

    st.markdown(f"""
    <div style="background:#faf7f0;border:1px solid #d4cfc4;padding:28px;margin-bottom:18px;">
      <div style="margin-bottom:8px;">
        <span style="background:{color};color:white;padding:3px 10px;font-size:10px;letter-spacing:2px;text-transform:uppercase;">{lesson["phase"]}</span>
        <span style="font-size:10px;color:#8a7e6b;letter-spacing:1.5px;margin-left:10px;">WEEK {lesson["week"]} · DAY {lesson["day"]} · {lesson["duration"]}</span>
      </div>
      <h2 style="font-family:'Cormorant Garamond',Georgia,serif;font-size:30px;font-weight:400;margin:8px 0 16px;">
        {lesson["title"]}
      </h2>
      <div style="border-left:3px solid #d4a017;padding-left:16px;margin-bottom:18px;font-size:14px;color:#3a3a3a;font-style:italic;">
        {lesson["big_idea"]}
      </div>
      <div style="margin-bottom:18px;">
        <div style="font-size:10px;letter-spacing:2px;color:#6b6356;text-transform:uppercase;margin-bottom:6px;">Lesson</div>
        <p style="font-size:15px;line-height:1.7;color:#1a1a1a;margin:0;">{lesson["lesson"]}</p>
      </div>
      <div style="margin-bottom:14px;padding:14px 16px;background:#fef3e8;border-left:3px solid #c9302c;">
        <div style="font-size:10px;letter-spacing:2px;color:#c9302c;text-transform:uppercase;margin-bottom:4px;">Today's Drill</div>
        <p style="font-size:14px;line-height:1.65;color:#1a1a1a;margin:0;">{lesson["drill"]}</p>
      </div>
      <div style="padding:10px 16px;background:#eaf3ed;border-left:3px solid #4a7c59;">
        <span style="font-size:10px;letter-spacing:1.5px;color:#4a7c59;text-transform:uppercase;font-weight:600;margin-right:8px;">Success</span>
        <span style="font-size:13px;color:#1a1a1a;">{lesson["success"]}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Personalized diagnostic from games
    if df is not None and not df.empty:
        recent_30 = df.tail(30)
        wins = (recent_30["outcome"] == "win").sum()
        losses = (recent_30["outcome"] == "loss").sum()
        draws = (recent_30["outcome"] == "draw").sum()
        win_rate = wins / len(recent_30) * 100 if len(recent_30) else 0

        st.markdown("### Diagnostic from your last 30 rapid games")
        d1, d2, d3 = st.columns(3)
        with d1: stat_card("Win rate", f"{win_rate:.0f}%", f"{wins}W / {draws}D / {losses}L", "#4a7c59")

        loss_breakdown = loss_pattern_breakdown(recent_30)
        if loss_breakdown:
            top_loss_reason = max(loss_breakdown.items(), key=lambda x: x[1])
            with d2: stat_card("Most common loss", top_loss_reason[0], f"{top_loss_reason[1]} games", "#c9302c")

        if "color" in recent_30.columns:
            white_wins = recent_30[(recent_30.color == "white") & (recent_30.outcome == "win")].shape[0]
            white_total = recent_30[recent_30.color == "white"].shape[0]
            black_wins = recent_30[(recent_30.color == "black") & (recent_30.outcome == "win")].shape[0]
            black_total = recent_30[recent_30.color == "black"].shape[0]
            with d3:
                w_pct = f"{white_wins/white_total*100:.0f}%" if white_total else "—"
                b_pct = f"{black_wins/black_total*100:.0f}%" if black_total else "—"
                stat_card("By color", f"W:{w_pct} / B:{b_pct}", f"{white_total} white, {black_total} black", "#6b4c93")

# ===== PROGRESS =====
with tab_progress:
    st.markdown("### Rating trajectory")
    if df is not None and not df.empty:
        # show one point per game (last 60 rapid games)
        chart_data = df.tail(60).reset_index(drop=True)
        chart_data["game_num"] = range(1, len(chart_data) + 1)

        line = alt.Chart(chart_data).mark_line(color="#1a1a1a", strokeWidth=2).encode(
            x=alt.X("end_time:T", title="Date"),
            y=alt.Y("rating:Q", title="Rating", scale=alt.Scale(zero=False)),
            tooltip=["end_time:T", "rating", "outcome", "opp", "opp_rating"]
        )
        points = alt.Chart(chart_data).mark_circle(size=60).encode(
            x="end_time:T",
            y="rating:Q",
            color=alt.Color("outcome:N", scale=alt.Scale(domain=["win", "draw", "loss"], range=["#4a7c59", "#8a7e6b", "#c9302c"])),
            tooltip=["end_time:T", "rating", "outcome", "opp", "opp_rating"]
        )
        target_rule = alt.Chart(pd.DataFrame({"y": [TARGET_RATING]})).mark_rule(strokeDash=[4, 4], color="#4a7c59").encode(y="y:Q")
        thousand_rule = alt.Chart(pd.DataFrame({"y": [1000]})).mark_rule(strokeDash=[2, 4], color="#8a7e6b").encode(y="y:Q")
        chart = (line + points + target_rule + thousand_rule).properties(height=350)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No rapid games found yet on the API. Play a few and refresh.")

    st.markdown("### Curriculum map")
    cols_per_row = 7
    for week in range(1, 5):
        st.markdown(f"**Week {week}**")
        cols = st.columns(7)
        week_days = [d for d in CURRICULUM if d["week"] == week]
        for i, d in enumerate(week_days):
            with cols[i]:
                is_today = d["day"] == current_day
                is_past = d["day"] < current_day
                color = PHASE_COLORS[d["phase"]]
                bg = color if is_past else ("#fef3e8" if is_today else "#faf7f0")
                txt = "white" if is_past else "#1a1a1a"
                border = "2px solid #d4a017" if is_today else "1px solid #d4cfc4"
                st.markdown(f"""
                <div style="padding:8px;background:{bg};border:{border};text-align:center;min-height:60px;">
                  <div style="font-size:10px;color:{txt};opacity:0.7;">D{d["day"]}</div>
                  <div style="font-size:10px;color:{txt};margin-top:3px;line-height:1.2;">{d["phase"]}</div>
                </div>
                """, unsafe_allow_html=True)

# ===== GAMES =====
with tab_games:
    st.markdown("### Recent rapid games")
    if df is not None and not df.empty:
        display = df.sort_values("end_time", ascending=False).head(25).copy()
        display["date"] = display["end_time"].dt.strftime("%b %d %H:%M")
        display["result"] = display["outcome"].map({"win": "✓ Win", "draw": "= Draw", "loss": "✗ Loss"})
        display["opponent"] = display.apply(lambda r: f"{r['opp']} ({r['opp_rating']})", axis=1)
        show = display[["date", "color", "result", "result_detail", "rating", "opponent", "url"]].copy()
        show.columns = ["Date", "Color", "Result", "Detail", "My Rating", "Opponent", "Link"]
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            column_config={"Link": st.column_config.LinkColumn("Link", display_text="Open ↗")}
        )

        st.markdown("### How you've been losing")
        loss_breakdown = loss_pattern_breakdown(df.tail(30))
        if loss_breakdown:
            cols = st.columns(min(len(loss_breakdown), 5))
            for i, (reason, count) in enumerate(sorted(loss_breakdown.items(), key=lambda x: -x[1])):
                with cols[i % 5]:
                    stat_card(reason, count, "games", "#c9302c")
            st.caption("'timeout' and 'resigned' are conversion-failure signals. 'checkmated' with high material count = king-safety issue.")
    else:
        st.info("No games loaded.")

# ===== CURRICULUM =====
with tab_curriculum:
    st.markdown("### Full 28-day plan")
    selected_day = st.selectbox(
        "Jump to day:",
        options=[d["day"] for d in CURRICULUM],
        format_func=lambda d: f"Day {d} · {CURRICULUM[d-1]['title']}",
        index=current_day - 1,
    )
    d = CURRICULUM[selected_day - 1]
    color = PHASE_COLORS[d["phase"]]
    st.markdown(f"""
    <div style="background:#faf7f0;border:1px solid #d4cfc4;padding:24px;">
      <span style="background:{color};color:white;padding:3px 10px;font-size:10px;letter-spacing:2px;text-transform:uppercase;">{d["phase"]}</span>
      <span style="font-size:10px;color:#8a7e6b;margin-left:10px;letter-spacing:1.5px;">WEEK {d["week"]} · {d["duration"]}</span>
      <h2 style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:400;margin:10px 0 14px;">
        Day {d["day"]} · {d["title"]}
      </h2>
      <div style="border-left:3px solid #d4a017;padding-left:14px;margin-bottom:14px;font-size:13px;color:#3a3a3a;font-style:italic;">
        {d["big_idea"]}
      </div>
      <div style="margin-bottom:14px;">
        <div style="font-size:10px;letter-spacing:1.5px;color:#6b6356;text-transform:uppercase;margin-bottom:4px;">Lesson</div>
        <p style="font-size:14px;line-height:1.7;color:#1a1a1a;margin:0;">{d["lesson"]}</p>
      </div>
      <div style="margin-bottom:12px;padding:10px 14px;background:#fef3e8;border-left:3px solid #c9302c;">
        <div style="font-size:10px;letter-spacing:1.5px;color:#c9302c;text-transform:uppercase;margin-bottom:4px;">Drill</div>
        <p style="font-size:13px;line-height:1.65;margin:0;">{d["drill"]}</p>
      </div>
      <div style="padding:8px 14px;background:#eaf3ed;border-left:3px solid #4a7c59;">
        <span style="font-size:10px;letter-spacing:1.5px;color:#4a7c59;text-transform:uppercase;font-weight:600;margin-right:8px;">Success</span>
        <span style="font-size:12px;color:#1a1a1a;">{d["success"]}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Refresh button
st.markdown("---")
col_a, col_b = st.columns([5, 1])
with col_b:
    if st.button("↻ Refresh data"):
        st.cache_data.clear()
        st.rerun()
with col_a:
    st.caption(f"Data auto-cached for 10 minutes. Last load: {datetime.now().strftime('%H:%M:%S')}")
