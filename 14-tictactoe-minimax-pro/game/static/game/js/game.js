// Game State
let currentGameId = null;
let currentMode = 'pve_hard';
let isGameActive = false;
let soundEnabled = true;
let scores = {
    x: parseInt(localStorage.getItem('ttt_score_x') || '0', 10),
    o: parseInt(localStorage.getItem('ttt_score_o') || '0', 10),
    ties: parseInt(localStorage.getItem('ttt_score_ties') || '0', 10)
};

// Web Audio API Synthesizer
let audioCtx = null;

function initAudio() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            audioCtx = new AudioContext();
        }
    }
}

function playSound(type) {
    if (!soundEnabled) return;
    try {
        initAudio();
        if (!audioCtx) return;
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const now = audioCtx.currentTime;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);

        if (type === 'x_move') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.08);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
            osc.start(now);
            osc.stop(now + 0.08);
        } else if (type === 'o_move') {
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(330, now);
            osc.frequency.exponentialRampToValueAtTime(220, now + 0.1);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
            osc.start(now);
            osc.stop(now + 0.1);
        } else if (type === 'win') {
            osc.type = 'square';
            osc.frequency.setValueAtTime(523.25, now);
            osc.frequency.setValueAtTime(659.25, now + 0.1);
            osc.frequency.setValueAtTime(783.99, now + 0.2);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
            osc.start(now);
            osc.stop(now + 0.35);
        } else if (type === 'draw') {
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(260, now);
            osc.frequency.exponentialRampToValueAtTime(130, now + 0.2);
            gain.gain.setValueAtTime(0.18, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
            osc.start(now);
            osc.stop(now + 0.2);
        }
    } catch (e) {
        // Audio error silently ignored
    }
}

// DOM Elements
const boardEl = document.getElementById('board');
const cells = document.querySelectorAll('.cell');
const statusBanner = document.getElementById('turn-text');
const scoreXEl = document.getElementById('score-x');
const scoreOEl = document.getElementById('score-o');
const scoreTiesEl = document.getElementById('score-ties');
const cardX = document.getElementById('card-x');
const cardO = document.getElementById('card-o');
const cardTies = document.getElementById('card-ties');
const nameO = document.getElementById('name-o');
const restartBtn = document.getElementById('restart-btn');
const resetScoreBtn = document.getElementById('reset-score-btn');
const soundBtn = document.getElementById('sound-btn');
const soundIcon = document.getElementById('sound-icon');
const modeBtns = document.querySelectorAll('.mode-btn');

function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function updateScoreboardUI() {
    scoreXEl.textContent = scores.x;
    scoreOEl.textContent = scores.o;
    scoreTiesEl.textContent = scores.ties;
    localStorage.setItem('ttt_score_x', scores.x);
    localStorage.setItem('ttt_score_o', scores.o);
    localStorage.setItem('ttt_score_ties', scores.ties);
}

function resetScores() {
    scores = { x: 0, o: 0, ties: 0 };
    updateScoreboardUI();
    startNewGame();
}

function setTurnIndicator(turn) {
    if (turn === 'X') {
        cardX.classList.add('active-turn');
        cardO.classList.remove('active-turn');
        if (currentMode === 'pvp') {
            statusBanner.textContent = "O'yinchi 1 (X) navbati";
        } else {
            statusBanner.textContent = "Sizning navbatingiz (X)";
        }
    } else {
        cardO.classList.add('active-turn');
        cardX.classList.remove('active-turn');
        if (currentMode === 'pvp') {
            statusBanner.textContent = "O'yinchi 2 (O) navbati";
        } else {
            statusBanner.textContent = "Bot o'ylamoqda...";
        }
    }
}

async function startNewGame() {
    try {
        isGameActive = false;
        cells.forEach(c => {
            c.textContent = '';
            c.className = 'cell';
        });

        // Update name for player O
        if (currentMode === 'pvp') {
            nameO.textContent = "O'yinchi 2 (O)";
        } else {
            nameO.textContent = "Bot (O)";
        }

        const res = await fetch(`/api/new/?mode=${encodeURIComponent(currentMode)}`);
        const data = await res.json();
        
        currentGameId = data.id;
        isGameActive = true;
        setTurnIndicator(data.turn);
    } catch (err) {
        console.error("Yangi o'yin boshlashda xatolik:", err);
        statusBanner.textContent = "Tarmoq xatosi! Qaytadan urinib ko'ring.";
    }
}

async function handleCellClick(e) {
    const cell = e.target.closest('.cell');
    if (!cell || !isGameActive) return;

    const index = parseInt(cell.dataset.index, 10);
    if (cell.classList.contains('taken')) return;

    // Immediately render player's X locally
    cell.textContent = '✕';
    cell.classList.add('taken', 'x');
    playSound('x_move');

    isGameActive = false;
    statusBanner.textContent = currentMode === 'pvp' ? "Navbat uzatilmoqda..." : "Bot o'ylamoqda...";

    try {
        const res = await fetch('/api/move/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                game_id: currentGameId,
                index: index
            })
        });

        const data = await res.json();
        if (!res.ok) {
            alert(data.error || "Xatolik yuz berdi");
            isGameActive = true;
            return;
        }

        // Render board from response
        renderBoard(data.board);

        if (data.bot_move !== null && data.bot_move !== undefined) {
            playSound('o_move');
        }

        // Check outcome
        if (data.winner) {
            handleGameOver(data.winner, data.winning_line);
        } else {
            isGameActive = true;
            setTurnIndicator(data.turn);
        }

    } catch (err) {
        console.error("Yurishni yuborishda xatolik:", err);
        isGameActive = true;
    }
}

function renderBoard(board) {
    board.forEach((val, i) => {
        const cell = cells[i];
        if (val === 'X') {
            cell.textContent = '✕';
            cell.className = 'cell taken x';
        } else if (val === 'O') {
            cell.textContent = '○';
            cell.className = 'cell taken o';
        } else {
            cell.textContent = '';
            cell.className = 'cell';
        }
    });
}

function handleGameOver(winner, winningLine) {
    isGameActive = false;
    cardX.classList.remove('active-turn');
    cardO.classList.remove('active-turn');

    if (winner === 'DRAW') {
        statusBanner.textContent = "🤝 Durang! Hech kim yengilmadi.";
        scores.ties += 1;
        playSound('draw');
    } else if (winner === 'X') {
        const winnerName = currentMode === 'pvp' ? "O'yinchi 1 (X)" : "Siz";
        statusBanner.textContent = `🎉 Tabriklaymiz! ${winnerName} g'alaba qozondi!`;
        scores.x += 1;
        playSound('win');
    } else if (winner === 'O') {
        const winnerName = currentMode === 'pvp' ? "O'yinchi 2 (O)" : "Bot (O)";
        statusBanner.textContent = `🤖 ${winnerName} g'alaba qozondi!`;
        scores.o += 1;
        playSound('win');
    }

    if (winningLine && Array.isArray(winningLine)) {
        winningLine.forEach(idx => {
            cells[idx].classList.add('winning');
        });
    }

    updateScoreboardUI();
}

// Event Listeners
boardEl.addEventListener('click', handleCellClick);
restartBtn.addEventListener('click', startNewGame);
resetScoreBtn.addEventListener('click', resetScores);

soundBtn.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    soundIcon.textContent = soundEnabled ? '🔊' : '🔇';
});

modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        startNewGame();
    });
});

// Init
updateScoreboardUI();
startNewGame();
