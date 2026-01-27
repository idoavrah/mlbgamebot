.PHONY: help parse parse-year parse-month parse-day run-website install

# Default target
help:
	@echo "MLB Game Bot - Commands"
	@echo "======================="
	@echo "make parse                                   : Parse data for the defaults (Yesterday)"
	@echo "make parse-year YEAR=2025                    : Parse data for a specific year"
	@echo "make parse-month YEAR=2025 MONTH=10          : Parse data for a specific month"
	@echo "make parse-day YEAR=2025 MONTH=10 DAY=04     : Parse data for a specific day"
	@echo "make run-website                             : Run the website locally on port 8000"
	@echo "make install                                 : Install backend dependencies"

# Default parse (Yesterday)
parse:
	@echo "Parsing default (Yesterday)..."
	@cd backend && python3 gamebot.py

# Parse for a specific year
parse-year:
	@echo "Parsing for year $(YEAR)..."
	@cd backend && LOAD_YEAR=$(YEAR) python3 gamebot.py

# Parse for a specific month
parse-month:
	@echo "Parsing for $(YEAR)-$(MONTH)..."
	@cd backend && LOAD_YEAR=$(YEAR) LOAD_MONTH=$(MONTH) python3 gamebot.py

# Parse for a specific day
parse-day:
	@echo "Parsing for $(YEAR)-$(MONTH)-$(DAY)..."
	@cd backend && LOAD_YEAR=$(YEAR) LOAD_MONTH=$(MONTH) LOAD_DAY=$(DAY) python3 gamebot.py

# Run the website
run-website:
	@echo "Starting local server at http://localhost:8000"
	@python3 -m http.server 8000

# Install dependencies
install:
	@pip3 install -r requirements.txt
