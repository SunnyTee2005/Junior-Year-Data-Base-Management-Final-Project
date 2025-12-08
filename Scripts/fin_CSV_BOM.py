import pandas as pd

try:
    # 1. 讀取原始檔案 (使用 utf-8-sig 來正確處理並吃掉原本的 BOM)
    print("正在讀取 product_table.csv...")
    df = pd.read_csv('product_table.csv', encoding='utf-8-sig')
    
    # 2. 存成新檔案 (使用 utf-8，這樣就不會帶 BOM 了)
    output_filename = 'product_table_clean.csv'
    print(f"正在移除 BOM 並儲存為 {output_filename}...")
    df.to_csv(output_filename, index=False, encoding='utf-8')
    
    print("-" * 30)
    print("成功！BOM 已移除。")
    print(f"請使用 MySQL Workbench 匯入新產生的 '{output_filename}'")
    print("-" * 30)
    
except FileNotFoundError:
    print("錯誤：找不到 product_table.csv，請確認檔案位置。")
except Exception as e:
    print(f"發生其他錯誤：{e}")