import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import google.auth
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Fetching NSE All Stocks List
def get_nse_symbols():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        df = pd.read_csv(url)
        symbols = [str(symbol).strip() + ".NS" for symbol in df['SYMBOL'].tolist()]
        return symbols
    except Exception as e:
        print("Fallback to major stocks list:", e)
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

def fetch_stock_returns(symbols):
    print(f"Scanning {len(symbols)} stocks...")
    # Fetching 3 months data in batch (Fast Multithreading)
    data = yf.download(symbols, period="3mo", interval="1d", group_by='ticker', threads=True)
    
    results = []
    for symbol in symbols:
        try:
            if len(symbols) == 1:
                df_stock = data
            else:
                df_stock = data[symbol]
            
            df_clean = df_stock['Close'].dropna()
            if len(df_clean) > 5:
                curr = df_clean.iloc[-1]
                d1 = df_clean.iloc[-2] if len(df_clean) >= 2 else curr
                w1 = df_clean.iloc[-6] if len(df_clean) >= 6 else df_clean.iloc[0]
                m1 = df_clean.iloc[-22] if len(df_clean) >= 22 else df_clean.iloc[0]
                m3 = df_clean.iloc[0]

                results.append({
                    'Stock Name': symbol.replace('.NS', ''),
                    'Price': round(curr, 2),
                    'chg1D': ((curr - d1) / d1) * 100,
                    'chg1W': ((curr - w1) / w1) * 100,
                    'chg1M': ((curr - m1) / m1) * 100,
                    'chg3M': ((curr - m3) / m3) * 100
                })
        except Exception:
            continue
            
    return pd.DataFrame(results)

def get_side_by_side_df(df_res):
    t1d = df_res.sort_values(by='chg1D', ascending=False).head(10)[['Stock Name', 'chg1D']].reset_index(drop=True)
    t1w = df_res.sort_values(by='chg1W', ascending=False).head(10)[['Stock Name', 'chg1W']].reset_index(drop=True)
    t1m = df_res.sort_values(by='chg1M', ascending=False).head(10)[['Stock Name', 'chg1M']].reset_index(drop=True)
    t3m = df_res.sort_values(by='chg3M', ascending=False).head(10)[['Stock Name', 'chg3M']].reset_index(drop=True)

    t1d.columns = ['1D Stock', '1D %Chng']
    t1w.columns = ['1W Stock', '1W %Chng']
    t1m.columns = ['1M Stock', '1M %Chng']
    t3m.columns = ['3M Stock', '3M %Chng']

    # Formatting percentages
    for col in ['1D %Chng', '1W %Chng', '1M %Chng', '3M %Chng']:
        if col in locals(): pass

    combined = pd.concat([t1d, t1w, t1m, t3m], axis=1)
    return combined

def main():
    symbols = get_nse_symbols()
    df_res = fetch_stock_returns(symbols)
    
    side_by_side = get_side_by_side_df(df_res)
    
    file_name = f"NSE_All_Stocks_Top10_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        side_by_side.to_excel(writer, sheet_name='NSE_Total_Market', index=False)
        
    print("Report generated locally successfully!")

    # Drive Upload Logic
    creds_json = os.environ.get('GCP_SA_KEY')
    folder_id = os.environ.get('DRIVE_FOLDER_ID')

    if creds_json and folder_id:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print('Uploaded to Google Drive! File ID:', file.get('id'))

if __name__ == "__main__":
    main()
