import os
import json
import time
import pandas as pd
import yfinance as yf
from datetime import datetime

# Complete FNO List (~180 Stocks)
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

def get_nse_all_symbols():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url)
        symbols = [str(sym).strip() + ".NS" for sym in df['SYMBOL'].dropna().tolist()]
        if len(symbols) > 100:
            return symbols
    except Exception as e:
        print("NSE CSV fetch error, using fallback list:", e)
    return FNO_STOCKS

def fetch_data_in_batches(symbols, batch_size=50):
    results = []
    total = len(symbols)
    print(f"Total tickers to process: {total}")

    for i in range(0, total, batch_size):
        chunk = symbols[i:i + batch_size]
        print(f"Fetching batch {i//batch_size + 1} of {(total // batch_size) + 1}...")
        
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
            print(f"Batch fetch error for {i}:", e)
        time.sleep(0.5)

    return pd.DataFrame(results)

def build_side_by_side_df(df_res):
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

    combined = pd.concat([t1d, t1w, t1m, t3m], axis=1)
    return combined

def main():
    print("--- Starting Market Report Generation ---")
    
    # 1. FNO Stocks
    fno_raw = fetch_data_in_batches(FNO_STOCKS, batch_size=40)
    fno_side = build_side_by_side_df(fno_raw)

    # 2. Total NSE Stocks
    nse_symbols = get_nse_all_symbols()
    nse_raw = fetch_data_in_batches(nse_symbols, batch_size=50)
    nse_side = build_side_by_side_df(nse_raw)

    file_name = f"NSE_Market_Top10_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        if not fno_side.empty:
            fno_side.to_excel(writer, sheet_name='FNO_Top_Gainers', index=False)
        if not nse_side.empty:
            nse_side.to_excel(writer, sheet_name='NSE_Total_Market', index=False)

    print(f"SUCCESS: Excel File Generated -> {file_name}")

    # Drive Upload
    creds_json = os.environ.get('GCP_SA_KEY')
    folder_id = os.environ.get('DRIVE_FOLDER_ID')

    if creds_json and folder_id:
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            info = json.loads(creds_json)
            creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive'])
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {'name': file_name, 'parents': [folder_id]}
            media = MediaFileUpload(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print('Uploaded to Drive! File ID:', file.get('id'))
        except Exception as e:
            print("Drive Upload Warning (File saved locally):", e)
    else:
        print("Drive Secrets not set properly. File generated locally.")

if __name__ == "__main__":
    main()


