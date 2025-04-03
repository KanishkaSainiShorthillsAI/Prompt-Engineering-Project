import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class NiftyScraper:
    """Scrapes Nifty 50 data from NSE website and downloads a CSV file."""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.nse_url = "https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY 50"
        self.driver = self._get_driver()

    def _get_driver(self):
        """Initializes and returns the Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {"download.default_directory": self.script_dir})
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def download_csv(self):
        """Downloads the latest Nifty 50 CSV file and returns its path."""
        print("Scraping started...")
        self.driver.get(self.nse_url)
        time.sleep(5)  
        
        try:
            csv_button = self.driver.find_element(By.ID, "dnldEquityStock")
            csv_button.click()
            print("CSV file downloading...")
        except Exception as e:
            print("Error: CSV download button not found.", e)
            self.driver.quit()
            return None
        
        time.sleep(10)  
        self.driver.quit()
        csv_files = [f for f in os.listdir(self.script_dir) if f.endswith(".csv")]
        if not csv_files:
            print("Error: No CSV file found in script directory.")
            return None

        latest_csv = max([os.path.join(self.script_dir, f) for f in csv_files], key=os.path.getctime)
        print(f"CSV file downloaded at path: {latest_csv}")
        return latest_csv


class NiftyAnalyzer:
    """Processes the Nifty 50 CSV data and provides analysis."""

    COLUMN_MAP = {
        "SYMBOL": "symbol",
        "%CHNG": "pChange",
        "LTP": "lastPrice",
        "52W H": "high_52_week",
        "52W L": "low_52_week",
        "30 D   %CHNG": "change_30d"
    }

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = self._load_data()

    def _load_data(self):
        """Loads and cleans CSV data."""
        try:
            df = pd.read_csv(self.csv_file)
            df.columns = [col.strip() for col in df.columns]

            df.rename(columns=self.COLUMN_MAP, inplace=True)
            missing_columns = [col for col in self.COLUMN_MAP.values() if col not in df.columns]
            if missing_columns:
                print(f"Error: Missing columns in CSV: {missing_columns}")
                return None

            
            for col in ["pChange", "lastPrice", "high_52_week", "low_52_week", "change_30d"]:
                df[col] = pd.to_numeric(df[col].astype(str).replace("-", "NaN"), errors="coerce")

            df.dropna(inplace=True)  
            return df

        except Exception as e:
            print("Error loading CSV file:", e)
            return None

    def analyze(self):
        """Extracts top gainers, losers, and key stock movements."""
        if self.df is None:
            return None, None, None, None, None

        return (
            self.df.nlargest(5, "pChange"),
            self.df.nsmallest(5, "pChange"),
            self.df[self.df["lastPrice"] <= 0.7 * self.df["high_52_week"]].nlargest(5, "lastPrice"),
            self.df[self.df["lastPrice"] >= 1.2 * self.df["low_52_week"]].nsmallest(5, "lastPrice"),
            self.df.nlargest(5, "change_30d"),
        )

    def plot_gainers_losers(self, gainers, losers):
        """Plots top 5 gainers and losers."""
        plt.figure(figsize=(10, 5))
        stocks = list(gainers["symbol"]) + list(losers["symbol"])
        percentage_change = list(gainers["pChange"]) + list(losers["pChange"])
        colors = ["blue"] * 5 + ["red"] * 5

        plt.bar(stocks, percentage_change, color=colors)
        plt.xlabel("Stock Symbol")
        plt.ylabel("Percentage Change")
        plt.title("Top 5 Gainers and Losers of the Day")
        plt.xticks(rotation=45)
        plt.show()


if __name__ == "__main__":
    scraper = NiftyScraper()
    csv_file = scraper.download_csv()

    if csv_file:
        analyzer = NiftyAnalyzer(csv_file)
        gainers, losers, below_52_high, above_52_low, top_30d_returns = analyzer.analyze()

        if gainers is not None:
            print("\nTop 5 Gainers")
            print(gainers[["symbol", "pChange"]].to_string(index=False))

            print("\nTop 5 Losers")
            print(losers[["symbol", "pChange"]].to_string(index=False))

            print("\nStocks 30% Below 52-Week High")
            print(below_52_high[["symbol", "lastPrice"]].to_string(index=False))

            print("\nStocks 20% Above 52-Week Low")
            print(above_52_low[["symbol", "lastPrice"]].to_string(index=False))

            print("\nTop 5 Stocks with Highest Returns in Last 30 Days")
            print(top_30d_returns[["symbol", "change_30d"]].to_string(index=False))

            analyzer.plot_gainers_losers(gainers, losers)
        else:
            print("Error: Data extraction failed.")
    else:
        print("Error: Failed to fetch NSE data.")

