# Financial Analysis Agents

A Python-based framework for financial analysis using **Benjamin Graham's principles** from *"Reading and Understanding Financial Statements"*. The project leverages AI (Google Gemini) to extract and structure financial data from raw text, then applies Graham's analytical methods to evaluate stocks.

## 📋 Features

- **Graham Analysis Agent**: Implements Graham's "Multiple Method" from Part 2 of his book, calculating key financial ratios and metrics
- **Data Builder Agent**: Uses Google Gemini API to intelligently extract and structure financial data from raw balance sheet text
- **Market Data Agent**: Fetches real financial data from Yahoo Finance and structures it using AI
- **Multiple Input Modes**:
  - Analyze pre-loaded JSON files from the `/data` folder
  - Manually input raw financial data and let AI extract values
  - Download ticker data from Yahoo Finance and analyze automatically
- **Type-Safe Data Schema**: Standardized `FinancialData` dataclass with automatic post-initialization validation

## 🎯 Project Structure

```
financial-analysis-agents/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── graham.py           # Benjamin Graham analysis engine
│   ├── builder.py          # AI-powered data extraction
│   └── market_data.py      # Yahoo Finance integration
│
├── models/                 # Data structures
│   ├── __init__.py
│   └── data_schema.py      # FinancialData dataclass with validation
│
├── data/                   # Sample input files
│   └── example_company.json
│
├── utils/                  # Helper functions
│   ├── __init__.py
│   └── loader.py           # JSON file loading utilities
│
├── .gitignore              # Git ignore rules
├── main.py                 # Main entry point
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Google API Key (for AI-powered data extraction)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/giuseppedavidde/MyGITprj.git
cd MyGITprj/financial-analysis-agents

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Google API Key

Create a `.env` file in the project root:

```bash
# .env
GOOGLE_API_KEY=your_google_api_key_here
```

**How to get a Google API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Generative AI API**
4. Create an API key in the credentials section
5. Copy and paste it into your `.env` file

### 3. Run the Application

```bash
python main.py
```

You'll see an interactive menu:

```
1. Analyze local JSON file (from /data folder)
2. Build data manually (paste raw financial text)
3. Download ticker data (Yahoo Finance + AI analysis)
```

## 📖 Usage Modes

### Mode 1: Analyze Local JSON Files

1. Place a JSON file in the `data/` folder (e.g., `apple.json`)
2. Run `python main.py` and select option **1**
3. Choose the file to analyze
4. View the Graham analysis report

**Example JSON file structure** (`data/example_company.json`):
```json
{
  "total_assets": 352755000000.0,
  "current_assets": 135405000000.0,
  "current_liabilities": 105718000000.0,
  "inventory": 2608000000.0,
  "intangible_assets": 0.0,
  "total_liabilities": 302096000000.0,
  "preferred_stock": 0.0,
  "common_stock": 73993000000.0,
  "surplus": -23334000000.0,
  "sales": 383285000000.0,
  "operating_income": 119505000000.0,
  "net_income": 96995000000.0,
  "interest_charges": 2645000000.0,
  "preferred_dividends": 0.0,
  "shares_outstanding": 15728000000.0,
  "current_market_price": 234.5
}
```

### Mode 2: Manual Data Entry with AI

1. Run `python main.py` and select option **2**
2. Paste raw financial statement text (from annual reports, financial websites, etc.)
3. The AI will extract and structure the data automatically
4. Optionally save the structured data as JSON for future analysis
5. Run Graham analysis immediately or later

### Mode 3: Yahoo Finance + AI Analysis

1. Run `python main.py` and select option **3**
2. Enter a stock ticker symbol (e.g., `AAPL`, `TSLA`, `GME`)
3. The app will:
   - Fetch financial data from Yahoo Finance
   - Structure it using Google Gemini AI
   - Run Graham's analysis automatically
   - Display the full report

## 📊 Graham Analysis Metrics

The `GrahamAgent` computes the following financial ratios based on Graham's methodology:

| Metric | Description | Graham's Reference |
|--------|-------------|-------------------|
| **Profit Margin** | Operating income / Sales | Part 2, Chapter 14 |
| **Interest Coverage** | Operating income / Interest charges | Minimum 2.5x–3x |
| **Current Ratio** | Current assets / Current liabilities | Minimum 2:1 for industrial |
| **Quick Ratio** | (Current assets - Inventory) / Current liabilities | Target 1:1 |
| **Book Value per Share** | (Equity - Intangible assets) / Shares | Ch. 21 |
| **Price-to-Book** | Market price / Book value | Indicator of safety margin |
| **Debt Ratio** | Total liabilities / Capitalization | Max 25–30% debt |
| **P/E Ratio** | Market price / EPS | Graham: < 15 for stable |
| **Earnings Yield** | EPS / Market price | Bond-equivalent comparison |

## 🛠️ Development

### Install Development Tools

The `requirements.txt` includes:
- **black**: Code formatting
- **flake8**: Linting and style checks
- **mypy**: Static type checking
- **pytest**: Unit testing framework

### Format and Lint Code

```bash
# Format with black
black .

# Check with flake8
flake8 .

# Type check with mypy
mypy agents models utils main.py
```

### Run Tests

```bash
pytest
```

## 🔐 Security & Best Practices

- **API Keys**: Store in `.env` file, never commit to git (see `.gitignore`)
- **Large Data Files**: CSV/XLS files and archives are ignored by default
- **Sensitive Data**: Remove personal financial data before committing
- **Error Handling**: All agent exceptions are caught with specific error types (not generic `Exception`)

## 📝 Configuration

### Environment Variables (`.env`)

```
GOOGLE_API_KEY=your_api_key_here
```

### Customizing Graham's Thresholds

Edit `agents/graham.py` to adjust Graham's minimum ratios:
- Interest coverage threshold (line ~40)
- Debt ratio limits (line ~70)
- P/E ratio cutoffs (line ~85)

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GOOGLE_API_KEY not found` | Ensure `.env` file exists in project root with your API key |
| `Module not found` | Run `pip install -r requirements.txt` and ensure virtual env is activated |
| `Yahoo Finance timeout` | Check internet connection; ticker symbol might be invalid |
| `JSON parsing error` | Validate JSON syntax in `/data` folder with [jsonlint.com](https://jsonlint.com) |

## 📚 References

- **Book**: Benjamin Graham, *"Reading and Understanding Financial Statements"*
- **API**: [Google Generative AI](https://ai.google.dev/)
- **Data**: [Yahoo Finance](https://finance.yahoo.com/)

## 📄 License

This project is part of the MyGITprj repository. Check the main repository for license details.

## 👤 Author

Davidde Giuseppe ([@giuseppedavidde](https://github.com/giuseppedavidde))

---

**Last Updated**: December 2, 2025
