import pandas as pd
import numpy as np
import re
import random
import string
import os

# --- 1. 讀取資料 ---
try:
    # 調整路徑以符合專案結構 (假設從專案根目錄執行)
    if os.path.exists('laptop.csv'):
        raw_df = pd.read_csv('laptop.csv', encoding='latin-1')
    else:
        # Fallback if inside Scripts dir
        raw_df = pd.read_csv('../laptop.csv', encoding='latin-1')

    if os.path.exists('Ready_to_Use_Data/product_table.csv'):
        product_df = pd.read_csv('Ready_to_Use_Data/product_table.csv')
    elif os.path.exists('../Ready_to_Use_Data/product_table.csv'):
        product_df = pd.read_csv('../Ready_to_Use_Data/product_table.csv')
    else:
        # Fallback for flat directory structure
        product_df = pd.read_csv('product_table.csv')
        
    print(f"資料讀取成功。處理筆數: {len(raw_df)}")
except FileNotFoundError:
    print("找不到檔案，請確認 laptop.csv 與 product_table.csv 的位置。")
    exit()

# --- 2. 真實重量查找表 (Real-World Weight Lookup) ---
REAL_WEIGHT_MAP = {
    'MACBOOK AIR': 1.29,
    'MACBOOK PRO': 1.60,
    'LG GRAM': 0.99,
    'DELL XPS': 1.27,
    'THINKPAD X1': 1.13,
    'ZENBOOK': 1.10,
    'SWIFT 5': 1.05,
    'ALIENWARE': 2.50,
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

# --- 新增功能: 解析 VRAM ---
def extract_vram(gpu_str):
    """
    從 GPU 字串解析 VRAM 大小 (GB)。
    邏輯: 抓取 'GB' 前的數字。若為內顯或找不到，回傳 0。
    """
    s = str(gpu_str).strip()
    # 排除內顯 (可視情況調整關鍵字)
    if "Intel" in s or "Iris" in s or "UHD" in s or "Shared" in s:
        # 簡單判斷：如果是純Intel Integrated GPU通常沒有獨顯記憶體
        # 但有些描述可能有寫 shared memory，這裡依需求設為 0
        pass
    
    # 抓取數字 + GB
    match = re.search(r'(\d+)\s*GB', s, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0

# --- 新增功能: 解析 StorageCapacity ---
def parse_storage_capacity(size_str):
    """
    輔助函式: 將 '1 TB', '512 GB' 轉為 GB 整數
    """
    s = str(size_str).upper()
    if 'TB' in s:
        digits = re.findall(r'(\d+)', s)
        if digits:
            return int(digits[0]) * 1024
    elif 'GB' in s:
        digits = re.findall(r'(\d+)', s)
        if digits:
            return int(digits[0])
    return 0

def calculate_total_storage(row):
    """
    計算總容量 (GB)。來源: SSD + HDD
    """
    ssd_str = str(row['SSD'])
    hdd_str = str(row['HDD'])
    
    total = 0
    
    # 處理 SSD
    if 'No' not in ssd_str and ssd_str != 'nan':
        total += parse_storage_capacity(ssd_str)
        
    # 處理 HDD
    if 'No' not in hdd_str and hdd_str != 'nan':
        total += parse_storage_capacity(hdd_str)
        
    # 防呆: 如果都沒抓到，預設給 256 (配合 clean_storage 的預設值)
    if total == 0:
        return 256
        
    return total

# --- SKU ID 提取 (真實料號優先) ---
def extract_real_sku_id(row):
    raw_name = str(row['Name'])
    brand = str(row['Brand']).upper()[:3]
    
    # 策略 1: 抓取括號內的料號 (如 82KU017KIN)
    match = re.search(r'\(([\w\d\-]+)\)', raw_name)
    if match:
        candidate = match.group(1)
        if len(candidate) > 4 and any(c.isdigit() for c in candidate) and "Inch" not in candidate:
            return candidate.upper()
    
    # 策略 2: 生成 "品牌-隨機碼"
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{brand}-{suffix}"

# --- 混合式重量計算 ---
def get_hybrid_weight(row):
    name_upper = str(row['Name']).upper()
    
    for key, weight in REAL_WEIGHT_MAP.items():
        if key in name_upper:
            noise = np.random.uniform(-0.05, 0.05)
            return round(weight + noise, 2)
            
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
merged_df['Weight'] = merged_df.apply(get_hybrid_weight, axis=1)
merged_df['SKU_ID'] = merged_df.apply(extract_real_sku_id, axis=1)

# --- 新增欄位 ---
merged_df['VRAM'] = merged_df['GPU'].apply(extract_vram)
merged_df['StorageCapacity'] = merged_df.apply(calculate_total_storage, axis=1)

# C. 處理 SKU_ID 重複
merged_df['SKU_ID_Count'] = merged_df.groupby('SKU_ID').cumcount() + 1
merged_df['SKU_ID'] = merged_df.apply(
    lambda x: f"{x['SKU_ID']}-V{x['SKU_ID_Count']}" if x['SKU_ID_Count'] > 1 else x['SKU_ID'], 
    axis=1
)

# D. 庫存
merged_df['Stock'] = np.random.randint(1, 51, size=len(merged_df))

# E. 輸出
output_columns = [
    'SKU_ID', 'ProductID', 'Processor_Name', 'GPU', 'VRAM', # Added VRAM
    'RAM', 'Storage', 'StorageCapacity',                    # Added StorageCapacity
    'ScreenSize', 'Weight', 'Price', 'Stock'
]

final_sku_df = merged_df[output_columns].rename(columns={'Processor_Name': 'CPU'})

output_filename = 'sku_table_v5.csv'
final_sku_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print("-" * 30)
print(f"處理完成！檔案已存為 {output_filename}")
print("前 5 筆預覽：")
print(final_sku_df[['SKU_ID', 'VRAM', 'StorageCapacity', 'Storage']].head())
