import { tableFromIPC } from 'https://cdn.jsdelivr.net/npm/apache-arrow@18.0.0/+esm';
import { FavoritesManager } from './favorites.js';

let manifest = {};
let dates = [];
let currentDate = "";
const favoritesManager = new FavoritesManager();

const yearSelect = document.getElementById("year-select");
const monthSelect = document.getElementById("month-select");
const daySelect = document.getElementById("day-select");
const globalPeekBtn = document.getElementById("global-peek-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const gameList = document.getElementById("game-list");
const template = document.getElementById("game-card-template");

// Favorites UI Elements
const favoritesBtn = document.getElementById("favorites-btn");
const favoritesMenu = document.getElementById("favorites-menu");
const favoritesList = document.getElementById("favorites-list");

function initFavoritesUI() {
    // Populate list
    const teams = favoritesManager.getAllTeams();
    favoritesList.innerHTML = '';
    
    teams.forEach(team => {
        const div = document.createElement("div");
        div.className = "fav-item";
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = `fav-${team.replace(/\s+/g, '-')}`;
        checkbox.checked = favoritesManager.isFavorite(team);
        
        const label = document.createElement("label");
        label.htmlFor = checkbox.id;
        label.textContent = team;
        
        div.appendChild(checkbox);
        div.appendChild(label);
        favoritesList.appendChild(div);
        
        // Interaction
        const toggle = () => {
            favoritesManager.toggleFavorite(team);
            checkbox.checked = favoritesManager.isFavorite(team); // Ensure state
            updateFavoritesBtnState();
            // Re-render games if we are viewing them to update sort order
            updateUI(false); 
        };

        checkbox.addEventListener("change", (e) => {
            e.stopPropagation(); // Prevent double trigger if div has click
            toggle();
        });
        
        // Allow clicking the row too
        div.addEventListener("click", (e) => {
            if (e.target !== checkbox && e.target !== label) {
                checkbox.checked = !checkbox.checked;
                toggle();
            }
        });
    });

    // Toggle Menu
    favoritesBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        favoritesMenu.classList.toggle("hidden");
    });

    // Body click closes menu
    document.body.addEventListener("click", (e) => {
        if (!favoritesMenu.contains(e.target) && e.target !== favoritesBtn && !favoritesBtn.contains(e.target)) {
            favoritesMenu.classList.add("hidden");
        }
    });

    // Stop propagation inside menu
    favoritesMenu.addEventListener("click", (e) => {
        e.stopPropagation();
    });

    updateFavoritesBtnState();
}

function updateFavoritesBtnState() {
    const hasFavorites = favoritesManager.getFavorites().length > 0;
    if (hasFavorites) {
        favoritesBtn.classList.add("active");
    } else {
        favoritesBtn.classList.remove("active");
    }
}

async function init() {
  initFavoritesUI();

  try {
    const response = await fetch(`data/games.json?v=${new Date().getTime()}`);
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
    


    populateDateSelectors();
    await updateUI();
    handleRouting();

    window.addEventListener('popstate', () => {
        const params = new URLSearchParams(window.location.search);
        
        // Handle Date Change
        const d = params.get('date');
        if (d && d !== currentDate) {
            currentDate = d;
            updateUI(false);
        }
        
        // Handle Routing (Details vs List)
        handleRouting();
    });

    function populateDateSelectors() {
        // Populate Years
        const years = new Set();
        Object.keys(manifest).forEach(dateStr => {
            years.add(dateStr.split('-')[0]);
        });
        const curY = currentDate ? currentDate.split('-')[0] : new Date().getFullYear().toString();
        years.add(curY);
        const sortedYears = Array.from(years).sort().reverse();
        
        yearSelect.innerHTML = '';
        sortedYears.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year;
            opt.textContent = year;
            yearSelect.appendChild(opt);
        });

        // Populate Months (Feb-Nov)
        const months = [
            { val: "02", name: "Feb" }, { val: "03", name: "Mar" }, 
            { val: "04", name: "Apr" }, { val: "05", name: "May" }, 
            { val: "06", name: "Jun" }, { val: "07", name: "Jul" }, 
            { val: "08", name: "Aug" }, { val: "09", name: "Sep" }, 
            { val: "10", name: "Oct" }, { val: "11", name: "Nov" }
        ];
        
        monthSelect.innerHTML = '';
        months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.val;
            opt.textContent = m.name;
            monthSelect.appendChild(opt);
        });

        // Populate Days (1-31)
        daySelect.innerHTML = '';
        for (let i = 1; i <= 31; i++) {
            const val = i.toString().padStart(2, '0');
            const opt = document.createElement('option');
            opt.value = val;
            opt.textContent = i;
            daySelect.appendChild(opt);
        }
    }

    function handleDateSelectChange() {
        const y = yearSelect.value;
        const m = monthSelect.value;
        const d = daySelect.value;
        const newDate = `${y}-${m}-${d}`;
        
        // COMPLETELY REPLACE params: Create clean URL with only date
        const url = new URL(window.location.origin + window.location.pathname);
        url.searchParams.set('date', newDate);
        
        window.history.pushState({}, '', url);
        currentDate = newDate;
        
        // Update list and ensure we are in List View
        updateUI(false).then(() => handleRouting());
    }

    yearSelect.addEventListener("change", handleDateSelectChange);
    monthSelect.addEventListener("change", handleDateSelectChange);
    daySelect.addEventListener("change", handleDateSelectChange);

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
            const url = new URL(window.location.origin + window.location.pathname);
            url.searchParams.set('date', target);
            window.history.pushState({}, '', url);
            currentDate = target;
            updateUI(false).then(() => handleRouting());
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
            const url = new URL(window.location.origin + window.location.pathname);
            url.searchParams.set('date', target);
            window.history.pushState({}, '', url);
            currentDate = target;
            updateUI(false).then(() => handleRouting());
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
  
  if (date) {
      const [y, m, d] = date.split('-');
      if (yearSelect && yearSelect.value !== y) yearSelect.value = y;
      if (monthSelect && monthSelect.value !== m) monthSelect.value = m;
      if (daySelect && daySelect.value !== d) daySelect.value = d;
  }

  if (shouldPushState) {
      const url = new URL(window.location);
      if (url.searchParams.get('date') !== date) {
          url.searchParams.set('date', date);
          window.history.pushState({}, '', url);
      }
  }

  // Clear current list and show loader
  gameList.innerHTML = '';
  // Re-add loader manually if needed or just wait for renderGames to clear it
  gameList.innerHTML = `
        <div class="loader">
        </div>`;

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
        // Attach filePath for detailed view
        lastRow.filePath = file;
        gamesData.push(lastRow);
      }
    }

    // Sort: Favorites First
    gamesData.sort((a, b) => {
        const aFav = favoritesManager.isFavorite(a.homeTeam) || favoritesManager.isFavorite(a.awayTeam);
        const bFav = favoritesManager.isFavorite(b.homeTeam) || favoritesManager.isFavorite(b.awayTeam);
        
        if (aFav && !bFav) return -1;
        if (!aFav && bFav) return 1;
        
        // Secondary sort: maybe by thrill score? Defaulting to original order (often time/id based)
        return 0;
    });

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
    
    // Check if favorite game
    const isFav = favoritesManager.isFavorite(game.homeTeam) || favoritesManager.isFavorite(game.awayTeam);
    if (isFav) {
        clone.querySelector(".game-card").classList.add("favorite-game");
    }

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
    
    // Separator Click -> Details
    const separator = clone.querySelector(".matchup-separator");
    separator.style.cursor = "pointer";
    separator.title = "View Game Details";
    separator.addEventListener("click", (e) => {
        e.stopPropagation();
        openGameDetails(game);
    });

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

// --- Routing & View Logic ---
const detailsView = document.getElementById("game-details-view");
const backBtn = document.getElementById("back-btn");
const pbpBody = document.getElementById("play-by-play-body");
const container = document.querySelector(".container header").parentNode; 

const mainHeader = document.querySelector("header");
const gameListSection = document.getElementById("game-list"); 

function handleRouting() {
    const params = new URLSearchParams(window.location.search);
    const gamePk = params.get('gamePk');
    
    if (gamePk) {
        showDetailsView(gamePk);
    } else {
        showListView();
    }
}

function showListView() {
    detailsView.classList.add("hidden");
    // mainHeader.classList.remove("hidden"); // Navbar stays visible
    gameListSection.classList.remove("hidden");
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

async function showDetailsView(gamePk) {
    // Hide List
    // mainHeader.classList.add("hidden"); // Navbar stays visible
    gameListSection.classList.add("hidden");
    detailsView.classList.remove("hidden");
    
    let filePath = null;
    let fallbackPath = `data/${currentDate.split('-')[0]}/${currentDate}-${gamePk}.ftr`;

    // 1. Try current date
    if (manifest[currentDate]) {
        filePath = manifest[currentDate].find(p => p.includes(gamePk));
    }
    
    // 2. Global Search in Manifest (if reload on different date or direct link)
    if (!filePath) {
        for (const dateKey in manifest) {
            const found = manifest[dateKey].find(p => p.includes(gamePk));
            if (found) {
                filePath = found;
                currentDate = dateKey; // Update current date context if found elsewhere
                break;
            }
        }
    }

    if (!filePath) filePath = fallbackPath; 

    await loadAndRenderDetails(filePath);
}

// Back Button
backBtn.addEventListener("click", () => {
    window.history.back();
});

// Scoring Toggle
const scoreToggle = document.getElementById("score-plays-toggle");
if (scoreToggle) {
    scoreToggle.addEventListener("change", (e) => {
        pbpBody.classList.toggle("show-scoring-only", e.target.checked);
    });
}

async function loadAndRenderDetails(filePath) {
    pbpBody.innerHTML = '<tr><td colspan="3" class="loader"><div class="spinner"></div></td></tr>';
    
    // Reset toggle state
    if (scoreToggle) {
        scoreToggle.checked = false;
        pbpBody.classList.remove("show-scoring-only");
    }

    // Clear header
    document.getElementById("details-home-team").textContent = "...";
    document.getElementById("details-away-team").textContent = "...";
    document.getElementById("details-meta").textContent = "";

    try {
        const rows = await loadFeather(filePath);
        if (!rows || rows.length === 0) throw new Error("No data");

        // Extract Meta
        // Extract Meta
        const metaRow = rows[rows.length - 1]; 
        const firstRow = rows[0];
        
        const homeTeam = firstRow.homeTeam || metaRow.homeTeam || "Home";
        const awayTeam = firstRow.awayTeam || metaRow.awayTeam || "Away";
        
        const homeScore = metaRow.homeScore !== undefined ? metaRow.homeScore : "--";
        const awayScore = metaRow.awayScore !== undefined ? metaRow.awayScore : "--";
        
        // Update DOM
        document.getElementById("details-home-team").textContent = homeTeam;
        document.getElementById("details-away-team").textContent = awayTeam;

        // Logos
        const hLogo = document.getElementById("details-home-logo");
        const aLogo = document.getElementById("details-away-logo");
        if(hLogo) hLogo.src = `images/${homeTeam}.png`;
        if(aLogo) aLogo.src = `images/${awayTeam}.png`;

        // Scores
        const hScoreEl = document.getElementById("details-home-score");
        const aScoreEl = document.getElementById("details-away-score");
        if(hScoreEl) hScoreEl.textContent = homeScore;
        if(aScoreEl) aScoreEl.textContent = awayScore;
        
        const venue = firstRow.venue || "";
        const desc = firstRow.gameDescription || "";
        
        document.getElementById("details-meta").textContent = `${desc} • ${venue}`;

        renderPlayByPlay(rows);
    } catch (e) {
        console.error("Details error:", e);
        pbpBody.innerHTML = `<tr><td colspan="3" class="error">Failed to load detailed data.</td></tr>`;
    }
}

function renderPlayByPlay(rows) {
    pbpBody.innerHTML = "";
    
    if (!rows || rows.length === 0) {
        pbpBody.innerHTML = "<tr><td colspan='3'>No play-by-play data available.</td></tr>";
        return;
    }

    const filters = [
        "batter timeout",
        "coaching visit",
        "defensive substitution",
        "defensive switch",
        "end of",
        "game advisory",
        "injury delay",
        "mound visit", 
        "offensive substitution", 
        "pitching change",
        "pitching substitution", 
        "scheduled",
        "start of",
        "status change", 
        "video review",
        "warmup",
    ];

    let prevHome = 0;
    let prevAway = 0;
    let firstRowRendered = false;

    rows.forEach(row => {
        if (!row) return;

        // original text for display
        const description = row.result || row.event || "";
        
        // AGGRESSIVE FILTER: Check ALL string values in the row
        const rowValues = Object.values(row)
            .filter(v => typeof v === 'string')
            .map(v => v.toLowerCase());
            
        const shouldExclude = filters.some(f => 
            rowValues.some(val => val.includes(f))
        );
        
        if (shouldExclude) return;

        const isTop = row.half === "top";
        const arrow = isTop ? "▲" : "▼";
        const inning = row.inning || "";
        const home = row.homeScore || 0;
        const away = row.awayScore || 0;
        
        const tr = document.createElement("tr");
        
        // Score Change Detection
        // Only highlight if scores changed AND it's not the very first visual row (unless 0-0 changed to something else immediately? No usually starts 0-0)
        // If row 1 is 1-0, highlight it? Yes maybe.
        // Let's just compare to prev.
        const scoreChanged = (home !== prevHome || away !== prevAway) && firstRowRendered;
        const rowClass = scoreChanged ? "score-change" : "";
        if (scoreChanged) tr.classList.add("score-change");

        // Inning Column
        const tdInning = document.createElement("td");
        tdInning.className = "pbp-inning-cell";
        tdInning.innerHTML = `<div class="inning-content"><span class="inning-arrow">${arrow}</span> ${inning}</div>`;
        tr.appendChild(tdInning);

        // Score Column
        const tdScore = document.createElement("td");
        tdScore.className = "pbp-score-cell";
        tdScore.innerHTML = `<span class="score-box">${away}-${home}</span>`;
        if (scoreChanged) tdScore.classList.add("score-change");
        tr.appendChild(tdScore);

        // Desc Column
        const tdDesc = document.createElement("td");
        tdDesc.className = "pbp-desc-cell";
        tdDesc.textContent = description;
        tr.appendChild(tdDesc);

        pbpBody.appendChild(tr);

        // Update tracking
        prevHome = home;
        prevAway = away;
        firstRowRendered = true;
    });
}


// Redirect old function call to routing
window.openGameDetails = function(game) {
    const pk = game.gamePk;
    if (pk) {
        // Reset search params to only include gamePk
        const url = new URL(window.location.protocol + "//" + window.location.host + window.location.pathname);
        url.searchParams.set('gamePk', pk);
        
        window.history.pushState({}, '', url);
        handleRouting();
    }
};

init();
