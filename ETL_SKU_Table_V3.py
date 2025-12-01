import pandas as pd
import numpy as np
import re
import random
import string

# --- 1. 讀取資料 ---
try:
    # 假設 product_table.csv 已經存在
    raw_df = pd.read_csv('laptop.csv', encoding='latin-1')
    product_df = pd.read_csv('product_table.csv') 
    print(f"資料讀取成功。處理筆數: {len(raw_df)}")
except FileNotFoundError:
    print("找不到檔案，請確認 laptop.csv 與 product_table.csv 都在目錄下。")
    exit()

# --- 2. 真實重量查找表 (Real-World Weight Lookup) ---
# 這是針對知名系列的「寫死」數據，讓資料看起來超真實
REAL_WEIGHT_MAP = {
    'MACBOOK AIR': 1.29,
    'MACBOOK PRO': 1.60, # 14 inch avg
    'LG GRAM': 0.99,     # 以輕薄聞名
    'DELL XPS': 1.27,
    'THINKPAD X1': 1.13,
    'ZENBOOK': 1.10,
    'SWIFT 5': 1.05,
    'ALIENWARE': 2.50,   # 知名重型機
    'ROG STRIX': 2.30,
    'LEGION 5': 2.40,
    'NITRO 5': 2.30,
    'TUF GAMING': 2.30,
    'IDEAPAD SLIM 3': 1.65,
    'VIVOBOOK 15': 1.70,
    'HP 15S': 1.69
}

# --- 3. 欄位清洗函式 ---

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

# --- SKU ID 提取 (真實料號優先) ---
def extract_real_sku_id(row):
    raw_name = str(row['Name'])
    brand = str(row['Brand']).upper()[:3]
    
    # 策略 1: 抓取括號內的料號 (如 82KU017KIN)
    match = re.search(r'\(([\w\d\-]+)\)', raw_name)
    if match:
        candidate = match.group(1)
        # 過濾雜訊：長度>4 且 含數字 且 不是純規格描述
        if len(candidate) > 4 and any(c.isdigit() for c in candidate) and "Inch" not in candidate:
            return candidate.upper()
    
    # 策略 2: 如果抓不到，生成 "品牌-隨機碼" (如 HP-X92Z)
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{brand}-{suffix}"

# --- 混合式重量計算 (查找表 + 物理估算) ---
def get_hybrid_weight(row):
    name_upper = str(row['Name']).upper()
    
    # 1. 優先查表 (Lookup)
    for key, weight in REAL_WEIGHT_MAP.items():
        if key in name_upper:
            # 加上一點點隨機擾動 (+- 0.05kg) 讓每台不要完全一樣
            noise = np.random.uniform(-0.05, 0.05)
            return round(weight + noise, 2)
            
    # 2. 查不到則使用智慧估算 (Fallback)
    screen = float(row['ScreenSize'])
    gpu = str(row['GPU']).upper()
    is_gaming = 'RTX' in gpu or 'GTX' in gpu or 'DEDICATED' in gpu
    
    if screen < 12.0:
        base_min, base_max = 1.05, 1.30
    elif 12.0 <= screen < 14.0:
        base_min, base_max = 1.15, 1.45
    elif 14.0 <= screen < 15.0:
        base_min, base_max = 1.30, 1.65
    elif 15.0 <= screen < 16.0:
        base_min, base_max = 1.60, 1.95
    else:
        base_min, base_max = 2.00, 2.50
        
    if is_gaming:
        base_min += 0.4
        base_max += 0.8
        
    return round(np.random.uniform(base_min, base_max), 2)

# --- 4. 執行 ETL ---

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
merged_df = merged_df.dropna(subset=['ProductID'])

# B. 清洗與生成
merged_df['RAM'] = merged_df['RAM'].apply(clean_ram)
merged_df['Storage'] = merged_df.apply(clean_storage, axis=1)
merged_df['ScreenSize'] = merged_df['Display'].apply(clean_screen)
merged_df['Price'] = merged_df['Price'].apply(clean_price)
merged_df['Weight'] = merged_df.apply(get_hybrid_weight, axis=1) # 套用混合式重量
merged_df['SKU_ID'] = merged_df.apply(extract_real_sku_id, axis=1) # 套用真實料號

# C. 處理 SKU_ID 重複 (加後綴)
merged_df['SKU_ID_Count'] = merged_df.groupby('SKU_ID').cumcount() + 1
merged_df['SKU_ID'] = merged_df.apply(
    lambda x: f"{x['SKU_ID']}-V{x['SKU_ID_Count']}" if x['SKU_ID_Count'] > 1 else x['SKU_ID'], 
    axis=1
)

# D. 庫存
merged_df['Stock'] = np.random.randint(1, 51, size=len(merged_df))

# E. 輸出
final_sku_df = merged_df[[
    'SKU_ID', 'ProductID', 'Processor_Name', 'GPU', 'RAM', 
    'Storage', 'ScreenSize', 'Weight', 'Price', 'Stock'
]].rename(columns={'Processor_Name': 'CPU'})

output_filename = 'sku_table_v3.csv'
final_sku_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print("-" * 30)
print(f"處理完成！檔案已存為 {output_filename}")
print("前 5 筆預覽：")
print(final_sku_df[['SKU_ID', 'Weight', 'Price']].head())