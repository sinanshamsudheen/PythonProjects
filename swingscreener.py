# Reliable Stock Breakout Screener for NSE Stocks
# Using Yahoo Finance as primary data source with enhanced reliability

import requests
import pandas as pd
import time
import sqlite3
import random
import logging
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as tf
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import warnings
import http.client
http.client.HTTPConnection.debuglevel = 0

# Set up logging
logging.basicConfig(
    filename='stock_screener.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Suppress verbose warnings
warnings.filterwarnings("ignore")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)

# NSE symbol lists by index - hardcoded to avoid scraping issues
# These lists should be periodically updated
NIFTY50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "SBIN", "BHARTIARTL", 
    "KOTAKBANK", "ITC", "HDFC", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "BAJFINANCE", 
    "WIPRO", "HCLTECH", "ULTRACEMCO", "SUNPHARMA", "TATASTEEL", "TITAN", "BAJAJFINSV", 
    "TECHM", "NTPC", "POWERGRID", "TATAMOTORS", "JSWSTEEL", "ADANIPORTS", "HINDALCO", 
    "DRREDDY", "DIVISLAB", "INDUSINDBK", "NESTLEIND", "M&M", "HEROMOTOCO", "COALINDIA", 
    "GRASIM", "CIPLA", "ADANIENT", "UPL", "BRITANNIA", "TATACONSUM", "SHREECEM", "BPCL", 
    "ONGC", "EICHERMOT", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO"
]

# Additional mid and small cap symbols
ADDITIONAL_SYMBOLS = [
    "PIDILITIND", "HAVELLS", "APOLLOHOSP", "BERGEPAINT", "MPHASIS", "NAUKRI", "DABUR", "LUPIN",
    "TORNTPHARM", "GODREJCP", "JUBLFOOD", "PEL", "ICICIGI", "MINDTREE", "BIOCON", "COLPAL",
    "MOTHERSUMI", "BANDHANBNK", "AMBUJACEM", "CADILAHC", "BOSCHLTD", "BANKBARODA", "AUROPHARMA", 
    "PAGEIND", "SIEMENS", "GAIL", "MCDOWELL-N", "ABBOTINDIA", "DLF", "OFSS", "HDFCAMC",
    "PGHH", "ALKEM", "MRF", "GLAXO", "HONAUT", "HAL", "BEL", "IRCTC", "SAIL", "PNB",
    "HINDPETRO", "NMDC", "LALPATHLAB", "AFFLE", "POLYCAB", "DIXON", "COFORGE", "DEEPAKNTR"
]

class StockScreener:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.output_dir = "/home/zero/trading/swing_output"
        os.makedirs(self.output_dir, exist_ok=True)
        self.init_database()
        
    def get_random_headers(self):
        """Generate random headers to avoid detection"""
        return {
            "User-Agent": self.ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            conn = sqlite3.connect("stock_data.db")
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS breakout_results (
                Symbol TEXT,
                IndexName TEXT,
                Date TEXT,
                Open REAL,
                High REAL,
                Low REAL,
                Close REAL,
                Volume REAL,
                Avg_Volume REAL,
                Volume_Ratio REAL,
                Candle TEXT,
                Signal TEXT,
                Reason TEXT,
                Resistance REAL,
                Support REAL,
                Risk_Reward REAL,
                Volume_Strength TEXT,
                Timestamp TEXT,
                PRIMARY KEY (Symbol, Date)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbol_metadata (
                Symbol TEXT PRIMARY KEY,
                Name TEXT,
                Sector TEXT, 
                Industry TEXT,
                MarketCap REAL,
                LastUpdated TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def get_stock_metadata(self, symbol):
        """Get stock metadata from Yahoo Finance"""
        try:
            ticker = tf.Ticker(f"{symbol}.NS")
            info = ticker.info
            
            return {
                "Symbol": symbol,
                "Name": info.get("longName", ""),
                "Sector": info.get("sector", ""),
                "Industry": info.get("industry", ""),
                "MarketCap": info.get("marketCap", 0),
                "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logging.error(f"Error getting metadata for {symbol}: {e}")
            return {
                "Symbol": symbol,
                "Name": "",
                "Sector": "",
                "Industry": "",
                "MarketCap": 0,
                "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_historical_data(self, symbol, days=30):
        """Get historical data using yfinance library"""
        try:
            logging.info(f"Fetching data for {symbol}")
            ticker = tf.Ticker(f"{symbol}.NS")
            
            # Get data for slightly more days to account for market holidays
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days*1.5)
            
            # Get historical data
            hist = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
            
            if hist.empty:
                logging.warning(f"No historical data found for {symbol}")
                return []
            
            # Format the data
            data = []
            for index, row in hist.iterrows():
                data.append({
                    "date": index.strftime("%Y-%m-%d"),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"]
                })
            
            # Sort by date descending and limit to requested days
            data.sort(key=lambda x: x["date"], reverse=True)
            return data[:days]
            
        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def calculate_breakout(self, latest, previous):
        """Calculate breakout patterns with additional metrics"""
        if not latest or not previous or len(previous) < 5:
            return None
            
        today_open = latest['open']
        today_high = latest['high']
        today_low = latest['low']
        today_close = latest['close']
        
        # Check if data is valid
        if today_open <= 0 or today_high <= 0 or today_low <= 0 or today_close <= 0:
            logging.warning(f"Invalid price data: Open={today_open}, High={today_high}, Low={today_low}, Close={today_close}")
            return None
        
        candle_color = "Green" if today_close > today_open else "Red" if today_close < today_open else "Doji"
        candle_body_size = abs(today_close - today_open)
        candle_size = today_high - today_low
        body_percentage = (candle_body_size / candle_size * 100) if candle_size > 0 else 0
        
        upper_wick = today_high - max(today_open, today_close)
        lower_wick = min(today_open, today_close) - today_low
        
        # Calculate resistance levels using last 10 days
        prev_highs = [day['high'] for day in previous[:10] if day['high'] > 0]
        sorted_highs = sorted(prev_highs)
        resistance_level = sorted_highs[-2] if len(sorted_highs) >= 2 else sorted_highs[-1] if len(sorted_highs) >= 1 else 0
        
        # Calculate support levels using last 10 days
        prev_lows = [day['low'] for day in previous[:10] if day['low'] > 0]
        sorted_lows = sorted(prev_lows)
        support_level = sorted_lows[1] if len(sorted_lows) >= 2 else sorted_lows[0] if len(sorted_lows) >= 1 else 0
        
        # Calculate volume metrics
        recent_volumes = [day['volume'] for day in previous[:10] if day['volume'] > 0]
        avg_volume = sum(recent_volumes) / max(1, len(recent_volumes))
        volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 0
        
        # Previous day data
        prev_day = previous[0] if previous else None
        prev_close = prev_day['close'] if prev_day else 0
        
        # Gap analysis
        gap_up = today_open > prev_close if prev_close > 0 else False
        gap_percentage = ((today_open - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        # Price action patterns
        bullish_engulfing = (today_open < prev_day['close'] and today_close > prev_day['open']) if prev_day else False
        
        # ATR calculation (10-day)
        tr_values = []
        for i in range(min(10, len(previous))):
            if i == 0:
                tr = max(today_high - today_low, abs(today_high - previous[i]['close']), abs(today_low - previous[i]['close']))
            else:
                tr = max(
                    previous[i-1]['high'] - previous[i-1]['low'], 
                    abs(previous[i-1]['high'] - previous[i]['close']), 
                    abs(previous[i-1]['low'] - previous[i]['close'])
                )
            tr_values.append(tr)
        
        atr = sum(tr_values) / len(tr_values) if tr_values else 0
        
        # Determine breakout signal with detailed reasoning
        signal = "No Entry"
        reason = ""
        
        if today_close < today_open:
            signal = "No Entry"
            reason = "Bearish candle"
        elif body_percentage < 30:
            signal = "No Entry"
            reason = "Small bodied candle"
        elif volume_ratio < 1.0:
            signal = "Weak Signal"
            reason = "Below average volume"
        elif today_close <= resistance_level:
            signal = "No Breakout"
            reason = "Did not break resistance"
        elif upper_wick > candle_body_size:
            signal = "Failed Breakout"
            reason = "Long upper wick shows selling pressure"
        elif bullish_engulfing and volume_ratio > 1.5:
            signal = "Strong Breakout"
            reason = "Bullish engulfing with high volume"
        elif gap_up and gap_percentage > 1.0 and volume_ratio > 1.5:
            signal = "Gap Up Breakout"
            reason = f"Gap up of {gap_percentage:.2f}% with strong volume"
        elif today_close > resistance_level and volume_ratio > 1.5:
            signal = "Resistance Breakout"
            reason = "Closed above resistance with good volume"
        else:
            signal = "Potential Breakout"
            reason = "Price action needs confirmation"
        
        # Volume classification
        volume_strength = "Very High" if volume_ratio > 3 else "High" if volume_ratio > 2 else "Above Average" if volume_ratio > 1.5 else "Average" if volume_ratio > 0.8 else "Low"
        
        # Calculate risk-reward ratio
        stop_loss = support_level if support_level > 0 else today_low - atr
        risk = today_close - stop_loss
        reward_target = today_close + (2 * risk)  # 1:2 risk-reward
        risk_reward = round(2.0, 2)  # Fixed at 1:2
        
        return {
            "Date": latest['date'],
            "Open": round(today_open, 2),
            "High": round(today_high, 2),
            "Low": round(today_low, 2),
            "Close": round(today_close, 2),
            "Volume": int(latest['volume']),
            "Avg_Volume": int(avg_volume),
            "Volume_Ratio": round(volume_ratio, 2),
            "Candle": candle_color,
            "Body_Percentage": round(body_percentage, 2),
            "Signal": signal,
            "Reason": reason,
            "Resistance": round(resistance_level, 2),
            "Support": round(support_level, 2),
            "Stop_Loss": round(stop_loss, 2),
            "Target": round(reward_target, 2),
            "Risk_Reward": risk_reward,
            "Volume_Strength": volume_strength,
            "ATR": round(atr, 2),
            "Previous_Close": round(prev_close, 2),
            "Gap_Percentage": round(gap_percentage, 2)
        }

    def process_symbol(self, symbol, index_name):
        """Process a single symbol with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 2.0))
                
                # Get the data
                data = self.get_historical_data(symbol)
                
                if not data or len(data) < 10:
                    logging.warning(f"Insufficient data for {symbol}: got {len(data) if data else 0} days")
                    return None
                
                # Calculate breakout signals
                result = self.calculate_breakout(data[0], data[1:])
                
                if not result:
                    return None
                    
                result["Symbol"] = symbol
                result["IndexName"] = index_name
                result["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Get and save metadata if we have a result
                try:
                    metadata = self.get_stock_metadata(symbol)
                    self.save_metadata(metadata)
                except Exception as e:
                    logging.error(f"Error saving metadata for {symbol}: {e}")
                
                return result
                
            except Exception as e:
                logging.error(f"Error processing {symbol} (Attempt {attempt+1}): {str(e)}")
                time.sleep(random.uniform(2, 5))
                
        return None
        
    def save_metadata(self, metadata):
        """Save stock metadata to database"""
        if not metadata:
            return
            
        try:
            conn = sqlite3.connect("stock_data.db")
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO symbol_metadata 
            (Symbol, Name, Sector, Industry, MarketCap, LastUpdated)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metadata["Symbol"],
                metadata["Name"],
                metadata["Sector"],
                metadata["Industry"],
                metadata["MarketCap"],
                metadata["LastUpdated"]
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error saving metadata for {metadata['Symbol']}: {e}")

    def save_to_db(self, results):
        """Save results to SQLite database with improved error handling"""
        if not results:
            logging.warning("No results to save to database")
            return
            
        conn = None
        try:
            conn = sqlite3.connect("stock_data.db")
            cursor = conn.cursor()
            
            for result in results:
                try:
                    cursor.execute('''
                    INSERT OR REPLACE INTO breakout_results 
                    (Symbol, IndexName, Date, Open, High, Low, Close, Volume, 
                    Avg_Volume, Volume_Ratio, Candle, Signal, Reason, 
                    Resistance, Support, Risk_Reward, Volume_Strength, Timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result["Symbol"],
                        result["IndexName"],
                        result["Date"],
                        result["Open"],
                        result["High"],
                        result["Low"],
                        result["Close"],
                        result["Volume"],
                        result["Avg_Volume"],
                        result["Volume_Ratio"],
                        result["Candle"],
                        result["Signal"],
                        result["Reason"],
                        result["Resistance"],
                        result["Support"],
                        result["Risk_Reward"],
                        result["Volume_Strength"],
                        result["Timestamp"]
                    ))
                except Exception as e:
                    logging.error(f"Error inserting {result['Symbol']}: {e}")
                    continue
                    
            conn.commit()
            logging.info(f"Saved {len(results)} records to database")
        except Exception as e:
            logging.error(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def run(self, symbols_dict=None):
        """Run the screener with the specified symbols or default lists"""
        start_time = datetime.now()
        logging.info(f"Starting stock screener at {start_time}")
        
        if symbols_dict is None:
            symbols_dict = {
                "NIFTY50": NIFTY50_SYMBOLS,
                "MIDCAP_SMALLCAP": ADDITIONAL_SYMBOLS
            }
        
        all_results = []
        
        for index_name, symbols in symbols_dict.items():
            logging.info(f"\nProcessing {len(symbols)} symbols from {index_name}...")
            index_results = []
            
            # Process symbols in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.process_symbol, symbol, index_name): symbol for symbol in symbols}
                
                for future in futures:
                    symbol = futures[future]
                    try:
                        result = future.result()
                        if result:
                            index_results.append(result)
                    except Exception as e:
                        logging.error(f"Error in future for {symbol}: {str(e)}")
            
            # Filter interesting signals
            breakouts = [r for r in index_results if r["Signal"] in ["Strong Breakout", "Gap Up Breakout", "Resistance Breakout"]]
            potentials = [r for r in index_results if r["Signal"] == "Potential Breakout"]
            
            logging.info(f"Found {len(breakouts)} strong breakouts and {len(potentials)} potential breakouts in {index_name}")
            
            # Save index-specific results
            if index_results:
                df = pd.DataFrame(index_results)
                
                # Save all signals for this index
                all_filename = f"{self.output_dir}/{index_name}_all_{datetime.now().strftime('%Y%m%d')}.xlsx"
                df.to_excel(all_filename, index=False)
                
                # Save breakouts only
                if breakouts:
                    df_breakouts = pd.DataFrame(breakouts)
                    breakouts_filename = f"{self.output_dir}/{index_name}_breakouts_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    df_breakouts.to_excel(breakouts_filename, index=False)
                
                all_results.extend(index_results)
        
        # Save all results
        if all_results:
            df_all = pd.DataFrame(all_results)
            
            # Filter for different signal types
            strong_signals = df_all[df_all["Signal"].isin(["Strong Breakout", "Gap Up Breakout", "Resistance Breakout"])]
            strong_signals = strong_signals.sort_values("Volume_Ratio", ascending=False)
            
            potential_signals = df_all[df_all["Signal"] == "Potential Breakout"]
            potential_signals = potential_signals.sort_values("Volume_Ratio", ascending=False)
            
            # Save consolidated results
            main_filename = f"{self.output_dir}/All_Results_{datetime.now().strftime('%Y%m%d')}.xlsx"
            strong_filename = f"{self.output_dir}/Strong_Breakouts_{datetime.now().strftime('%Y%m%d')}.xlsx"
            potential_filename = f"{self.output_dir}/Potential_Breakouts_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            df_all.to_excel(main_filename, index=False)
            
            if not strong_signals.empty:
                strong_signals.to_excel(strong_filename, index=False)
            
            if not potential_signals.empty:
                potential_signals.to_excel(potential_filename, index=False)
            
            # Save to database
            self.save_to_db(all_results)
            
            # Create HTML report with charts
            self.create_html_report(strong_signals, "strong_breakouts")
            self.create_html_report(potential_signals, "potential_breakouts")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60.0
            
            logging.info(f"\nScreener completed in {duration:.2f} minutes.")
            logging.info(f"Found {len(all_results)} total signals.")
            logging.info(f"Found {len(strong_signals)} strong breakouts.")
            logging.info(f"Found {len(potential_signals)} potential breakouts.")
            
            return df_all
        else:
            logging.warning("\nNo results found.")
            return None
    
    def create_html_report(self, df, report_type):
        """Create an HTML report for the results"""
        if df is None or df.empty:
            return
            
        try:
            # Create an HTML file with the results
            html_file = f"{self.output_dir}/{report_type}_{datetime.now().strftime('%Y%m%d')}.html"
            
            # HTML template with basic styling
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Stock Breakout Report - {datetime.now().strftime('%Y-%m-%d')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333366; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .green {{ color: green; }}
                    .red {{ color: red; }}
                    .strong {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>Stock Breakout Scanner - {report_type.replace('_', ' ').title()}</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Signal</th>
                        <th>Reason</th>
                        <th>Close</th>
                        <th>Volume Ratio</th>
                        <th>Stop Loss</th>
                        <th>Target</th>
                    </tr>
            """
            
            # Add each row to the table
            for _, row in df.iterrows():
                signal_class = "strong" if "Strong" in row["Signal"] else ""
                close_class = "green" if row["Close"] > row["Open"] else "red"
                
                html_content += f"""
                    <tr>
                        <td class="{signal_class}">{row["Symbol"]}</td>
                        <td class="{signal_class}">{row["Signal"]}</td>
                        <td>{row["Reason"]}</td>
                        <td class="{close_class}">{row["Close"]}</td>
                        <td>{row["Volume_Ratio"]}</td>
                        <td>{row.get("Stop_Loss", row["Support"])}</td>
                        <td>{row.get("Target", "-")}</td>
                    </tr>
                """
            
            html_content += """
                </table>
            </body>
            </html>
            """
            
            # Write the HTML content to a file
            with open(html_file, "w") as f:
                f.write(html_content)
                
            logging.info(f"HTML report created: {html_file}")
        except Exception as e:
            logging.error(f"Error creating HTML report: {e}")


def main():
    try:
        logging.info("Starting Stock Breakout Screener")
        
        # Create and run the screener
        screener = StockScreener()
        results = screener.run()
        
        if results is not None:
            print(f"Found {len(results)} signals.")
            print(f"Results saved to the 'output' directory.")
        else:
            print("No results found.")
            
    except Exception as e:
        logging.error(f"Error in main: {e}")
        print(f"An error occurred: {e}")
        print("Check the log file for details.")

if __name__ == "__main__":
    main()