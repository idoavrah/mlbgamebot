import { tableFromIPC } from "https://cdn.jsdelivr.net/npm/apache-arrow@18.0.0/+esm";
import { FavoritesManager } from "./favorites.js";

let dates = [];
let currentDate = "";
let gamesByDate = {}; // cache: date -> summary rows
const favoritesManager = new FavoritesManager();

const TEAM_STRUCTURE = {
  "Arizona Diamondbacks": ["Arizona", "Diamondbacks"],
  "Atlanta Braves": ["Atlanta", "Braves"],
  "Baltimore Orioles": ["Baltimore", "Orioles"],
  "Boston Red Sox": ["Boston", "Red Sox"],
  "Chicago Cubs": ["Chicago", "Cubs"],
  "Chicago White Sox": ["Chicago", "White Sox"],
  "Cincinnati Reds": ["Cincinnati", "Reds"],
  "Cleveland Guardians": ["Cleveland", "Guardians"],
  "Cleveland Indians": ["Cleveland", "Indians"],
  "Colorado Rockies": ["Colorado", "Rockies"],
  "Detroit Tigers": ["Detroit", "Tigers"],
  "Houston Astros": ["Houston", "Astros"],
  "Kansas City Royals": ["Kansas City", "Royals"],
  "Los Angeles Angels": ["Los Angeles", "Angels"],
  "Los Angeles Dodgers": ["Los Angeles", "Dodgers"],
  "Miami Marlins": ["Miami", "Marlins"],
  "Milwaukee Brewers": ["Milwaukee", "Brewers"],
  "Minnesota Twins": ["Minnesota", "Twins"],
  "New York Mets": ["New York", "Mets"],
  "New York Yankees": ["New York", "Yankees"],
  "Oakland Athletics": ["Oakland", "Athletics"],
  Athletics: ["Oakland", "Athletics"],
  "Philadelphia Phillies": ["Philadelphia", "Phillies"],
  "Pittsburgh Pirates": ["Pittsburgh", "Pirates"],
  "San Diego Padres": ["San Diego", "Padres"],
  "San Francisco Giants": ["San Francisco", "Giants"],
  "Seattle Mariners": ["Seattle", "Mariners"],
  "St. Louis Cardinals": ["St. Louis", "Cardinals"],
  "Tampa Bay Rays": ["Tampa Bay", "Rays"],
  "Texas Rangers": ["Texas", "Rangers"],
  "Toronto Blue Jays": ["Toronto", "Blue Jays"],
  "Washington Nationals": ["Washington", "Nationals"],
};

function renderTeamName(teamName) {
  const struct = TEAM_STRUCTURE[teamName];
  if (struct) {
    return `<div class="name-l1">${struct[0]}</div><div class="name-l2">${struct[1]}</div>`;
  }

  // Fallback: search for last space
  const lastSpace = teamName.lastIndexOf(" ");
  if (lastSpace === -1) return `<div class="name-l1">${teamName}</div>`;

  const l1 = teamName.substring(0, lastSpace);
  const l2 = teamName.substring(lastSpace + 1);
  return `<div class="name-l1">${l1}</div><div class="name-l2">${l2}</div>`;
}

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
  favoritesList.innerHTML = "";

  teams.forEach((team) => {
    const div = document.createElement("div");
    div.className = "fav-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `fav-${team.replace(/\s+/g, "-")}`;
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
    if (
      !favoritesMenu.contains(e.target) &&
      e.target !== favoritesBtn &&
      !favoritesBtn.contains(e.target)
    ) {
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
    const response = await fetch(`data/index.json?v=${new Date().getTime()}`);
    dates = await response.json();
    console.log(`[Init] Loaded index with ${dates.length} dates`);

    // Default to latest
    currentDate = dates[dates.length - 1];

    // URL override
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get("date");
    if (dateParam) {
      currentDate = dateParam;
    }

    populateDateSelectors();
    await updateUI();
    handleRouting();

    window.addEventListener("popstate", () => {
      const params = new URLSearchParams(window.location.search);

      // Handle Date Change
      const d = params.get("date");
      if (d && d !== currentDate) {
        currentDate = d;
        updateUI(false);
      }

      // Handle Routing (Details vs List)
      handleRouting();
    });

    function populateDateSelectors() {
      // Populate Years from available dates
      const years = new Set();
      dates.forEach((dateStr) => years.add(dateStr.split("-")[0]));
      const curY = currentDate
        ? currentDate.split("-")[0]
        : new Date().getFullYear().toString();
      years.add(curY);
      const sortedYears = Array.from(years).sort().reverse();

      yearSelect.innerHTML = "";
      sortedYears.forEach((year) => {
        const opt = document.createElement("option");
        opt.value = year;
        opt.textContent = year;
        yearSelect.appendChild(opt);
      });

      // Populate Months (Feb-Nov)
      const months = [
        { val: "01", name: "Jan" },
        { val: "02", name: "Feb" },
        { val: "03", name: "Mar" },
        { val: "04", name: "Apr" },
        { val: "05", name: "May" },
        { val: "06", name: "Jun" },
        { val: "07", name: "Jul" },
        { val: "08", name: "Aug" },
        { val: "09", name: "Sep" },
        { val: "10", name: "Oct" },
        { val: "11", name: "Nov" },
        { val: "12", name: "Dec" },
      ];

      monthSelect.innerHTML = "";
      months.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.val;
        opt.textContent = m.name;
        monthSelect.appendChild(opt);
      });

      // Populate Days (1-31)
      daySelect.innerHTML = "";
      for (let i = 1; i <= 31; i++) {
        const val = i.toString().padStart(2, "0");
        const opt = document.createElement("option");
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
      url.searchParams.set("date", newDate);

      window.history.pushState({}, "", url);
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
        url.searchParams.set("date", target);
        window.history.pushState({}, "", url);
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
        url.searchParams.set("date", target);
        window.history.pushState({}, "", url);
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
    const [y, m, d] = date.split("-");
    if (yearSelect && yearSelect.value !== y) yearSelect.value = y;
    if (monthSelect && monthSelect.value !== m) monthSelect.value = m;
    if (daySelect && daySelect.value !== d) daySelect.value = d;
  }

  if (shouldPushState) {
    const url = new URL(window.location);
    if (url.searchParams.get("date") !== date) {
      url.searchParams.set("date", date);
      window.history.pushState({}, "", url);
    }
  }

  // Clear current list and show loader
  gameList.innerHTML = "";
  // Re-add loader manually if needed or just wait for renderGames to clear it
  gameList.innerHTML = `
        <div class="loader">
        </div>`;

  try {
    const year = date.split("-")[0];
    const summaryPath = `data/${year}/${date}-summary.ftr`;
    console.log(`[UI] Fetching daily summary: ${summaryPath}`);
    const gamesData = await loadFeather(summaryPath);

    if (!gamesData || gamesData.length === 0) {
      gameList.innerHTML = "<p>No games recorded for this date.</p>";
      return;
    }

    // Cache for use in showDetailsView
    gamesByDate[date] = gamesData;

    // Sort: Favorites First
    gamesData.sort((a, b) => {
      const aFav =
        favoritesManager.isFavorite(a.homeTeam) ||
        favoritesManager.isFavorite(a.awayTeam);
      const bFav =
        favoritesManager.isFavorite(b.homeTeam) ||
        favoritesManager.isFavorite(b.awayTeam);
      if (aFav && !bFav) return -1;
      if (!aFav && bFav) return 1;
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
    const response = await fetch(filePath + "?t=" + Date.now());
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
    const isFav =
      favoritesManager.isFavorite(game.homeTeam) ||
      favoritesManager.isFavorite(game.awayTeam);
    if (isFav) {
      clone.querySelector(".game-card").classList.add("favorite-game");
    }

    // Meta Data
    const seriesDesc = game.seriesDescription || "Regular Season";
    clone.querySelector(".series-description").textContent = seriesDesc;

    clone.querySelector(".game-info-text").textContent =
      game.gameDescription || "";
    clone.querySelector(".game-venue").textContent = game.venue || "";

    // Home Team Data
    const homeLogoEl = clone.querySelector(".home-logo");
    homeLogoEl.className = `team-sprite home-logo ${getTeamSpriteClass(game.homeTeam)}`;
    clone.querySelector(".home-name").innerHTML = renderTeamName(game.homeTeam);
    clone.querySelector(".home-score").textContent = game.homeFinalScore;

    // Away Team Data
    const awayLogoEl = clone.querySelector(".away-logo");
    awayLogoEl.className = `team-sprite away-logo ${getTeamSpriteClass(game.awayTeam)}`;
    clone.querySelector(".away-name").innerHTML = renderTeamName(game.awayTeam);
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
  if (score < 2.5) return "gauge-tier-1";
  if (score < 5.0) return "gauge-tier-2";
  if (score < 7.5) return "gauge-tier-3";
  return "gauge-tier-4";
}

function getTeamSpriteClass(teamName) {
  if (!teamName) return "sprite-baseball";

  // Valid team list from FavoritesManager or similar
  const validTeams = favoritesManager.getAllTeams();
  // Also include some known aliases/historical names if needed
  if (
    !validTeams.includes(teamName) &&
    teamName !== "Athletics" &&
    teamName !== "Cleveland Indians"
  ) {
    return "sprite-baseball";
  }

  // Normalize class name: replace spaces with hyphens
  const className = teamName.replace(/ /g, "-");
  return `sprite-${className}`;
}

// --- Routing & View Logic ---
const detailsView = document.getElementById("game-details-view");
const backBtn = document.getElementById("back-btn");
const pbpBody = document.getElementById("play-by-play-body");
const mainContentArea = document.querySelector(".main-content-area");

const mainHeader = document.querySelector("header");
const gameListSection = document.getElementById("game-list");

function handleRouting() {
  const params = new URLSearchParams(window.location.search);
  const gamePk = params.get("gamePk");

  if (gamePk) {
    showDetailsView(gamePk);
  } else {
    showListView();
  }
}

function showListView() {
  detailsView.classList.add("hidden");
  mainContentArea.classList.remove("hidden");
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;
}

async function showDetailsView(gamePk) {
  mainContentArea.classList.add("hidden");
  detailsView.classList.remove("hidden");
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;

  let filePath = null;

  // 1. Try cached summary rows for currentDate
  const cached = gamesByDate[currentDate];
  if (cached) {
    const game = cached.find((g) => String(g.gamePk) === String(gamePk));
    if (game) filePath = game.filePath;
  }

  // 2. Load the summary FTR for currentDate on-demand (page reload case)
  if (!filePath) {
    const year = currentDate.split("-")[0];
    const summaryPath = `data/${year}/${currentDate}-summary.ftr`;
    try {
      const rows = await loadFeather(summaryPath);
      if (rows) {
        gamesByDate[currentDate] = rows;
        const game = rows.find((g) => String(g.gamePk) === String(gamePk));
        if (game) filePath = game.filePath;
      }
    } catch (e) {
      /* fall through to fallback */
    }
  }

  // 3. Fallback: derive path from convention
  if (!filePath) {
    const year = currentDate.split("-")[0];
    filePath = `data/${year}/${currentDate}-${gamePk}.ftr`;
  }

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
  pbpBody.innerHTML =
    '<tr><td colspan="3" class="loader"><div class="spinner"></div></td></tr>';

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

    const homeScore =
      metaRow.homeScore !== undefined ? metaRow.homeScore : "--";
    const awayScore =
      metaRow.awayScore !== undefined ? metaRow.awayScore : "--";

    // Update DOM
    document.getElementById("details-home-team").innerHTML =
      renderTeamName(homeTeam);
    document.getElementById("details-away-team").innerHTML =
      renderTeamName(awayTeam);

    // Logos
    const hLogo = document.getElementById("details-home-logo");
    const aLogo = document.getElementById("details-away-logo");
    if (hLogo)
      hLogo.className = `team-sprite details-logo ${getTeamSpriteClass(homeTeam)}`;
    if (aLogo)
      aLogo.className = `team-sprite details-logo ${getTeamSpriteClass(awayTeam)}`;

    // Scores
    const hScoreEl = document.getElementById("details-home-score");
    const aScoreEl = document.getElementById("details-away-score");
    if (hScoreEl) hScoreEl.textContent = homeScore;
    if (aScoreEl) aScoreEl.textContent = awayScore;

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
    pbpBody.innerHTML =
      "<tr><td colspan='3'>No play-by-play data available.</td></tr>";
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

  rows.forEach((row) => {
    if (!row) return;

    // original text for display
    const description = row.result || row.event || "";

    // AGGRESSIVE FILTER: Check ALL string values in the row
    const rowValues = Object.values(row)
      .filter((v) => typeof v === "string")
      .map((v) => v.toLowerCase());

    const shouldExclude = filters.some((f) =>
      rowValues.some((val) => val.includes(f)),
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
    const scoreChanged =
      (home !== prevHome || away !== prevAway) && firstRowRendered;
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
window.openGameDetails = function (game) {
  const pk = game.gamePk;
  if (pk) {
    // Reset search params to only include gamePk
    const url = new URL(
      window.location.protocol +
        "//" +
        window.location.host +
        window.location.pathname,
    );
    url.searchParams.set("gamePk", pk);

    window.history.pushState({}, "", url);
    handleRouting();
  }
};

init();
