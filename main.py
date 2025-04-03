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
    """Scrapes and downloads the Nifty 50 stock data from NSE."""
    def __init__(self):
        self.script_dir = os.getcwd()
        self.nse_url = "https://www.nseindia.com/market-data/live-equity-market"
        self.driver = self._initialize_driver()
    
    def _initialize_driver(self):
        """Initializes and returns a Selenium WebDriver."""
        options = Options()
        options.add_experimental_option("prefs", {"download.default_directory": self.script_dir})
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def download_csv(self):
        """Downloads the latest Nifty 50 CSV file and returns its path."""
        self.driver.get(self.nse_url)
        time.sleep(5)
        
        try:
            csv_button = self.driver.find_element(By.ID, "dnldEquityStock")
            csv_button.click()
            print("CSV Download Started...")
        except Exception as e:
            print("Error: CSV Download Button Not Found.", e)
            self.driver.quit()
            return None
        
        time.sleep(10)
        self.driver.quit()
        
        csv_files = [f for f in os.listdir(self.script_dir) if f.endswith(".csv")]
        if not csv_files:
            print("Error: No CSV file found.")
            return None
        
        latest_csv = max([os.path.join(self.script_dir, f) for f in csv_files], key=os.path.getctime)
        print(f"Latest CSV Found: {latest_csv}")
        return latest_csv


class NiftyAnalyzer:
    """Analyzes the Nifty 50 stock data."""
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
        self.df = self._load_and_clean_data()
    
    def _load_and_clean_data(self):
        """Loads and cleans the CSV data."""
        try:
            df = pd.read_csv(self.csv_file)
            df.columns = [col.strip() for col in df.columns]
            df.rename(columns=self.COLUMN_MAP, inplace=True)
            
            for col in ["pChange", "lastPrice", "high_52_week", "low_52_week", "change_30d"]:
                df[col] = df[col].astype(str).str.replace(",", "").astype(float)
            
            return df.dropna()
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return None
    
    def get_top_gainers(self):
        return self.df.nlargest(5, "pChange")
    
    def get_top_losers(self):
        return self.df.nsmallest(5, "pChange")
    
    def get_stocks_30_below_52_week_high(self):
        return self.df[self.df["lastPrice"] <= 0.7 * self.df["high_52_week"]].nlargest(5, "lastPrice")
    
    def get_stocks_20_above_52_week_low(self):
        return self.df[self.df["lastPrice"] >= 1.2 * self.df["low_52_week"]].nsmallest(5, "lastPrice")
    
    def get_top_30_day_returns(self):
        return self.df.nlargest(5, "change_30d")


class NiftyVisualizer:
    """Visualizes Nifty 50 stock data."""
    @staticmethod
    def plot_gainers_losers(gainers, losers):
        plt.figure(figsize=(10,5))
        stocks = list(gainers["symbol"]) + list(losers["symbol"])
        percentage_change = list(gainers["pChange"]) + list(losers["pChange"])
        colors = ["blue"]*5 + ["red"]*5
        
        plt.bar(stocks, percentage_change, color=colors)
        plt.xlabel("Stock Symbol")
        plt.ylabel("Percentage Change")
        plt.title("Top 5 Gainers and Losers")
        plt.xticks(rotation=45)
        plt.show()


if __name__ == "__main__":
    scraper = NiftyScraper()
    csv_file = scraper.download_csv()
    
    if csv_file:
        analyzer = NiftyAnalyzer(csv_file)
        gainers = analyzer.get_top_gainers()
        losers = analyzer.get_top_losers()
        below_52_high = analyzer.get_stocks_30_below_52_week_high()
        above_52_low = analyzer.get_stocks_20_above_52_week_low()
        top_30d_returns = analyzer.get_top_30_day_returns()
        
        print("\nTop 5 Gainers")
        print(gainers[["symbol", "pChange"]])
        
        print("\nTop 5 Losers")
        print(losers[["symbol", "pChange"]])
        
        print("\nStocks 30% Below 52-Week High")
        print(below_52_high[["symbol", "lastPrice"]])
        
        print("\nStocks 20% Above 52-Week Low")
        print(above_52_low[["symbol", "lastPrice"]])
        
        print("\nTop 5 Stocks with Highest 30-Day Returns")
        print(top_30d_returns[["symbol", "change_30d"]])
        
        NiftyVisualizer.plot_gainers_losers(gainers, losers)
    else:
        print("Error: Failed to fetch NSE data.")
