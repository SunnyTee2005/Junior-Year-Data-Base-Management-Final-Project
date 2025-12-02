import pandas as pd
import random
from faker import Faker
import numpy as np

# --- 參數設定 (Scale Up) ---
# 為了符合 4000 筆 SKU 的庫存規模，我們需要擴大交易資料
NUM_CUSTOMERS = 1000    # 從 50 改為 1000
NUM_ORDERS = 5000       # 從 200 改為 5000 (確保數據密度)
LOCALE = 'zh_TW'

fake = Faker(LOCALE)

# --- 1. 讀取 SKU ID ---
try:
    sku_df = pd.read_csv('sku_table_v3.csv')
    valid_sku_ids = sku_df['SKU_ID'].tolist()
    
    # [新增邏輯] 模擬 "熱銷商品"
    # 我們隨機選出 10% 的商品當作 "熱門款"，讓它們被選到的機率高 5 倍
    # 這樣你的 "銷售排行" 報表才會有高低起伏，不會大家都只賣 1 台
    hot_items = random.sample(valid_sku_ids, k=int(len(valid_sku_ids) * 0.1))
    
    print(f"成功讀取 SKU 表，共有 {len(valid_sku_ids)} 種商品。")
    print(f"已標記 {len(hot_items)} 種熱銷商品 (權重加倍)。")
    
except FileNotFoundError:
    print("錯誤：找不到 sku_table_v3.csv。")
    exit()

# --- 2. 生成顧客資料 (Customer) ---
print(f"正在生成 {NUM_CUSTOMERS} 位顧客資料...")
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        'CustomerID': i,
        'Email': fake.email(),
        'Password': fake.password(length=10),
        'Name': fake.name(),
        'Phone': fake.phone_number()
    })
customer_df = pd.DataFrame(customers)

# --- 3. 生成地址簿 (AddressBook) ---
print("正在生成地址資料...")
addresses = []
address_id_counter = 1
customer_address_map = {} 

payment_methods = ['Credit Card', 'Line Pay', 'Cash on Delivery', 'Apple Pay']

for cust_id in customer_df['CustomerID']:
    # 每個顧客隨機生成 1~2 個地址 (減少無效地址)
    num_addr = random.choices([1, 2], weights=[0.8, 0.2])[0]
    customer_addr_ids = []
    
    for _ in range(num_addr):
        addresses.append({
            'AddressID': address_id_counter,
            'CustomerID': cust_id,
            'ReceiverName': fake.name(),
            'Phone': fake.phone_number(),
            'Address': fake.address(),
            'PaymentMethod': random.choice(payment_methods)
        })
        customer_addr_ids.append(address_id_counter)
        address_id_counter += 1
    
    customer_address_map[cust_id] = customer_addr_ids

address_df = pd.DataFrame(addresses)

# --- 4. 生成訂單 (Order) ---
print(f"正在生成 {NUM_ORDERS} 筆訂單 (這可能需要幾秒鐘)...")
orders = []
order_items = []
order_item_id_counter = 1

statuses = ['Processing', 'Shipped', 'Delivered', 'Cancelled']
status_weights = [0.1, 0.2, 0.6, 0.1] # 大部分訂單應該是 Delivered

# 為了加速，預先準備好熱門與一般商品的權重池
# 一般商品權重 1，熱門商品權重 10
sku_weights = [10 if sku in hot_items else 1 for sku in valid_sku_ids]
# 轉為 numpy array 加速抽樣
sku_array = np.array(valid_sku_ids)
sku_probs = np.array(sku_weights) / sum(sku_weights)

for order_id in range(1, NUM_ORDERS + 1):
    cust_id = random.choice(customer_df['CustomerID'])
    addr_id = random.choice(customer_address_map[cust_id])
    
    # 時間分佈優化：讓訂單集中在最近，比較真實
    order_date = fake.date_time_between(start_date='-6m', end_date='now')
    
    orders.append({
        'Order_ID': order_id,
        'Customer_ID': cust_id,
        'Address_ID': addr_id,
        'OrderDate': order_date,
        'Status': random.choices(statuses, weights=status_weights)[0]
    })
    
    # --- 5. 生成訂單品項 (OrderItem) ---
    # 平均每單買 1.5 個品項
    num_items = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
    
    # 使用 Numpy 加權隨機抽樣 (比 Python random.sample 快且支援權重)
    selected_skus = np.random.choice(sku_array, size=num_items, replace=False, p=sku_probs)
    
    for sku_id in selected_skus:
        order_items.append({
            'OrderItemID': order_item_id_counter,
            'OrderID': order_id,
            'SKUID': sku_id,
            'Quantity': random.choices([1, 2], weights=[0.9, 0.1])[0] # 筆電通常只買一台
        })
        order_item_id_counter += 1

order_df = pd.DataFrame(orders)
order_item_df = pd.DataFrame(order_items)

# --- 6. 輸出 ---
print("-" * 30)
customer_df.to_csv('customer.csv', index=False, encoding='utf-8-sig')
address_df.to_csv('address_book.csv', index=False, encoding='utf-8-sig')
order_df.to_csv('order.csv', index=False, encoding='utf-8-sig')
order_item_df.to_csv('order_item.csv', index=False, encoding='utf-8-sig')

print(f"生成完畢！數據統計：")
print(f"Customer:   {len(customer_df)} 筆")
print(f"Address:    {len(address_df)} 筆")
print(f"Order:      {len(order_df)} 筆")
print(f"OrderItem:  {len(order_item_df)} 筆 (資料庫主表)")
print("-" * 30)