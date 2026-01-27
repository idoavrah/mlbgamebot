import { tableFromIPC } from 'https://cdn.jsdelivr.net/npm/apache-arrow@18.0.0/+esm';

let manifest = {};
let dates = [];
let currentDate = "";

const datePicker = document.getElementById("date-picker");
const globalPeekBtn = document.getElementById("global-peek-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const gameList = document.getElementById("game-list");
const template = document.getElementById("game-card-template");

async function init() {
  try {
    const response = await fetch("data/games.json");
    manifest = await response.json();
    dates = Object.keys(manifest).sort();

    // Default to latest
    currentDate = dates[dates.length - 1];

    // URL override
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    if (dateParam) {
        currentDate = dateParam;
    }
    
    // Set picker bounds (optional, but good UX)
    if (dates.length > 0) {
        datePicker.min = dates[0];
        datePicker.max = dates[dates.length - 1];
    }

    updateUI();

    window.addEventListener('popstate', () => {
        const params = new URLSearchParams(window.location.search);
        const d = params.get('date');
        if (d) {
            currentDate = d;
            updateUI(false);
        }
    });

    datePicker.addEventListener("change", (e) => {
        currentDate = e.target.value;
        updateUI(true);
    });

    prevBtn.addEventListener("click", () => {
        let target = null;
        const idx = dates.indexOf(currentDate);
        if (idx !== -1) {
            if (idx > 0) target = dates[idx - 1];
        } else {
            // Find closest < currentDate
            for (let i = dates.length - 1; i >= 0; i--) {
                if (dates[i] < currentDate) {
                    target = dates[i];
                    break;
                }
            }
        }
        if (target) {
            currentDate = target;
            updateUI(true);
        }
    });

    nextBtn.addEventListener("click", () => {
        let target = null;
        const idx = dates.indexOf(currentDate);
        if (idx !== -1) {
            if (idx < dates.length - 1) target = dates[idx + 1];
        } else {
            // Find closest > currentDate
            for (let i = 0; i < dates.length; i++) {
                if (dates[i] > currentDate) {
                    target = dates[i];
                    break;
                }
            }
        }
        if (target) {
            currentDate = target;
            updateUI(true);
        }
    });

    // Global Peek - Hold Interaction
    const reveal = () => {
        document.body.classList.add("show-scores");
        globalPeekBtn.classList.add("active");
    };
    const hide = () => {
        document.body.classList.remove("show-scores");
        globalPeekBtn.classList.remove("active");
    };

    globalPeekBtn.addEventListener("mousedown", reveal);
    globalPeekBtn.addEventListener("mouseup", hide);
    globalPeekBtn.addEventListener("mouseleave", hide);
    globalPeekBtn.addEventListener("touchstart", (e) => {
        e.preventDefault(); 
        reveal();
    });
    globalPeekBtn.addEventListener("touchend", hide);

  } catch (error) {
    console.error("Failed to initialize:", error);
    gameList.innerHTML = `<div class="error">Failed to load games manifest.</div>`;
  }
}

async function updateUI(shouldPushState = false) {
  const date = currentDate;
  datePicker.value = date;

  if (shouldPushState) {
      const url = new URL(window.location);
      if (url.searchParams.get('date') !== date) {
          url.searchParams.set('date', date);
          window.history.pushState({}, '', url);
      }
  }

  // Clear current list and show loader
  gameList.innerHTML = '';

  const gameFiles = manifest[date];
  
  if (!gameFiles) {
      gameList.innerHTML = "<p>No games recorded for this date.</p>";
      return;
  }
  
  const gamesData = [];

  try {
    for (const file of gameFiles) {
      const data = await loadFeather(file);
      if (data) {
        // Feather file might have many rows (play-by-play),
        // but the last row usually has the final scores and scores for the game.
        const lastRow = data[data.length - 1];
        gamesData.push(lastRow);
      }
    }

    renderGames(gamesData);
  } catch (error) {
    console.error("Error loading games:", error);
    gameList.innerHTML = `<div class="error">Error loading game data for ${date}.</div>`;
  }
}

// ... loadFeather remains same ...
async function loadFeather(filePath) {
    try {
        const response = await fetch(filePath + '?t=' + Date.now());
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const buffer = await response.arrayBuffer();
        
        const table = tableFromIPC(new Uint8Array(buffer));
        
        const items = [];
        for (let i = 0; i < table.numRows; i++) {
            items.push(table.get(i).toJSON());
        }
        return items;
    } catch (error) {
        console.error(`Error parsing ${filePath}:`, error);
        return null;
    }
}

function renderGames(games) {
  gameList.innerHTML = "";

  if (games.length === 0) {
    gameList.innerHTML = "<p>No games recorded for this date.</p>";
    return;
  }

  games.forEach((game, index) => {
    const clone = template.content.cloneNode(true);
    
    // Meta Data
    const seriesDesc = game.seriesDescription || "Regular Season";
    clone.querySelector(".series-description").textContent = seriesDesc;
    
    clone.querySelector(".game-info-text").textContent = game.gameDescription || "";
    clone.querySelector(".game-venue").textContent = game.venue || "";

    // Home Team Data
    clone.querySelector(".home-logo").src = `images/${game.homeTeam}.png`;
    clone.querySelector(".home-logo").alt = game.homeTeam;
    clone.querySelector(".home-name").textContent = game.homeTeam;
    clone.querySelector(".home-score").textContent = game.homeFinalScore;

    // Away Team Data
    clone.querySelector(".away-logo").src = `images/${game.awayTeam}.png`;
    clone.querySelector(".away-logo").alt = game.awayTeam;
    clone.querySelector(".away-name").textContent = game.awayTeam;
    clone.querySelector(".away-score").textContent = game.awayFinalScore;

    // Metrics (0-10 scale)
    const thrill = parseFloat(game.thrillScore) || 0;
    const offense = parseFloat(game.offenseScore) || 0;
    const defense = parseFloat(game.defenseScore) || 0;

    const thrillEl = clone.querySelector(".thrill-fill");
    thrillEl.className = `gauge-fill ${getGaugeClass(thrill)}`;
    thrillEl.style.width = `${thrill * 10}%`;
    clone.querySelector(".thrill-value").textContent = thrill.toFixed(1);

    const offenseEl = clone.querySelector(".offense-fill");
    offenseEl.className = `gauge-fill ${getGaugeClass(offense)}`;
    offenseEl.style.width = `${offense * 10}%`;
    clone.querySelector(".offense-value").textContent = offense.toFixed(1);

    const defenseEl = clone.querySelector(".defense-fill");
    defenseEl.className = `gauge-fill ${getGaugeClass(defense)}`;
    defenseEl.style.width = `${defense * 10}%`;
    clone.querySelector(".defense-value").textContent = defense.toFixed(1);

    // Removed series description from footer as it moved to title? 
    // Actually let's keep it in the card but styled as "title".
    // We already set it above .series-description
    
    // Stagger animation
    const card = clone.querySelector(".game-card");
    card.style.animationDelay = `${index * 0.05}s`; // Faster stagger

    gameList.appendChild(clone);
  });
}

// ... formatDate removed as date picker handles display ...

function getGaugeClass(score) {
    if (score < 2.5) return 'gauge-tier-1';
    if (score < 5.0) return 'gauge-tier-2';
    if (score < 7.5) return 'gauge-tier-3';
    return 'gauge-tier-4';
}

init();
