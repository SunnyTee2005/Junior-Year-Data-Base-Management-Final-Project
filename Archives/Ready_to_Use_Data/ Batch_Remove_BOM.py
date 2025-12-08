import pandas as pd
import glob
import os

# 1. 告訴使用者現在程式在哪裡執行
current_path = os.getcwd()
print(f"📍 程式當前執行位置: {current_path}")

# 2. 取得當前目錄下所有 .csv 檔案
csv_files = glob.glob('*.csv')

print(f"🔍 在此路徑下找到 {len(csv_files)} 個 CSV 檔案")
print("-" * 30)

if len(csv_files) == 0:
    print("❌ 錯誤：找不到任何 CSV 檔案！")
    print("👉 請確認：此 Python 檔是否跟 .csv 檔放在「同一個資料夾」內？")
    exit()

for file in csv_files:
    try:
        if file.endswith('.py'): continue
        
        print(f"正在處理: {file}...", end="")
        
        # 讀取並去除 BOM
        df = pd.read_csv(file, encoding='utf-8-sig')
        df.to_csv(file, index=False, encoding='utf-8')
        
        print(" [成功 ✅]")
        
    except Exception as e:
        print(f" [失敗 ❌] {e}")

print("-" * 30)
print("處理結束。")