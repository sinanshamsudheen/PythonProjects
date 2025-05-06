# Advanced Intraday Stock Screener for Next-Day Trading
# Identifies high-probability intraday trading candidates for the next trading day

import pandas as pd
import numpy as np
import yfinance as yf
import ta
import sqlite3
import logging
import os
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
import warnings
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Set up logging
logging.basicConfig(
    filename='intraday_screener.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
# NSE symbols for both large, mid and small caps
NSE_SYMBOLS = [
    # Large Cap
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "SBIN", "BHARTIARTL", 
    "KOTAKBANK", "ITC", "HDFC", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "BAJFINANCE", 
    "WIPRO", "HCLTECH", "TITAN", "SUNPHARMA", "TATASTEEL",
    # Mid Cap
    "INDIGO", "BIOCON", "APOLLOHOSP", "AUROPHARMA", "HDFCAMC", "MPHASIS", "PIIND", 
    "HAVELLS", "BERGEPAINT", "TORNTPHARM", "PEL", "TATAPOWER", "DABUR", "MUTHOOTFIN",
    "LUPIN", "BANDHANBNK", "GODREJCP", "AMBUJACEM", "CADILAHC", "BOSCHLTD", "SIEMENS",
    # Small Cap with volume
    "IRCTC", "CHAMBLFERT", "GRANULES", "CANBK", "NATIONALUM", "SAIL", "PNB", "RVNL",
    "CEATLTD", "HINDCOPPER", "GMRINFRA", "BANKBARODA", "FEDERALBNK", "ASHOKLEY",
    "ABFRL", "TATACHEM", "ADANIPOWER", "MANAPPURAM", "NMDC", "IDFC", "EXIDEIND", "JINDALSAW"
]

class IntradayScreener:
    def __init__(self):
        self.ua = UserAgent()
        self.output_dir = "/home/zero/trading/intraday_output"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/charts", exist_ok=True)
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with schema for intraday setups"""
        try:
            conn = sqlite3.connect("intraday_data.db")
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS intraday_setups (
                Symbol TEXT,
                Date TEXT,
                Setup_Type TEXT,
                Signal TEXT,
                Confidence TEXT,
                Entry REAL,
                Stop_Loss REAL,
                Target1 REAL,
                Target2 REAL,
                Risk_Reward REAL,
                Volume_Ratio REAL,
                Trend_Strength TEXT,
                Support REAL,
                Resistance REAL,
                ADX REAL,
                RSI REAL,
                MACD_Signal TEXT,
                Volatility REAL,
                Risk_Factor REAL,
                Expected_Movement REAL,
                Pattern TEXT,
                Notes TEXT,
                Timestamp TEXT,
                PRIMARY KEY (Symbol, Date, Setup_Type)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_sentiment (
                Date TEXT PRIMARY KEY,
                Overall_Sentiment TEXT,
                Index_Movement REAL,
                Advancing_Count INTEGER,
                Declining_Count INTEGER,
                New_High_Count INTEGER,
                New_Low_Count INTEGER,
                Volume_Change REAL,
                VIX REAL,
                Notes TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Intraday database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")

    def get_market_data(self):
        """Get market sentiment data for context"""
        try:
            # Get Nifty index data
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="10d")
            
            # Get India VIX data
            india_vix = yf.Ticker("^INDIAVIX")
            vix_data = india_vix.history(period="5d")
            
            # Get Bank Nifty data for sector strength
            bank_nifty = yf.Ticker("^NSEBANK")
            bank_nifty_data = bank_nifty.history(period="5d")
            
            latest_date = nifty_data.index[-1].strftime("%Y-%m-%d")
            # latest_date = "2025-04-24"
            
            # Calculate market metrics
            nifty_change = ((nifty_data['Close'].iloc[-1] / nifty_data['Close'].iloc[-2]) - 1) * 100
            vix_value = vix_data['Close'].iloc[-1]
            vix_change = ((vix_data['Close'].iloc[-1] / vix_data['Close'].iloc[-2]) - 1) * 100
            
            # Simple trend analysis
            short_ma = nifty_data['Close'].rolling(5).mean()[-1]
            long_ma = nifty_data['Close'].rolling(10).mean()[-1]
            trend = "Bullish" if short_ma > long_ma else "Bearish"
            
            # Volume analysis
            vol_change = ((nifty_data['Volume'].iloc[-1] / nifty_data['Volume'].iloc[-2]) - 1) * 100
            
            # Simulate advancing/declining stocks (would need proper NSE data)
            adv_count = 0
            dec_count = 0
            for symbol in NSE_SYMBOLS[:20]:  # Use subset for speed
                try:
                    stock = yf.Ticker(f"{symbol}.NS")
                    data = stock.history(period="2d")
                    if len(data) >= 2:
                        if data['Close'].iloc[-1] > data['Close'].iloc[-2]:
                            adv_count += 1
                        else:
                            dec_count += 1
                except:
                    continue
            
            # Store market sentiment
            sentiment = "Bullish" if adv_count > dec_count and nifty_change > 0 else "Bearish" if dec_count > adv_count and nifty_change < 0 else "Neutral"
            
            market_data = {
                "Date": latest_date,
                "Overall_Sentiment": sentiment,
                "Index_Movement": round(nifty_change, 2),
                "Advancing_Count": adv_count,
                "Declining_Count": dec_count,
                "New_High_Count": 0,  # Would need proper NSE data
                "New_Low_Count": 0,   # Would need proper NSE data
                "Volume_Change": round(vol_change, 2),
                "VIX": round(vix_value, 2),
                "Notes": f"VIX change: {round(vix_change, 2)}%, Market trend: {trend}"
            }
            
            # Save to database
            self.save_market_sentiment(market_data)
            
            return market_data
        except Exception as e:
            logging.error(f"Error getting market data: {e}")
            return None

    def save_market_sentiment(self, data):
        """Save market sentiment data to database"""
        if not data:
            return
            
        try:
            conn = sqlite3.connect("intraday_data.db")
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO market_sentiment
            (Date, Overall_Sentiment, Index_Movement, Advancing_Count, Declining_Count,
            New_High_Count, New_Low_Count, Volume_Change, VIX, Notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data["Date"],
                data["Overall_Sentiment"],
                data["Index_Movement"],
                data["Advancing_Count"],
                data["Declining_Count"],
                data["New_High_Count"],
                data["New_Low_Count"],
                data["Volume_Change"],
                data["VIX"],
                data["Notes"]
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error saving market sentiment: {e}")

    def get_stock_data(self, symbol, period="60d", interval="1d"):
        """Get historical data with multiple timeframes for analysis"""
        try:
            # Get data for both daily and intraday analysis
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return None
                
            # Get alternative timeframe for multi-timeframe analysis
            if interval == "1d":
                alt_data = ticker.history(period="10d", interval="1h")
            else:
                alt_data = ticker.history(period="20d", interval="1d")
                
            return {
                "main_data": data,
                "alt_data": alt_data
            }
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_technical_indicators(self, data):
        """Calculate comprehensive technical indicators"""
        if data is None or data["main_data"].empty:
            return None
            
        df = data["main_data"].copy()
        
        # Basic price data
        df['BodySize'] = abs(df['Close'] - df['Open'])
        df['CandleSize'] = df['High'] - df['Low']
        df['BodyToCandle'] = df['BodySize'] / df['CandleSize']
        df['UpperWick'] = df.apply(lambda x: x['High'] - x['Close'] if x['Close'] > x['Open'] else x['High'] - x['Open'], axis=1)
        df['LowerWick'] = df.apply(lambda x: x['Open'] - x['Low'] if x['Close'] > x['Open'] else x['Close'] - x['Low'], axis=1)
        
        # Moving Averages
        df['SMA5'] = df['Close'].rolling(window=5).mean()
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['EMA9'] = ta.trend.ema_indicator(df['Close'], window=9)
        df['EMA21'] = ta.trend.ema_indicator(df['Close'], window=21)
        
        # Volume analysis
        df['VolSMA20'] = df['Volume'].rolling(window=20).mean()
        df['VolRatio'] = df['Volume'] / df['VolSMA20']
        
        # Trend indicators
        df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        df['ATR%'] = df['ATR'] / df['Close'] * 100
        
        # Momentum indicators
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Volatility indicators
        bollinger = ta.volatility.BollingerBands(df['Close'])
        df['BB_Upper'] = bollinger.bollinger_hband()
        df['BB_Lower'] = bollinger.bollinger_lband()
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA20']
        
        # Support/Resistance identification
        df['PrevHigh'] = df['High'].rolling(window=10).max().shift(1)
        df['PrevLow'] = df['Low'].rolling(window=10).min().shift(1)
        
        # Pattern identification
        df['Engulfing'] = (
            ((df['Close'] > df['Open']) & 
             (df['Open'].shift(1) > df['Close'].shift(1)) &
             (df['Open'] < df['Close'].shift(1)) &
             (df['Close'] > df['Open'].shift(1)))
        ).astype(int)
        
        df['InsideBar'] = (
            (df['High'] < df['High'].shift(1)) &
            (df['Low'] > df['Low'].shift(1))
        ).astype(int)
        
        df['OutsideBar'] = (
            (df['High'] > df['High'].shift(1)) &
            (df['Low'] < df['Low'].shift(1))
        ).astype(int)
        
        # Breakout signals
        df['BreakoutLevel'] = df['High'].rolling(window=5).max().shift(1)
        df['BreakdownLevel'] = df['Low'].rolling(window=5).min().shift(1)
        
        # Gap analysis
        df['Gap'] = df['Open'] - df['Close'].shift(1)
        df['GapPercent'] = df['Gap'] / df['Close'].shift(1) * 100
                
        return df

    def identify_patterns(self, df, market_sentiment):
        """Identify high-probability intraday patterns for next day"""
        if df is None or len(df) < 30:
            return None
            
        latest = df.iloc[-1]
        second_last = df.iloc[-2] if len(df) > 1 else None
        
        # Initialize result dictionary
        patterns = []
        
        # Only look at the most recent data for patterns
        recent_df = df.iloc[-20:]
        latest_date = recent_df.index[-1].strftime("%Y-%m-%d")
        
        # Market context
        market_trend = market_sentiment.get("Overall_Sentiment", "Neutral") if market_sentiment else "Neutral"
        
        # 1. Bullish patterns
        if market_trend in ["Bullish", "Neutral"]:
            # Bullish engulfing at support
            if (latest['Engulfing'] == 1 and 
                latest['Low'] <= latest['PrevLow'] * 1.01 and 
                latest['VolRatio'] > 1.0):
                patterns.append({
                    "Setup_Type": "Bullish",
                    "Signal": "Engulfing at Support",
                    "Confidence": "High" if latest['VolRatio'] > 1.5 and latest['ADX'] > 20 else "Medium",
                    "Entry": round(latest['Close'] * 1.005, 2),  # Entry slightly above close
                    "Stop_Loss": round(min(latest['Low'], latest['Low'] - latest['ATR'] * 0.5), 2),
                    "Target1": round(latest['Close'] + latest['ATR'] * 1.5, 2),
                    "Target2": round(latest['Close'] + latest['ATR'] * 2.5, 2),
                    "Pattern": "Bullish Engulfing",
                    "Notes": "Wait for breakout above day's high"
                })
                
            # Pullback to moving average in uptrend
            if (latest['Close'] > latest['SMA20'] > latest['SMA50'] and
                latest['Low'] <= latest['EMA21'] * 1.01 and
                latest['Low'] > latest['EMA21'] * 0.98 and
                latest['RSI'] > 40):
                patterns.append({
                    "Setup_Type": "Bullish",
                    "Signal": "MA Pullback",
                    "Confidence": "High" if latest['ADX'] > 25 else "Medium",
                    "Entry": round(latest['Close'] * 1.01, 2),
                    "Stop_Loss": round(min(latest['Low'], latest['EMA21'] * 0.97), 2),
                    "Target1": round(latest['Close'] + latest['ATR'] * 1.5, 2),
                    "Target2": round(latest['Close'] + latest['ATR'] * 2.5, 2),
                    "Pattern": "EMA21 Support Bounce",
                    "Notes": "Strong trending setup"
                })
                
            # NR4 (Narrow Range) pattern with good volume
            if len(recent_df) >= 5:
                last_4_ranges = [day['High'] - day['Low'] for _, day in recent_df.iloc[-5:-1].iterrows()]
                current_range = latest['High'] - latest['Low']
                if current_range < min(last_4_ranges) and latest['VolRatio'] > 0.8:
                    patterns.append({
                        "Setup_Type": "Bullish",
                        "Signal": "NR4 Breakout",
                        "Confidence": "Medium",
                        "Entry": round(latest['High'] * 1.005, 2),
                        "Stop_Loss": round(latest['Low'] * 0.995, 2),
                        "Target1": round(latest['High'] + (latest['High'] - latest['Low']) * 1.5, 2),
                        "Target2": round(latest['High'] + (latest['High'] - latest['Low']) * 2.5, 2),
                        "Pattern": "Narrow Range",
                        "Notes": "Explosive move potential"
                    })
        
        # 2. Bearish patterns
        if market_trend in ["Bearish", "Neutral"]:
            # Bearish engulfing at resistance
            if (latest['Close'] < latest['Open'] and
                latest['High'] >= latest['PrevHigh'] * 0.99 and
                latest['Open'] > latest['Close'].shift(1) and
                latest['Close'] < latest['Open'].shift(1) and
                latest['VolRatio'] > 1.0):
                patterns.append({
                    "Setup_Type": "Bearish",
                    "Signal": "Engulfing at Resistance",
                    "Confidence": "High" if latest['VolRatio'] > 1.5 and latest['ADX'] > 20 else "Medium",
                    "Entry": round(latest['Close'] * 0.995, 2),  # Entry slightly below close
                    "Stop_Loss": round(max(latest['High'], latest['High'] + latest['ATR'] * 0.5), 2),
                    "Target1": round(latest['Close'] - latest['ATR'] * 1.5, 2),
                    "Target2": round(latest['Close'] - latest['ATR'] * 2.5, 2),
                    "Pattern": "Bearish Engulfing",
                    "Notes": "Wait for breakdown below day's low"
                })
                
            # Failed breakout with rejection
            if (latest['High'] > latest['BreakoutLevel'] and
                latest['Close'] < latest['BreakoutLevel'] and
                latest['VolRatio'] > 1.2):
                patterns.append({
                    "Setup_Type": "Bearish",
                    "Signal": "Failed Breakout",
                    "Confidence": "High" if latest['UpperWick'] > latest['BodySize'] * 1.5 else "Medium",
                    "Entry": round(latest['Low'] * 0.995, 2),
                    "Stop_Loss": round(latest['High'] * 1.005, 2),
                    "Target1": round(latest['Close'] - latest['ATR'] * 1.5, 2),
                    "Target2": round(latest['Close'] - latest['ATR'] * 2.5, 2),
                    "Pattern": "Failed Breakout",
                    "Notes": "Watch for high volume rejection"
                })
        
        # 3. Range-bound plays
        # Inside bar pattern for range breakout
        if latest['InsideBar'] == 1 and latest['VolRatio'] < 0.8:
            # Bullish bias if close in upper half
            if latest['Close'] > (latest['High'] + latest['Low']) / 2:
                patterns.append({
                    "Setup_Type": "Range",
                    "Signal": "Inside Bar Breakout",
                    "Confidence": "Medium",
                    "Entry": round(latest['High'] * 1.005, 2),
                    "Stop_Loss": round(latest['Low'] * 0.995, 2),
                    "Target1": round(latest['High'] + (latest['High'] - latest['Low']), 2),
                    "Target2": round(latest['High'] + (latest['High'] - latest['Low']) * 1.5, 2),
                    "Pattern": "Inside Bar",
                    "Notes": "Wait for mother bar high break"
                })
            # Bearish bias if close in lower half
            else:
                patterns.append({
                    "Setup_Type": "Range",
                    "Signal": "Inside Bar Breakdown",
                    "Confidence": "Medium",
                    "Entry": round(latest['Low'] * 0.995, 2),
                    "Stop_Loss": round(latest['High'] * 1.005, 2),
                    "Target1": round(latest['Low'] - (latest['High'] - latest['Low']), 2),
                    "Target2": round(latest['Low'] - (latest['High'] - latest['Low']) * 1.5, 2),
                    "Pattern": "Inside Bar",
                    "Notes": "Wait for mother bar low break"
                })
        
        # 4. Momentum plays
        # Strong momentum continuation with pullback
        if (latest['Close'] > latest['Open'] and
            latest['Close'] > latest['SMA5'] > latest['SMA20'] and
            latest['RSI'] < 70 and latest['RSI'] > 40 and
            latest['MACD'] > latest['MACD_Signal']):
            patterns.append({
                "Setup_Type": "Momentum",
                "Signal": "Bull Momentum",
                "Confidence": "High" if latest['VolRatio'] > 1.2 and latest['ADX'] > 25 else "Medium",
                "Entry": round(latest['Close'] * 1.01, 2),
                "Stop_Loss": round(min(latest['Low'], latest['SMA5'] * 0.98), 2),
                "Target1": round(latest['Close'] * 1.02, 2),
                "Target2": round(latest['Close'] * 1.04, 2),
                "Pattern": "Momentum Continuation",
                "Notes": "Strong trend continuation setup"
            })
        
        # Enhance patterns with additional metrics
        for pattern in patterns:
            pattern["Symbol"] = df.index.name if df.index.name else "Unknown"
            pattern["Date"] = latest_date
            pattern["Risk_Reward"] = round((pattern["Target1"] - pattern["Entry"]) / (pattern["Entry"] - pattern["Stop_Loss"]), 2)
            pattern["Volume_Ratio"] = round(latest['VolRatio'], 2)
            pattern["Trend_Strength"] = "Strong" if latest['ADX'] > 25 else "Moderate" if latest['ADX'] > 20 else "Weak"
            pattern["Support"] = round(latest['PrevLow'], 2)
            pattern["Resistance"] = round(latest['PrevHigh'], 2)
            pattern["ADX"] = round(latest['ADX'], 2)
            pattern["RSI"] = round(latest['RSI'], 2)
            pattern["MACD_Signal"] = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
            pattern["Volatility"] = round(latest['ATR%'], 2)
            pattern["Risk_Factor"] = round(abs(pattern["Entry"] - pattern["Stop_Loss"]) / latest['Close'] * 100, 2)
            pattern["Expected_Movement"] = round(latest['ATR'] * 1.5, 2)
            pattern["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return patterns

    def create_chart(self, symbol, data, patterns=None):
        """Create a chart for visual confirmation"""

        if data is None or data.empty:
            return False
            
        try:
            df = data.copy()
            
            # Create figure and axis
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
            fig.suptitle(f"{symbol} - Technical Analysis Chart", fontsize=14)
            
            # Plot candlesticks
            width = 0.6
            width2 = 0.05
            up = df[df['Close'] >= df['Open']]
            down = df[df['Close'] < df['Open']]
            
            # Plot up candles
            ax1.bar(up.index, up['Close'] - up['Open'], width, bottom=up['Open'], color='green', alpha=0.6)
            ax1.bar(up.index, up['High'] - up['Close'], width2, bottom=up['Close'], color='green', alpha=0.6)
            ax1.bar(up.index, up['Open'] - up['Low'], width2, bottom=up['Low'], color='green', alpha=0.6)
            
            # Plot down candles
            ax1.bar(down.index, down['Open'] - down['Close'], width, bottom=down['Close'], color='red', alpha=0.6)
            ax1.bar(down.index, down['High'] - down['Open'], width2, bottom=down['Open'], color='red', alpha=0.6)
            ax1.bar(down.index, down['Close'] - down['Low'], width2, bottom=down['Low'], color='red', alpha=0.6)
            
            # Plot moving averages
            ax1.plot(df.index, df['SMA20'], color='blue', linestyle='-', linewidth=1.0, label='SMA20')
            ax1.plot(df.index, df['EMA9'], color='red', linestyle='-', linewidth=1.0, label='EMA9')
            ax1.plot(df.index, df['EMA21'], color='green', linestyle='--', linewidth=1.0, label='EMA21')
            
            # Plot bollinger bands
            ax1.plot(df.index, df['BB_Upper'], color='gray', linestyle='--', linewidth=0.5)
            ax1.plot(df.index, df['BB_Lower'], color='gray', linestyle='--', linewidth=0.5)
            
            # Plot Volume
            ax2.bar(up.index, up['Volume'], width, color='green', alpha=0.6)
            ax2.bar(down.index, down['Volume'], width, color='red', alpha=0.6)
            ax2.plot(df.index, df['VolSMA20'], color='blue', linestyle='-', label='Volume SMA20')
            
            # Highlight patterns if provided
            if patterns:
                for pattern in patterns:
                    # Mark entry, stop and target levels
                    last_idx = df.index[-1]
                    ax1.axhline(y=pattern['Entry'], color='blue', linestyle='-', alpha=0.7, linewidth=1)
                    ax1.axhline(y=pattern['Stop_Loss'], color='red', linestyle='-', alpha=0.7, linewidth=1)
                    ax1.axhline(y=pattern['Target1'], color='green', linestyle='--', alpha=0.7, linewidth=1)
                    
                    # Add labels
                    ax1.text(df.index[-int(len(df)*0.1)], pattern['Entry'], 'Entry', fontsize=8, color='blue')
                    ax1.text(df.index[-int(len(df)*0.1)], pattern['Stop_Loss'], 'Stop', fontsize=8, color='red')
                    ax1.text(df.index[-int(len(df)*0.1)], pattern['Target1'], 'Target', fontsize=8, color='green')
                    
                    # Add pattern info
                    fig.text(0.02, 0.02, f"Setup: {pattern['Signal']} ({pattern['Confidence']}) - R:R {pattern['Risk_Reward']}", fontsize=10)
            
            # Add legends and labels
            ax1.legend(loc='upper left', fontsize=8)
            ax1.set_ylabel('Price')
            ax1.grid(True, alpha=0.3)
            
            ax2.set_ylabel('Volume')
            ax2.grid(True, alpha=0.3)
            
            # Format dates on x-axis
            if len(df) > 30:
                plt.xticks(rotation=45)
                
            plt.tight_layout()
            
            # Save chart
            chart_path = f"{self.output_dir}/charts/{symbol}_chart.png"
            plt.savefig(chart_path)
            plt.close(fig)
            plt.close()
            
            return chart_path
        except Exception as e:
            logging.error(f"Error creating chart for {symbol}: {e}")
            return False

    def process_symbol(self, symbol):
        """Process a single symbol for intraday setups"""
        try:
            logging.info(f"Processing {symbol} for intraday setups")
            
            # Get stock data
            data_dict = self.get_stock_data(symbol)
            if not data_dict:
                return None
                
            # Calculate indicators
            df = self.calculate_technical_indicators(data_dict)
            if df is None:
                return None
                
            # Set the symbol as the index name for reference
            df.index.name = symbol
            
            # Get market sentiment
            market_sentiment = self.get_market_data()
            
            # Identify patterns
            patterns = self.identify_patterns(df, market_sentiment)
            if not patterns:
                return None
                
            # Create chart for visual confirmation
            chart_path = self.create_chart(symbol, df.iloc[-30:], patterns[0] if patterns else None)
            
            # Return identified patterns
            for pattern in patterns:
                pattern["Chart"] = chart_path if chart_path else ""
                
            return patterns
        except Exception as e:
            logging.error(f"Error processing {symbol}: {e}")
            return None

    def save_setups(self, all_setups):
        """Save identified setups to database"""
        if not all_setups:
            return
            
        flattened_setups = []
        for setups in all_setups:
            if setups:
                flattened_setups.extend(setups)
        
        if not flattened_setups:
            logging.info("No setups to save")
            return
            
        try:
            conn = sqlite3.connect("intraday_data.db")
            cursor = conn.cursor()
            
            for setup in flattened_setups:
                cursor.execute('''
                INSERT OR REPLACE INTO intraday_setups
                (Symbol, Date, Setup_Type, Signal, Confidence, Entry, Stop_Loss, Target1, Target2, 
                Risk_Reward, Volume_Ratio, Trend_Strength, Support, Resistance, ADX, RSI, 
                MACD_Signal, Volatility, Risk_Factor, Expected_Movement, Pattern, Notes, Timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    setup["Symbol"],
                    setup["Date"],
                    setup["Setup_Type"],
                    setup["Signal"],
                    setup["Confidence"],
                    setup["Entry"],
                    setup["Stop_Loss"],
                    setup["Target1"],
                    setup["Target2"],
                    setup["Risk_Reward"],
                    setup["Volume_Ratio"],
                    setup["Trend_Strength"],
                    setup["Support"],
                    setup["Resistance"],
                    setup["ADX"],
                    setup["RSI"],
                    setup["MACD_Signal"],
                    setup["Volatility"],
                    setup["Risk_Factor"],
                    setup["Expected_Movement"],
                    setup["Pattern"],
                    setup["Notes"],
                    setup["Timestamp"]
                ))
            
            conn.commit()
            conn.close()
            logging.info(f"Saved {len(flattened_setups)} intraday setups to database")
        except Exception as e:
            logging.error(f"Error saving setups to database: {e}")

    def generate_report(self, setups):
        """Generate HTML report with trading setups for next day"""
        if not setups:
            return
            
        flattened_setups = []
        for s in setups:
            if s:
                flattened_setups.extend(s)
                
        if not flattened_setups:
            logging.info("No setups to report")
            return
            
        try:
            # Sort setups by confidence and risk reward
            sorted_setups = sorted(flattened_setups, 
                                  key=lambda x: (1 if x["Confidence"] == "High" else 0, x["Risk_Reward"]), 
                                  reverse=True)
            
            # Create report header
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            next_trading_day = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            if datetime.now().weekday() == 4:  # Friday
                next_trading_day = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            elif datetime.now().weekday() == 5:  # Saturday
                next_trading_day = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                
            # Get market sentiment
            market_sentiment = self.get_market_data()
            sentiment_text = market_sentiment["Overall_Sentiment"] if market_sentiment else "Neutral"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Intraday Trading Setups for {next_trading_day}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                    .setup {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                    .high {{ border-left: 5px solid green; }}
                    .medium {{ border-left: 5px solid orange; }}
                    .bullish {{ background-color: rgba(0, 255, 0, 0.05); }}
                    .bearish {{ background-color: rgba(255, 0, 0, 0.05); }}
                    .range {{ background-color: rgba(0, 0, 255, 0.05); }}
                    .momentum {{ background-color: rgba(255, 165, 0, 0.05); }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .chart {{ margin-top: 15px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Intraday Trading Setups for {next_trading_day}</h1>
                    <p>Generated on: {now}</p>
                    <p>Market Sentiment: <strong>{sentiment_text}</strong></p>
                    <p>Total Setups Found: <strong>{len(sorted_setups)}</strong></p>
                </div>
            """
            
            # Add each setup
            for setup in sorted_setups:
                confidence_class = "high" if setup["Confidence"] == "High" else "medium"
                setup_class = setup["Setup_Type"].lower()
                
                html += f"""
                <div class="setup {confidence_class} {setup_class}">
                    <h2>{setup["Symbol"]} - {setup["Signal"]} ({setup["Confidence"]})</h2>
                    <p><strong>Pattern:</strong> {setup["Pattern"]}</p>
                    <p><strong>Notes:</strong> {setup["Notes"]}</p>
                    
                    <table>
                        <tr>
                            <th>Entry</th>
                            <th>Stop Loss</th>
                            <th>Target 1</th>
                            <th>Target 2</th>
                            <th>Risk:Reward</th>
                        </tr>
                        <tr>
                            <td>{setup["Entry"]}</td>
                            <td>{setup["Stop_Loss"]}</td>
                            <td>{setup["Target1"]}</td>
                            <td>{setup["Target2"]}</td>
                            <td>{setup["Risk_Reward"]}</td>
                        </tr>
                    </table>
                    
                    <table style="margin-top: 15px;">
                        <tr>
                            <th>ADX</th>
                            <th>RSI</th>
                            <th>Volume Ratio</th>
                            <th>Trend Strength</th>
                            <th>MACD Signal</th>
                        </tr>
                        <tr>
                            <td>{setup["ADX"]}</td>
                            <td>{setup["RSI"]}</td>
                            <td>{setup["Volume_Ratio"]}</td>
                            <td>{setup["Trend_Strength"]}</td>
                            <td>{setup["MACD_Signal"]}</td>
                        </tr>
                    </table>
                """
                
                # Add chart if available
                if "Chart" in setup and setup["Chart"]:
                    chart_filename = setup["Chart"].split("/")[-1]
                    html += f"""
                    <div class="chart">
                        <img src="charts/{chart_filename}" alt="{setup["Symbol"]} Chart" style="max-width: 100%; height: auto;">
                    </div>
                    """
                    
                html += "</div>"
                
            # Close HTML
            html += """
            </body>
            </html>
            """
            
            # Save report
            report_path = f"{self.output_dir}/intraday_setups_{next_trading_day.replace('-', '')}.html"
            with open(report_path, "w") as f:
                f.write(html)
                
            logging.info(f"Generated report saved to {report_path}")
            return report_path
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            return None

    def rank_setups(self, all_setups):
        """Rank setups based on multiple factors"""
        if not all_setups:
            return []
            
        flattened_setups = []
        for setups in all_setups:
            if setups:
                flattened_setups.extend(setups)
                
        if not flattened_setups:
            return []
            
        # Calculate score for each setup
        for setup in flattened_setups:
            # Base score from confidence
            if setup["Confidence"] == "High":
                setup["Score"] = 5
            elif setup["Confidence"] == "Medium":
                setup["Score"] = 3
            else:
                setup["Score"] = 1
                
            # Add points for good risk:reward
            if setup["Risk_Reward"] >= 3:
                setup["Score"] += 3
            elif setup["Risk_Reward"] >= 2:
                setup["Score"] += 2
            elif setup["Risk_Reward"] >= 1.5:
                setup["Score"] += 1
                
            # Add points for trend alignment
            if setup["Setup_Type"] == "Bullish" and setup["Trend_Strength"] == "Strong" and setup["MACD_Signal"] == "Bullish":
                setup["Score"] += 2
            elif setup["Setup_Type"] == "Bearish" and setup["Trend_Strength"] == "Strong" and setup["MACD_Signal"] == "Bearish":
                setup["Score"] += 2
                
            # Add points for good volume
            if setup["Volume_Ratio"] >= 1.5:
                setup["Score"] += 2
            elif setup["Volume_Ratio"] >= 1.0:
                setup["Score"] += 1
                
            # Adjust for extreme RSI
            if setup["Setup_Type"] == "Bullish" and setup["RSI"] < 30:
                setup["Score"] += 1
            elif setup["Setup_Type"] == "Bearish" and setup["RSI"] > 70:
                setup["Score"] += 1
                
            # Penalize for high risk factor
            if setup["Risk_Factor"] > 3.0:
                setup["Score"] -= 2
            elif setup["Risk_Factor"] > 2.0:
                setup["Score"] -= 1
        
        # Sort by score
        return sorted(flattened_setups, key=lambda x: x["Score"], reverse=True)

    def run(self):
        """Run the screener to find next-day intraday setups"""
        logging.info("Starting intraday screener")
        
        # Process each symbol
        all_setups = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {executor.submit(self.process_symbol, symbol): symbol for symbol in NSE_SYMBOLS}
            for future in future_to_symbol:
                try:
                    setup = future.result()
                    if setup:
                        all_setups.append(setup)
                        time.sleep(0.5)  # Small delay to avoid overloading
                except Exception as e:
                    logging.error(f"Error in thread: {e}")
        
        # Save all setups to database
        self.save_setups(all_setups)
        
        # Rank setups
        ranked_setups = self.rank_setups(all_setups)
        
        # Generate report
        report_path = self.generate_report(all_setups)
        
        # Print summary
        if ranked_setups:
            print(f"\nTop Intraday Trading Setups for Next Trading Day:")
            for i, setup in enumerate(ranked_setups[:10], 1):
                print(f"{i}. {setup['Symbol']} - {setup['Signal']} ({setup['Confidence']}) - R:R {setup['Risk_Reward']}")
                print(f"   Entry: {setup['Entry']} | Stop: {setup['Stop_Loss']} | Target: {setup['Target1']}")
                print(f"   Setup Score: {setup['Score']}")
                print()
                
            if report_path:
                print(f"\nDetailed report saved to: {report_path}")
        else:
            print("No high-probability intraday setups found for next trading day.")
            
        return ranked_setups


class IntradayBacktester:
    """Class to backtest the intraday setups"""
    
    def __init__(self, db_path="intraday_data.db"):
        self.db_path = db_path
        
    def get_historical_setups(self, days=30):
        """Get historical setups from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get setups from last N days
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute('''
            SELECT * FROM intraday_setups
            WHERE Date >= ?
            ORDER BY Date DESC
            ''', (from_date,))
            
            setups = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dicts
            setup_dicts = []
            for setup in setups:
                setup_dict = dict(zip(columns, setup))
                setup_dicts.append(setup_dict)
                
            conn.close()
            return setup_dicts
        except Exception as e:
            logging.error(f"Error getting historical setups: {e}")
            return []
            
    def get_next_day_data(self, symbol, date):
        """Get next day's data for a symbol after a specific date"""
        try:
            # Convert date string to datetime
            setup_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Calculate next trading day
            next_day = setup_date + timedelta(days=1)
            if next_day.weekday() >= 5:  # Weekend
                next_day = next_day + timedelta(days=(7 - next_day.weekday()))
                
            # Format as string
            next_day_str = next_day.strftime("%Y-%m-%d")
            
            # Get data for that day
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(start=next_day_str, end=(next_day + timedelta(days=1)).strftime("%Y-%m-%d"), interval="5m")
            
            return data
        except Exception as e:
            logging.error(f"Error getting next day data for {symbol} on {date}: {e}")
            return None
            
    def evaluate_setup(self, setup, next_day_data):
        """Evaluate the performance of a setup"""
        if next_day_data is None or next_day_data.empty:
            return None
            
        try:
            result = {
                "Symbol": setup["Symbol"],
                "Date": setup["Date"],
                "Setup_Type": setup["Setup_Type"],
                "Signal": setup["Signal"],
                "Entry": setup["Entry"],
                "Stop_Loss": setup["Stop_Loss"],
                "Target1": setup["Target1"],
                "Target2": setup["Target2"]
            }
            
            # Get entry, stop and target prices
            entry_price = float(setup["Entry"])
            stop_loss = float(setup["Stop_Loss"])
            target1 = float(setup["Target1"])
            target2 = float(setup["Target2"])
            
            # Get next day's high, low
            day_high = next_day_data["High"].max()
            day_low = next_day_data["Low"].min()
            
            # Check if entry was triggered
            entry_triggered = False
            if setup["Setup_Type"] in ["Bullish", "Momentum"] and day_low <= entry_price <= day_high:
                entry_triggered = True
            elif setup["Setup_Type"] in ["Bearish"] and day_low <= entry_price <= day_high:
                entry_triggered = True
            elif setup["Setup_Type"] in ["Range"] and day_low <= entry_price <= day_high:
                entry_triggered = True
                
            result["Entry_Triggered"] = entry_triggered
            
            if entry_triggered:
                # Check if stop loss was hit
                stop_hit = False
                if setup["Setup_Type"] in ["Bullish", "Momentum"] and day_low <= stop_loss:
                    stop_hit = True
                elif setup["Setup_Type"] in ["Bearish"] and day_high >= stop_loss:
                    stop_hit = True
                elif setup["Setup_Type"] in ["Range"]:
                    if entry_price > stop_loss and day_low <= stop_loss:
                        stop_hit = True
                    elif entry_price < stop_loss and day_high >= stop_loss:
                        stop_hit = True
                        
                result["Stop_Hit"] = stop_hit
                
                # Check if targets were hit
                target1_hit = False
                target2_hit = False
                
                if setup["Setup_Type"] in ["Bullish", "Momentum"] and day_high >= target1:
                    target1_hit = True
                    if day_high >= target2:
                        target2_hit = True
                elif setup["Setup_Type"] in ["Bearish"] and day_low <= target1:
                    target1_hit = True
                    if day_low <= target2:
                        target2_hit = True
                elif setup["Setup_Type"] in ["Range"]:
                    if entry_price < target1 and day_high >= target1:
                        target1_hit = True
                        if day_high >= target2:
                            target2_hit = True
                    elif entry_price > target1 and day_low <= target1:
                        target1_hit = True
                        if day_low <= target2:
                            target2_hit = True
                            
                result["Target1_Hit"] = target1_hit
                result["Target2_Hit"] = target2_hit
                
                # Calculate outcome
                if stop_hit and not (target1_hit or target2_hit):
                    result["Outcome"] = "Loss"
                    result["Profit_Factor"] = -1.0
                elif target1_hit and not stop_hit:
                    result["Outcome"] = "Win"
                    if target2_hit:
                        result["Profit_Factor"] = abs((target2 - entry_price) / (entry_price - stop_loss))
                    else:
                        result["Profit_Factor"] = abs((target1 - entry_price) / (entry_price - stop_loss))
                elif target1_hit and stop_hit:
                    # Need to check which happened first - for this we'd need time series analysis
                    # For simplicity, we'll assume breakeven
                    result["Outcome"] = "Breakeven"
                    result["Profit_Factor"] = 0.0
                else:
                    # Neither stop nor target hit - would close at end of day
                    close_price = next_day_data["Close"].iloc[-1]
                    if setup["Setup_Type"] in ["Bullish", "Momentum"]:
                        pnl = close_price - entry_price
                    elif setup["Setup_Type"] in ["Bearish"]:
                        pnl = entry_price - close_price
                    else:  # Range
                        if entry_price < target1:  # Long position
                            pnl = close_price - entry_price
                        else:  # Short position
                            pnl = entry_price - close_price
                            
                    risk = abs(entry_price - stop_loss)
                    result["Profit_Factor"] = pnl / risk
                    
                    if result["Profit_Factor"] > 0:
                        result["Outcome"] = "Small Win"
                    elif result["Profit_Factor"] < 0:
                        result["Outcome"] = "Small Loss"
                    else:
                        result["Outcome"] = "Breakeven"
            else:
                result["Outcome"] = "No Entry"
                result["Profit_Factor"] = 0.0
                result["Stop_Hit"] = False
                result["Target1_Hit"] = False
                result["Target2_Hit"] = False
                
            return result
        except Exception as e:
            logging.error(f"Error evaluating setup: {e}")
            return None
            
    def run_backtest(self, days=30):
        """Run backtest on historical setups"""
        # Get historical setups
        setups = self.get_historical_setups(days)
        if not setups:
            print("No historical setups found for backtesting")
            return None
            
        print(f"Running backtest on {len(setups)} historical setups...")
        
        results = []
        for setup in setups:
            # Get next day data
            next_day_data = self.get_next_day_data(setup["Symbol"], setup["Date"])
            
            # Evaluate setup
            if next_day_data is not None:
                result = self.evaluate_setup(setup, next_day_data)
                if result:
                    results.append(result)
                    
        # Generate backtest report
        if results:
            self.generate_backtest_report(results)
            
        return results
        
    def generate_backtest_report(self, results):
        """Generate backtest report"""
        if not results:
            return
            
        # Calculate statistics
        total_setups = len(results)
        entry_triggered = sum(1 for r in results if r.get("Entry_Triggered", False))
        entry_rate = round(entry_triggered / total_setups * 100, 2) if total_setups > 0 else 0
        
        wins = sum(1 for r in results if r.get("Outcome") in ["Win", "Small Win"])
        losses = sum(1 for r in results if r.get("Outcome") in ["Loss", "Small Loss"])
        breakeven = sum(1 for r in results if r.get("Outcome") == "Breakeven")
        no_entry = sum(1 for r in results if r.get("Outcome") == "No Entry")
        
        win_rate = round(wins / entry_triggered * 100, 2) if entry_triggered > 0 else 0
        
        # Calculate profit factor
        total_profit = sum(r.get("Profit_Factor", 0) for r in results if r.get("Profit_Factor", 0) > 0)
        total_loss = abs(sum(r.get("Profit_Factor", 0) for r in results if r.get("Profit_Factor", 0) < 0))
        profit_factor = round(total_profit / total_loss, 2) if total_loss > 0 else float('inf')
        
        # Group by setup type
        setup_types = {}
        for r in results:
            setup_type = r.get("Setup_Type")
            if setup_type not in setup_types:
                setup_types[setup_type] = {
                    "count": 0,
                    "wins": 0,
                    "losses": 0,
                    "breakeven": 0,
                    "no_entry": 0
                }
                
            setup_types[setup_type]["count"] += 1
            if r.get("Outcome") in ["Win", "Small Win"]:
                setup_types[setup_type]["wins"] += 1
            elif r.get("Outcome") in ["Loss", "Small Loss"]:
                setup_types[setup_type]["losses"] += 1
            elif r.get("Outcome") == "Breakeven":
                setup_types[setup_type]["breakeven"] += 1
            elif r.get("Outcome") == "No Entry":
                setup_types[setup_type]["no_entry"] += 1
                
        # Print results
        print("\n=== BACKTEST RESULTS ===")
        print(f"Total Setups: {total_setups}")
        print(f"Entry Triggered: {entry_triggered} ({entry_rate}%)")
        print(f"Win Rate: {win_rate}%")
        print(f"Profit Factor: {profit_factor}")
        print(f"Wins: {wins}, Losses: {losses}, Breakeven: {breakeven}, No Entry: {no_entry}")
        
        print("\nResults by Setup Type:")
        for setup_type, stats in setup_types.items():
            win_rate = round(stats["wins"] / (stats["wins"] + stats["losses"]) * 100, 2) if (stats["wins"] + stats["losses"]) > 0 else 0
            print(f"{setup_type}: {stats['count']} setups, {win_rate}% win rate")
            print(f"  Wins: {stats['wins']}, Losses: {stats['losses']}, Breakeven: {stats['breakeven']}, No Entry: {stats['no_entry']}")
            
        # Generate HTML report
        self.generate_html_backtest_report(results, {
            "total_setups": total_setups,
            "entry_triggered": entry_triggered,
            "entry_rate": entry_rate,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "no_entry": no_entry,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "setup_types": setup_types
        })
        
    def generate_html_backtest_report(self, results, stats):
        """Generate HTML backtest report"""
        try:
            # Create report file
            now = datetime.now().strftime("%Y-%m-%d")
            report_path = f"backtest_report_{now}.html"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Intraday Strategy Backtest Results</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                    .stats {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                    .stat-box {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; width: 30%; text-align: center; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .win {{ color: green; }}
                    .loss {{ color: red; }}
                    .neutral {{ color: orange; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Intraday Strategy Backtest Results</h1>
                    <p>Generated on: {now}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>Win Rate</h3>
                        <h2 class="{('win' if stats['win_rate'] >= 60 else 'neutral' if stats['win_rate'] >= 45 else 'loss')}">{stats['win_rate']}%</h2>
                        <p>{stats['wins']} wins, {stats['losses']} losses</p>
                    </div>
                    <div class="stat-box">
                        <h3>Profit Factor</h3>
                        <h2 class="{('win' if stats['profit_factor'] >= 1.5 else 'neutral' if stats['profit_factor'] >= 1 else 'loss')}">{stats['profit_factor']}</h2>
                        <p>Profit to Loss Ratio</p>
                    </div>
                    <div class="stat-box">
                        <h3>Entry Rate</h3>
                        <h2>{stats['entry_rate']}%</h2>
                        <p>{stats['entry_triggered']} of {stats['total_setups']} setups</p>
                    </div>
                </div>
                
                <h2>Performance by Setup Type</h2>
                <table>
                    <tr>
                        <th>Setup Type</th>
                        <th>Count</th>
                        <th>Win Rate</th>
                        <th>Wins</th>
                        <th>Losses</th>
                        <th>Breakeven</th>
                        <th>No Entry</th>
                    </tr>
            """
            
            # Add setup type rows
            for setup_type, type_stats in stats["setup_types"].items():
                win_rate = round(type_stats["wins"] / (type_stats["wins"] + type_stats["losses"]) * 100, 2) if (type_stats["wins"] + type_stats["losses"]) > 0 else 0
                
                html += f"""
                <tr>
                    <td>{setup_type}</td>
                    <td>{type_stats['count']}</td>
                    <td class="{('win' if win_rate >= 60 else 'neutral' if win_rate >= 45 else 'loss')}">{win_rate}%</td>
                    <td>{type_stats['wins']}</td>
                    <td>{type_stats['losses']}</td>
                    <td>{type_stats['breakeven']}</td>
                    <td>{type_stats['no_entry']}</td>
                </tr>
                """
                
            html += """
                </table>
                
                <h2>Individual Setup Results</h2>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Date</th>
                        <th>Setup Type</th>
                        <th>Signal</th>
                        <th>Entry Triggered</th>
                        <th>Outcome</th>
                        <th>Profit Factor</th>
                    </tr>
            """
            
            # Add individual result rows
            for result in results:
                outcome_class = "win" if result.get("Outcome") in ["Win", "Small Win"] else "loss" if result.get("Outcome") in ["Loss", "Small Loss"] else "neutral"
                
                html += f"""
                <tr>
                    <td>{result.get('Symbol')}</td>
                    <td>{result.get('Date')}</td>
                    <td>{result.get('Setup_Type')}</td>
                    <td>{result.get('Signal')}</td>
                    <td>{"Yes" if result.get('Entry_Triggered') else "No"}</td>
                    <td class="{outcome_class}">{result.get('Outcome')}</td>
                    <td>{round(result.get('Profit_Factor', 0), 2)}</td>
                </tr>
                """
                
            html += """
                </table>
            </body>
            </html>
            """
            
            # Write to file
            with open(report_path, "w") as f:
                f.write(html)
                
            print(f"\nBacktest report saved to: {report_path}")
        except Exception as e:
            logging.error(f"Error generating HTML backtest report: {e}")


if __name__ == "__main__":
    try:
        # Initialize with welcome message
        print("\n" + "="*50)
        print("Intraday Stock Screener")
        print("="*50 + "\n")
        
        # Run the screener
        print("Running stock screener to identify today's setups...")
        screener = IntradayScreener()
        setups = screener.run()
        
        # Show screener results
        if setups:
            report_path = f"{screener.output_dir}/intraday_setups_{datetime.now().strftime('%Y%m%d')}.html"
            print(f"\nToday's trading setups saved to: {report_path}")
            
            # Automatically open the report
            try:
                import webbrowser
                webbrowser.open('file://' + os.path.abspath(report_path))
            except Exception as e:
                print(f"Could not automatically open the report in browser: {e}")
        else:
            print("\nNo setups found today.")
            
        print("\nScreening complete. Exiting program...")
        
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"\nError occurred: {e}")