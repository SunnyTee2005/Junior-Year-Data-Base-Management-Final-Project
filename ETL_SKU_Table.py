import pandas as pd
import numpy as np
import re

# --- 1. 讀取資料 ---
try:
    # 原始資料
    raw_df = pd.read_csv('laptop.csv', encoding='latin-1')
    # 剛剛產生的 Product 表 (為了拿 ProductID)
    product_df = pd.read_csv('product_table.csv') 
    print("成功讀取原始資料與 Product 表。")
except FileNotFoundError:
    print("錯誤：找不到檔案。請確認 laptop.csv 和 product_table.csv 都在同一個資料夾。")
    exit()

# --- 2. 定義清洗函式 ---

# 清洗名稱 (為了跟 Product 表做對應，邏輯必須跟上一步一樣)
def clean_product_name(raw_name):
    if '(' in str(raw_name):
        return str(raw_name).split('(')[0].strip()
    return str(raw_name).strip()

# 清洗 RAM: "16 GB" -> 16 (int)
def clean_ram(ram_str):
    if pd.isna(ram_str): return 8 # 預設值
    # 移除非數字字元
    digits = re.findall(r'\d+', str(ram_str))
    if digits:
        return int(digits[0])
    return 8

# 清洗 Storage: 合併 SSD 和 HDD 欄位
def clean_storage(row):
    ssd = str(row['SSD']).strip()
    hdd = str(row['HDD']).strip()
    storage_info = []
    
    if 'No' not in ssd and ssd != 'nan':
        storage_info.append(ssd)
    if 'No' not in hdd and hdd != 'nan':
        storage_info.append(hdd)
        
    return " + ".join(storage_info) if storage_info else "256 GB SSD"

# 清洗 Screen Size: "15.6 Inch" -> 15.6 (float)
def clean_screen(screen_str):
    try:
        # 嘗試直接轉浮點數
        return float(str(screen_str).split()[0])
    except:
        return 15.6 # 預設值

# 清洗 Price: 確保是乾淨的數字
def clean_price(price):
    try:
        return int(price)
    except:
        return 0

# --- 3. 開始處理 SKU 資料 ---

# 複製一份原始資料來處理
sku_df = raw_df.copy()

# A. 建立暫時的 CleanName 用來跟 Product 表進行 Join
sku_df['TempName'] = sku_df['Name'].apply(clean_product_name)

# B. 關鍵步驟：Merge (Join) 取得 ProductID
# 相當於 SQL: JOIN product_df ON Brand = BrandName AND TempName = ProductName
merged_df = pd.merge(
    sku_df, 
    product_df[['ProductID', 'BrandName', 'ProductName']], 
    left_on=['Brand', 'TempName'], 
    right_on=['BrandName', 'ProductName'],
    how='left'
)

# 檢查一下有沒有對應失敗的 (ProductID 為 NaN)
missing_ids = merged_df['ProductID'].isna().sum()
if missing_ids > 0:
    print(f"警告：有 {missing_ids} 筆資料找不到對應的 ProductID，將會被移除。")
    merged_df = merged_df.dropna(subset=['ProductID'])

# C. 清洗各個欄位
merged_df['RAM'] = merged_df['RAM'].apply(clean_ram)
merged_df['Storage'] = merged_df.apply(clean_storage, axis=1)
merged_df['ScreenSize'] = merged_df['Display'].apply(clean_screen)
merged_df['Price'] = merged_df['Price'].apply(clean_price)

# D. 生成 SKU_ID (PK)
merged_df.insert(0, 'SKU_ID', range(1, 1 + len(merged_df)))

# E. 生成庫存 (Stock) - 隨機生成 1~50 之間的數字
merged_df['Stock'] = np.random.randint(1, 51, size=len(merged_df))

# F. 挑選最終需要的欄位 (對應 Schema)
# SKU(SKU_ID, ProductID, CPU, GPU, Storage, ScreenSize, Weight, Price, Stock, RAM)
final_sku_df = merged_df[[
    'SKU_ID', 
    'ProductID', 
    'Processor_Name', # 對應 CPU
    'GPU', 
    'RAM', 
    'Storage', 
    'ScreenSize', 
    'Price', 
    'Stock'
]].copy()

# 重新命名以符合 Schema
final_sku_df = final_sku_df.rename(columns={
    'Processor_Name': 'CPU'
})

# 補上 Weight (因為 CSV 裡沒有重量，我們給一個平均值或假資料)
# 這裡簡單隨機生成 1.2kg ~ 2.5kg
final_sku_df['Weight'] = np.round(np.random.uniform(1.2, 2.5, size=len(final_sku_df)), 2)

# --- 4. 輸出結果 ---
print("-" * 30)
print("SKU 資料處理完成！預覽前 5 筆：")
print(final_sku_df.head())
print("-" * 30)
print(f"總共生成 {len(final_sku_df)} 筆 SKU 資料。")

output_filename = 'sku_table.csv'
final_sku_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"檔案已儲存為：{output_filename}")