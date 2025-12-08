-- 設定環境
CREATE DATABASE IF NOT EXISTS LaptopStore;
USE LaptopStore;

-- 暫時關閉外鍵檢查，避免 DROP TABLE 時因為順序問題報錯
SET FOREIGN_KEY_CHECKS = 0;

-- 如果表存在就刪除 (重置環境用)
DROP TABLE IF EXISTS OrderItem;
DROP TABLE IF EXISTS `Order`;
DROP TABLE IF EXISTS AddressBook;
DROP TABLE IF EXISTS SKU;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Product;

-- 開啟外鍵檢查
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 第一部分：Master Data (主檔)
-- ==========================================

-- 1. 商品系列 (Product)
CREATE TABLE Product (
    ProductID INT PRIMARY KEY,
    BrandName VARCHAR(50) NOT NULL,
    ProductName VARCHAR(255) NOT NULL,
    Category VARCHAR(50) DEFAULT 'Laptop',
    Status VARCHAR(20) DEFAULT 'Active'
);

-- 2. 規格型號 (SKU)
-- [更新] 新增 VRAM 和 StorageCapacity 以支援 GUI 的規格比較功能
CREATE TABLE SKU (
    SKU_ID VARCHAR(50) PRIMARY KEY, -- 注意：這是真實料號 (String)，不是 INT
    ProductID INT NOT NULL,
    CPU VARCHAR(100),
    GPU VARCHAR(100),
    VRAM INT DEFAULT 0,             -- [新增] 顯卡記憶體 (GB)，用於篩選
    RAM INT NOT NULL,               -- 記憶體 (GB)
    Storage VARCHAR(100),           -- 原始字串 (顯示用)
    StorageCapacity INT NOT NULL,   -- [新增] 總容量 (GB)，用於篩選
    ScreenSize DECIMAL(4, 1),
    Weight DECIMAL(4, 2),
    Price INT NOT NULL,
    Stock INT DEFAULT 0,
    
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

-- 3. 顧客 (Customer)
-- [更新] 新增 RegisterDate 以支援會員中心顯示
CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Phone VARCHAR(20),
    RegisterDate DATETIME DEFAULT CURRENT_TIMESTAMP -- [新增] 註冊日期
);

-- 4. 收件資訊 (AddressBook)
CREATE TABLE AddressBook (
    AddressID INT PRIMARY KEY,
    CustomerID INT NOT NULL,
    ReceiverName VARCHAR(100),
    Phone VARCHAR(20),
    Address VARCHAR(255),
    PaymentMethod VARCHAR(50),      -- 這是顧客的「預設」付款方式
    
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

-- ==========================================
-- 第二部分：Transaction Data (交易資料)
-- ==========================================

-- 5. 訂單 (Order)
-- [更新] 新增 PaymentMethod 以記錄當下交易方式 (Snapshot)
CREATE TABLE `Order` (
    Order_ID INT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Address_ID INT NOT NULL,
    PaymentMethod VARCHAR(50),      -- [新增] 訂單當下的付款方式
    OrderDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20),             -- Processing, Shipped, Delivered...
    
    FOREIGN KEY (Customer_ID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (Address_ID) REFERENCES AddressBook(AddressID)
);

-- 6. 訂單品項 (OrderItem)
CREATE TABLE OrderItem (
    OrderItemID INT PRIMARY KEY,
    OrderID INT NOT NULL,
    SKUID VARCHAR(50) NOT NULL,     -- 對應 SKU 表的 VARCHAR PK
    Quantity INT NOT NULL,
    
    FOREIGN KEY (OrderID) REFERENCES `Order`(Order_ID),
    FOREIGN KEY (SKUID) REFERENCES SKU(SKU_ID)
);

-- 建立索引加速查詢 (針對期末 Demo 的重點功能)
CREATE INDEX idx_sku_specs ON SKU(RAM, StorageCapacity, VRAM); -- 加速規格篩選
CREATE INDEX idx_sku_price ON SKU(Price);                      -- 加速價格區間篩選
CREATE INDEX idx_order_date ON `Order`(OrderDate);             -- 加速銷售報表統計