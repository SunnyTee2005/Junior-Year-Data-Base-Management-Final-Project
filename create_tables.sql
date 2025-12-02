-- 1. 建立資料庫
CREATE DATABASE IF NOT EXISTS LaptopStore;
USE LaptopStore;

-- ==========================================
-- 第一部分：Master Data (主檔)
-- ==========================================

-- 1. 商品系列 (Product) - 最上層父表
CREATE TABLE Product (
    ProductID INT PRIMARY KEY,
    BrandName VARCHAR(50) NOT NULL,
    ProductName VARCHAR(255) NOT NULL,
    Category VARCHAR(50) DEFAULT 'Laptop',
    Status VARCHAR(20) DEFAULT 'Active'
);

-- 2. 規格型號 (SKU) - 依賴 Product
CREATE TABLE SKU (
    SKU_ID VARCHAR(50) PRIMARY KEY, -- 使用真實料號 (String PK)
    ProductID INT NOT NULL,
    CPU VARCHAR(100),
    GPU VARCHAR(100),
    RAM INT NOT NULL,               -- 存整數 (GB)
    Storage VARCHAR(100),
    ScreenSize DECIMAL(4, 1),       -- 例如 15.6
    Weight DECIMAL(4, 2),           -- 例如 1.45
    Price INT NOT NULL,
    Stock INT DEFAULT 0,
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

-- 3. 顧客 (Customer) - 獨立父表
CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Phone VARCHAR(20)
);

-- 4. 收件資訊 (AddressBook) - 依賴 Customer
CREATE TABLE AddressBook (
    AddressID INT PRIMARY KEY,
    CustomerID INT NOT NULL,
    ReceiverName VARCHAR(100),
    Phone VARCHAR(20),
    Address VARCHAR(255),
    PaymentMethod VARCHAR(50),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

-- ==========================================
-- 第二部分：Transaction Data (交易資料)
-- ==========================================

-- 5. 訂單 (Order) - 依賴 Customer 和 AddressBook
CREATE TABLE `Order` (
    Order_ID INT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Address_ID INT NOT NULL,
    OrderDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20),
    
    FOREIGN KEY (Customer_ID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (Address_ID) REFERENCES AddressBook(AddressID)
);

-- 6. 訂單品項 (OrderItem) - 依賴 Order 和 SKU
CREATE TABLE OrderItem (
    OrderItemID INT PRIMARY KEY,
    OrderID INT NOT NULL,
    SKUID VARCHAR(50) NOT NULL,
    Quantity INT NOT NULL,
    
    FOREIGN KEY (OrderID) REFERENCES `Order`(Order_ID),
    FOREIGN KEY (SKUID) REFERENCES SKU(SKU_ID)
);

-- 建立一些索引以加速查詢 (Optional but Good for Project)
CREATE INDEX idx_sku_price ON SKU(Price);
CREATE INDEX idx_order_date ON `Order`(OrderDate);