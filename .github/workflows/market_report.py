import os
import json
import time
import pandas as pd
import yfinance as yf
from datetime import datetime

# Complete FNO & Major NSE Watchlist Fallback
FNO_STOCKS = [
    "AARTIIND.NS","ABB.NS","ABBOTINDIA.NS","ABCAPITAL.NS","ABFRL.NS","ACC.NS","ADANIENT.NS","ADANIPORTS.NS","ALKEM.NS","AMBUJACEM.NS",
    "APOLLOHOSP.NS","APOLLOTYRE.NS","ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","ATUL.NS","AUBANK.NS","AUROPHARMA.NS","AXISBANK.NS","BAJAJ-AUTO.NS",
    "BAJAJFINSV.NS","BAJFINANCE.NS","BALKRISIND.NS","BALRAMCHIN.NS","BANDHANBNK.NS","BANKBARODA.NS","BATAINDIA.NS","BEL.NS","BERGEPAINT.NS","BHARATFORG.NS",
    "BHARTIARTL.NS","BHEL.NS","BIOCON.NS","BSOFT.NS","BPCL.NS","BRITANNIA.NS","CANBK.NS","CANFINHOME.NS","CHAMBLFERT.NS","CHOLAFIN.NS",
    "CIPLA.NS","COALINDIA.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","COROMANDEL.NS","CROMPTON.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS",
    "DEEPAKNTR.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","LALPATHLAB.NS","DRREDDY.NS","EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS",
    "GAIL.NS","GLENMARK.NS","GMRINFRA.NS","GNFC.NS","GODREJCP.NS","GODREJPROP.NS","GRANULES.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS",
    "HAVELLS.NS","HCLTECH.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDCOPPER.NS","HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS",
    "ICICIGI.NS","ICICIPRULI.NS","IDEA.NS","IDFC.NS","IDFCFIRSTB.NS","IEX.NS","IGL.NS","INDHOTEL.NS","INDIACEM.NS","INDIAMART.NS",
    "INDIGO.NS","INDUSINDBK.NS","INDUSTOWER.NS","INFY.NS","IOC.NS","IPCALAB.NS","IRCTC.NS","ITC.NS","JINDALSTEL.NS","JKCEMENT.NS",
    "JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS","LT.NS","LTIM.NS","LTTS.NS","LUPIN.NS","M&M.NS","M&MFIN.NS","MANAPPURAM.NS",
    "MARUTI.NS","MCDOWELL-N.NS","MCX.NS","METROPOLIS.NS","MFSL.NS","MGL.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS","MUTHOOTFIN.NS",
    "NATIONALUM.NS","NAVINFLUOR.NS","NESTLEIND.NS","NMDC.NS","NTPC.NS","OBEROIRLTY.NS","OFSS.NS","ONGC.NS","PAGEIND.NS","PERSISTENT.NS",
    "PETRONET.NS","PFC.NS","PIDILITIND.NS","PIIND.NS","PNB.NS","POLYCAB.NS","POWERGRID.NS","PVRINOX.NS","RAMCOCEM.NS","RBLBANK.NS",
    "REC.NS","RELIANCE.NS","SAIL.NS","SBICARD.NS","SBILIFE.NS","SBIN.NS","SHREECEM.NS","SHRIRAMFIN.NS","SIEMENS.NS","SRF.NS",
    "SUNPHARMA.NS","SUNTV.NS","SYNGENE.NS","TATACHEM.NS","TATACOMM.NS","TATACONSUM.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS","TCS.NS",
    "TECHM.NS","TITAN.NS","TORNTPHARM.NS","TRENT.NS","TVSMOTOR.NS","UBL.NS","ULTRACEMCO.NS","UPL.NS","VEDL.NS","VOLTAS.NS","WIPRO.NS","ZEEL.NS"
]

def fetch_stock_metrics(symbols):
    print(f"Fetching data for {len(symbols)} stocks...")
    results = []
    chunk_size = 25
    
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i + chunk_size]
        try:
            data = yf.download(chunk, period="3mo", interval="1d", group_by='ticker', threads=True, progress=False)
            for sym in chunk:
                try:
                    df = data[sym] if len(chunk) > 1 else data
                    if 'Close' in df and not df['Close'].dropna().empty:
                        close = df['Close'].dropna()
                        if len(close) >= 5:
                            curr = float(close.iloc[-1])
                            d1 = float(close.iloc[-2]) if len(close) >= 2 else curr
                            w1 = float(close.iloc[-6]) if len(close) >= 6 else float(close.iloc[0])
                            m1 = float(close.iloc[-22]) if len(close) >= 22 else float(close.iloc[0])
                            m3 = float(close.iloc[0])

                            results.append({
                                'Stock Name': sym.replace('.NS', ''),
                                'chg1D': round(((curr - d1) / d1) * 100, 2),
                                'chg1W': round(((curr - w1) / w1) * 100, 2),
                                'chg1M': round(((curr - m1) / m1) * 100, 2),
                                'chg3M': round(((curr - m3) / m3) * 100, 2)
                            })
                except Exception:
                    continue
        except Exception as e:
            print(f"Batch fetch error at index {i}: {e}")
        time.sleep(0.1)
        
    return pd.DataFrame(results)

def format_side_by_side(df_res):
    if df_res.empty:
        return pd.DataFrame()

    t1d = df_res.sort_values(by='chg1D', ascending=False).head(10)[['Stock Name', 'chg1D']].reset_index(drop=True)
    t1w = df_res.sort_values(by='chg1W', ascending=False).head(10)[['Stock Name', 'chg1W']].reset_index(drop=True)
    t1m = df_res.sort_values(by='chg1M', ascending=False).head(10)[['Stock Name', 'chg1M']].reset_index(drop=True)
    t3m = df_res.sort_values(by='chg3M', ascending=False).head(10)[['Stock Name', 'chg3M']].reset_index(drop=True)

    t1d.columns = ['1D Stock', '1D %Chng']
    t1w.columns = ['1W Stock', '1W %Chng']
    t1m.columns = ['1M Stock', '1M %Chng']
    t3m.columns = ['3M Stock', '3M %Chng']

    for col in ['1D %Chng', '1W %Chng', '1M %Chng', '3M %Chng']:
        if col in t1d: t1d[col] = t1d[col].apply(lambda x: f"+{x}%" if x >= 0 else f"{x}%")
        if col in t1w: t1w[col] = t1w[col].apply(lambda x: f"+{x}%" if x >= 0 else f"{x}%")
        if col in t1m: t1m[col] = t1m[col].apply(lambda x: f"+{x}%" if x >= 0 else f"{x}%")
        if col in t3m: t3m[col] = t3m[col].apply(lambda x: f"+{x}%" if x >= 0 else f"{x}%")

    return pd.concat([t1d, t1w, t1m, t3m], axis=1)

def main():
    print("Starting processing...")
    fno_raw = fetch_stock_metrics(FNO_STOCKS)
    fno_formatted = format_side_by_side(fno_raw)

    file_name = f"NSE_Market_Top10_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        if not fno_formatted.empty:
            fno_formatted.to_excel(writer, sheet_name='FNO_Top_Gainers', index=False)
        else:
            pd.DataFrame({'Message': ['Data processing failed']}).to_excel(writer, sheet_name='FNO_Top_Gainers', index=False)

    print(f"File created successfully: {file_name}")

if __name__ == "__main__":
    main()


