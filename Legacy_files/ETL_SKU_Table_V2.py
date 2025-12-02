import pandas as pd
import numpy as np
import re
import random
import string

# --- 1. 讀取資料 ---
try:
    # 讀取原始資料與 Product 表
    # 注意：這裡假設你已經有上一步生成的 product_table.csv
    raw_df = pd.read_csv('laptop.csv', encoding='latin-1')
    product_df = pd.read_csv('product_table.csv') 
    print(f"成功讀取資料。原始筆數: {len(raw_df)}")
except FileNotFoundError:
    print("錯誤：找不到檔案。請確認 laptop.csv 和 product_table.csv 都在同一個資料夾。")
    exit()

# --- 2. 定義清洗與生成函式 ---

def clean_product_name(raw_name):
    if '(' in str(raw_name):
        return str(raw_name).split('(')[0].strip()
    return str(raw_name).strip()

def clean_ram(ram_str):
    if pd.isna(ram_str): return 8
    digits = re.findall(r'\d+', str(ram_str))
    return int(digits[0]) if digits else 8

def clean_storage(row):
    ssd = str(row['SSD']).strip()
    hdd = str(row['HDD']).strip()
    storage_info = []
    if 'No' not in ssd and ssd != 'nan': storage_info.append(ssd)
    if 'No' not in hdd and hdd != 'nan': storage_info.append(hdd)
    return " + ".join(storage_info) if storage_info else "256 GB SSD"

def clean_screen(screen_str):
    try:
        return float(str(screen_str).split()[0])
    except:
        return 15.6

def clean_price(price):
    try:
        return int(price)
    except:
        return 0

# --- [新功能] SKU ID 提取器 ---
def extract_sku_string(row):
    raw_name = str(row['Name'])
    brand = str(row['Brand']).upper()[:3] # 取品牌前三字
    
    # 1. 嘗試抓取括號內的料號 (例如: 82KU017KIN)
    # Regex 邏輯：找括號，且括號內包含數字 (避免抓到 "(Black)")
    match = re.search(r'\(([\w\d\-]+)\)', raw_name)
    
    if match:
        candidate = match.group(1)
        # 過濾掉太短或純英文的描述 (如 "Laptop", "Core i5")
        if len(candidate) > 4 and any(c.isdigit() for c in candidate):
            return candidate.upper()
            
    # 2. 如果抓不到，生成一個擬真的 SKU (例如: HP-RAND-491)
    # 這比純數字 1, 2, 3 真實多了
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{brand}-{random_suffix}"

# --- [新功能] 智慧重量估算 (Heuristic Weight Estimation) ---
def get_smart_weight(row):
    screen = float(row['ScreenSize'])
    gpu = str(row['GPU']).upper()
    
    # 判斷是否為電競筆電 (Gaming Laptops are heavier)
    is_gaming = 'RTX' in gpu or 'GTX' in gpu or 'DEDICATED' in gpu
    
    # 基礎重量範圍 (Base Range based on Physics)
    if screen < 12.0:
        base_min, base_max = 1.05, 1.30 # 小筆電/平板
    elif 12.0 <= screen < 14.0:
        base_min, base_max = 1.15, 1.45 # Ultrabook (13吋)
    elif 14.0 <= screen < 15.0:
        base_min, base_max = 1.30, 1.65 # 14吋商務機
    elif 15.0 <= screen < 16.0:
        base_min, base_max = 1.60, 1.95 # 15.6吋標準機
    elif 16.0 <= screen < 17.0:
        base_min, base_max = 1.80, 2.30 # 16吋
    else: # >= 17.0
        base_min, base_max = 2.40, 3.20 # 巨無霸
        
    # 電競筆電懲罰 (加上散熱模組重量)
    if is_gaming:
        # 電競筆電通常比同尺寸文書機重 0.4 ~ 0.8 kg
        base_min += 0.4
        base_max += 0.8
        
    # 產生並取小數點後兩位
    return round(np.random.uniform(base_min, base_max), 2)

# --- 3. 開始處理資料 ---

sku_df = raw_df.copy()

# A. 連結 ProductID
sku_df['TempName'] = sku_df['Name'].apply(clean_product_name)
merged_df = pd.merge(
    sku_df, 
    product_df[['ProductID', 'BrandName', 'ProductName']], 
    left_on=['Brand', 'TempName'], 
    right_on=['BrandName', 'ProductName'],
    how='left'
)
merged_df = merged_df.dropna(subset=['ProductID']) # 移除對不到的

# B. 應用清洗邏輯
merged_df['RAM'] = merged_df['RAM'].apply(clean_ram)
merged_df['Storage'] = merged_df.apply(clean_storage, axis=1)
merged_df['ScreenSize'] = merged_df['Display'].apply(clean_screen)
merged_df['Price'] = merged_df['Price'].apply(clean_price)
merged_df['Weight'] = merged_df.apply(get_smart_weight, axis=1) # 套用智慧重量

# C. 生成擬真 SKU ID (字串)
merged_df['SKU_ID'] = merged_df.apply(extract_sku_string, axis=1)

# *重要*：檢查 SKU_ID 是否有重複？
# 真實世界可能有兩筆資料是同一台電腦但不同價格，這會導致 ID 重複 (Primary Key Error)
# 我們簡單處理：如果有重複，就在後面加個 "-V2", "-V3"
merged_df['SKU_ID_Count'] = merged_df.groupby('SKU_ID').cumcount() + 1
merged_df['SKU_ID'] = merged_df.apply(
    lambda x: f"{x['SKU_ID']}-V{x['SKU_ID_Count']}" if x['SKU_ID_Count'] > 1 else x['SKU_ID'], 
    axis=1
)

# D. 生成庫存
merged_df['Stock'] = np.random.randint(1, 51, size=len(merged_df))

# E. 選取最終欄位
final_sku_df = merged_df[[
    'SKU_ID', 
    'ProductID', 
    'Processor_Name', 
    'GPU', 
    'RAM', 
    'Storage', 
    'ScreenSize', 
    'Weight', 
    'Price', 
    'Stock'
]].rename(columns={'Processor_Name': 'CPU'})

# --- 4. 輸出 ---
print("-" * 30)
print("SKU 資料 (V2) 處理完成！")
print("前 5 筆預覽 (注意看 SKU_ID 和 Weight)：")
print(final_sku_df.head())
print("-" * 30)

output_filename = 'sku_table_v2.csv'
final_sku_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"檔案已儲存為：{output_filename}")