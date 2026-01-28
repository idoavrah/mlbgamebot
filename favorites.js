export class FavoritesManager {
  constructor() {
    this.storageKey = "mlb_favorites";
    this.favorites = this.loadFavorites();

    // MLB Teams List for UI population
    this.teams = [
      "Arizona Diamondbacks",
      "Atlanta Braves",
      "Baltimore Orioles",
      "Boston Red Sox",
      "Chicago Cubs",
      "Chicago White Sox",
      "Cincinnati Reds",
      "Cleveland Guardians",
      "Colorado Rockies",
      "Detroit Tigers",
      "Houston Astros",
      "Kansas City Royals",
      "Los Angeles Angels",
      "Los Angeles Dodgers",
      "Miami Marlins",
      "Milwaukee Brewers",
      "Minnesota Twins",
      "New York Mets",
      "New York Yankees",
      "Oakland Athletics",
      "Philadelphia Phillies",
      "Pittsburgh Pirates",
      "San Diego Padres",
      "San Francisco Giants",
      "Seattle Mariners",
      "St. Louis Cardinals",
      "Tampa Bay Rays",
      "Texas Rangers",
      "Toronto Blue Jays",
      "Washington Nationals",
    ].sort();
  }

  loadFavorites() {
    const stored = localStorage.getItem(this.storageKey);
    return stored ? JSON.parse(stored) : [];
  }

  saveFavorites() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
  }

  getFavorites() {
    return this.favorites;
  }

  getAllTeams() {
    return this.teams;
  }

  isFavorite(teamName) {
    return this.favorites.includes(teamName);
  }

  toggleFavorite(teamName) {
    if (this.isFavorite(teamName)) {
      this.favorites = this.favorites.filter((t) => t !== teamName);
    } else {
      this.favorites.push(teamName);
    }
    this.saveFavorites();
  }
}
