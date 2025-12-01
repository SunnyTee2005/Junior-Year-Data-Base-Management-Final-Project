import pandas as pd

# 1. 讀取原始資料
# encoding='latin-1' 是為了處理一些特殊符號，若讀取失敗可嘗試
try:
    df = pd.read_csv('laptop.csv')
    print(f"成功讀取原始資料，共 {len(df)} 筆。")
except UnicodeDecodeError:
    df = pd.read_csv('laptop.csv', encoding='latin-1')
    print("使用 latin-1 編碼讀取成功。")

# 2. 定義清理名稱的函式
def clean_product_name(raw_name):
    # 邏輯：找到第一個 '('，只取前面的部分，並移除前後空白
    if '(' in raw_name:
        return raw_name.split('(')[0].strip()
    return raw_name.strip()

# 3. 建立 Product 表格的資料
# 先取出需要的欄位
product_df = df[['Brand', 'Name']].copy()

# 應用清理函式
product_df['ProductName'] = product_df['Name'].apply(clean_product_name)

# 移除原始的 Name 欄位，我們不需要了
product_df = product_df.drop(columns=['Name'])

# 重新命名 Brand 為 BrandName (對應你們的 Schema)
product_df = product_df.rename(columns={'Brand': 'BrandName'})

# 4. 去除重複 (De-duplicate)
# 因為原始資料可能是 "Flat Table"，同一個商品系列可能有不同規格的多筆資料
# 我們只保留 "BrandName" 和 "ProductName" 都相同的第一筆
product_df = product_df.drop_duplicates(subset=['BrandName', 'ProductName'])

# 5. 生成 ProductID (Surrogate Key)
# 從 1 開始編號
product_df.insert(0, 'ProductID', range(1, 1 + len(product_df)))

# 6. 補上其他固定欄位
# 根據你們的 Schema，還有 Category 和 Status
product_df['Category'] = 'Laptop'
product_df['Status'] = 'Active'

# 7. 檢查結果
print("-" * 30)
print("處理完成！預覽前 5 筆 Product 資料：")
print(product_df.head())
print("-" * 30)
print(f"總共生成 {len(product_df)} 筆唯一的商品資料。")

# 8. 輸出成 CSV
output_filename = 'product_table.csv'
product_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
print(f"檔案已儲存為：{output_filename}")

# 小撇步：這份 product_table.csv 可以直接用 Excel 打開檢查，
# 或者之後寫 SQL 時用 LOAD DATA INFILE 匯入。