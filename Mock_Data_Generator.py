import pandas as pd
import random
from faker import Faker
import datetime

# --- 設定 ---
# 我們要生成多少資料？
NUM_CUSTOMERS = 50      # 50 位會員
NUM_ORDERS = 200        # 200 張訂單
LOCALE = 'zh_TW'        # 設定為台灣地區 (生成中文姓名地址)

# 初始化 Faker
fake = Faker(LOCALE)

# --- 1. 讀取 SKU ID ---
# 我們需要知道有哪些商品可以買
try:
    sku_df = pd.read_csv('sku_table_v3.csv')
    valid_sku_ids = sku_df['SKU_ID'].tolist()
    print(f"成功讀取 SKU 表，共有 {len(valid_sku_ids)} 種商品可供下單。")
except FileNotFoundError:
    print("錯誤：找不到 sku_table_v3.csv。請先完成上一步。")
    exit()

# --- 2. 生成顧客資料 (Customer) ---
print("正在生成顧客資料...")
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
# 建立一個查表，紀錄每個顧客擁有哪幾個 AddressID (為了後面生成訂單用)
customer_address_map = {} 

payment_methods = ['Credit Card', 'Line Pay', 'Cash on Delivery', 'Apple Pay']

for cust_id in customer_df['CustomerID']:
    # 每個顧客隨機生成 1~3 個地址
    num_addr = random.randint(1, 3)
    customer_addr_ids = []
    
    for _ in range(num_addr):
        addresses.append({
            'AddressID': address_id_counter,
            'CustomerID': cust_id,
            'ReceiverName': fake.name(), # 收件人可能是別人
            'Phone': fake.phone_number(),
            'Address': fake.address(),
            'PaymentMethod': random.choice(payment_methods)
        })
        customer_addr_ids.append(address_id_counter)
        address_id_counter += 1
    
    customer_address_map[cust_id] = customer_addr_ids

address_df = pd.DataFrame(addresses)

# --- 4. 生成訂單 (Order) ---
print("正在生成訂單...")
orders = []
order_items = []
order_item_id_counter = 1

statuses = ['Processing', 'Shipped', 'Delivered', 'Cancelled']

for order_id in range(1, NUM_ORDERS + 1):
    # A. 隨機選一個顧客
    cust_id = random.choice(customer_df['CustomerID'])
    
    # B. *關鍵邏輯*：只能從「該顧客」的地址中選一個
    # 如果隨便亂選地址，會發生「A買東西寄到B家」的邏輯錯誤
    addr_id = random.choice(customer_address_map[cust_id])
    
    # C. 生成時間 (過去一年內)
    order_date = fake.date_time_between(start_date='-1y', end_date='now')
    
    orders.append({
        'Order_ID': order_id,
        'Customer_ID': cust_id,
        'Address_ID': addr_id,
        'OrderDate': order_date,
        'Status': random.choice(statuses)
    })
    
    # --- 5. 生成訂單品項 (OrderItem) ---
    # 每張訂單買 1~4 種商品
    num_items = random.randint(1, 4)
    # 隨機挑選不重複的商品
    selected_skus = random.sample(valid_sku_ids, num_items)
    
    for sku_id in selected_skus:
        order_items.append({
            'OrderItemID': order_item_id_counter,
            'OrderID': order_id,
            'SKUID': sku_id,
            'Quantity': random.randint(1, 3) # 每種買 1~3 個
        })
        order_item_id_counter += 1

order_df = pd.DataFrame(orders)
order_item_df = pd.DataFrame(order_items)

# --- 6. 輸出所有 CSV ---
print("-" * 30)
customer_df.to_csv('customer.csv', index=False, encoding='utf-8-sig')
address_df.to_csv('address_book.csv', index=False, encoding='utf-8-sig')
order_df.to_csv('order.csv', index=False, encoding='utf-8-sig')
order_item_df.to_csv('order_item.csv', index=False, encoding='utf-8-sig')

print(f"成功生成 4 份 CSV 檔案：")
print(f"1. customer.csv ({len(customer_df)} 筆)")
print(f"2. address_book.csv ({len(address_df)} 筆)")
print(f"3. order.csv ({len(order_df)} 筆)")
print(f"4. order_item.csv ({len(order_item_df)} 筆)")
print("-" * 30)