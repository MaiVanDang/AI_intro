-- Tạo kiểu ENUM cho các trạng thái
CREATE TYPE discount_type AS ENUM ('percentage', 'fixed_amount');
CREATE TYPE promotion_status AS ENUM ('active', 'inactive', 'expired');
CREATE TYPE payment_status AS ENUM ('paid', 'unpaid', 'pending');

-- Tạo bảng Brand
CREATE TABLE Brand (
    Brand_ID SERIAL PRIMARY KEY,
    Brand_Name VARCHAR(255) NOT NULL,
    Description TEXT,
    Logo_URL VARCHAR(500),
    Origin_Country VARCHAR(100)
);

-- Tạo bảng Product_Category
CREATE TABLE Product_Category (
    Category_ID SERIAL PRIMARY KEY,
    Parent_Category_ID INT,
    Category_Name VARCHAR(255) NOT NULL,
    Description TEXT,
    FOREIGN KEY (Parent_Category_ID) REFERENCES Product_Category(Category_ID)
);

-- Tạo bảng Customer
CREATE TABLE Customer (
    Customer_ID SERIAL PRIMARY KEY,
    Email VARCHAR(255) UNIQUE,
    Phone VARCHAR(20),
    Name VARCHAR(255),
    Address TEXT
);

-- Tạo bảng Payment_Method
CREATE TABLE Payment_Method (
    Payment_Method_ID SERIAL PRIMARY KEY,
    Method_Name VARCHAR(100),
    Description TEXT
);

-- Tạo bảng Shipping_Method
CREATE TABLE Shipping_Method (
    Shipping_Method_ID SERIAL PRIMARY KEY,
    Method_Name VARCHAR(100),
    Description TEXT,
    Cost_per_product DECIMAL(10,2),
    average_delivery_time_per_km DECIMAL(5,2)
);

-- Tạo bảng Shipping_Address
CREATE TABLE Shipping_Address (
    Address_ID SERIAL PRIMARY KEY,
    Customer_ID INT,
    Receiver_Name VARCHAR(255),
    Receiver_Phone VARCHAR(20),
    Country VARCHAR(100),
    City VARCHAR(100),
    Province_State VARCHAR(100),
    Postal_Code VARCHAR(20),
    Is_Default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
);

-- Tạo bảng Promotion
CREATE TABLE Promotion (
    Promotion_ID SERIAL PRIMARY KEY,
    Description TEXT,
    Discount_Type discount_type,
    Discount_Value DECIMAL(10,2),
    Start_Date DATE,
    End_Date DATE,
    Coupon_Code VARCHAR(50),
    Minimum_Order DECIMAL(10,2),
    Status promotion_status
);

-- Tạo bảng Product
CREATE TABLE Product (
    Product_ID SERIAL PRIMARY KEY,
    Product_Name VARCHAR(255) NOT NULL,
    Category_ID INT,
    Brand_ID INT,
    Description TEXT,
    Price DECIMAL(10,2),
    Stock_Quantity INT,
    Image_URLs TEXT,
    Specifications TEXT,
    Created_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Category_ID) REFERENCES Product_Category(Category_ID),
    FOREIGN KEY (Brand_ID) REFERENCES Brand(Brand_ID)
);

-- Tạo bảng Order
CREATE TABLE "Order" (
    Order_ID SERIAL PRIMARY KEY,
    Customer_ID INT,
    Payment_Method_ID INT,
    Shipping_Method_ID INT,
    Shipping_Address_ID INT,
    Promotion_ID INT,
    Order_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Total_Amount DECIMAL(12,2),
    Shipping_Fee DECIMAL(10,2),
    Discount DECIMAL(10,2),
    Payment_Status payment_status,
    Order_Status VARCHAR(100),
    Estimated_Delivery_Date DATE,
    Note TEXT,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID),
    FOREIGN KEY (Payment_Method_ID) REFERENCES Payment_Method(Payment_Method_ID),
    FOREIGN KEY (Shipping_Method_ID) REFERENCES Shipping_Method(Shipping_Method_ID),
    FOREIGN KEY (Shipping_Address_ID) REFERENCES Shipping_Address(Address_ID),
    FOREIGN KEY (Promotion_ID) REFERENCES Promotion(Promotion_ID)
);

-- Tạo bảng Order_Item
CREATE TABLE Order_Item (
    Order_ID INT,
    Product_ID INT,
    Quantity INT,
    PRIMARY KEY (Order_ID, Product_ID),
    FOREIGN KEY (Order_ID) REFERENCES "Order"(Order_ID),
    FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID)
);

-- Tạo bảng Review
CREATE TABLE Review (
    Review_ID SERIAL PRIMARY KEY,
    Product_ID INT,
    Customer_ID INT,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment TEXT,
    Review_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Images TEXT,
    FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID),
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
);



-- Brand: 10 popular sportswear brands
INSERT INTO Brand (Brand_ID, Brand_Name, Description, Logo_URL, Origin_Country) VALUES
(1, 'Nike', 'Leading sportswear and sneaker brand', 'https://example.com/logo_nike.png', 'USA'),
(2, 'Adidas', 'Global sportswear and athletic gear manufacturer', 'https://example.com/logo_adidas.png', 'Germany'),
(3, 'Puma', 'Athletic footwear and casual apparel', 'https://example.com/logo_puma.png', 'Germany'),
(4, 'Under Armour', 'Performance apparel and athletic gear', 'https://example.com/logo_ua.png', 'USA'),
(5, 'Asics', 'High-quality running shoes and sportswear', 'https://example.com/logo_asics.png', 'Japan'),
(6, 'New Balance', 'Athletic footwear with focus on comfort', 'https://example.com/logo_nb.png', 'USA'),
(7, 'Converse', 'Iconic sneakers and casual footwear', 'https://example.com/logo_converse.png', 'USA'),
(8, 'Fila', 'Stylish sportswear and footwear', 'https://example.com/logo_fila.png', 'South Korea'),
(9, 'Skechers', 'Comfort-focused footwear and sneakers', 'https://example.com/logo_skechers.png', 'USA'),
(10, 'Vans', 'Skateboarding shoes and streetwear', 'https://example.com/logo_vans.png', 'USA');

-- Product_Category: Unchanged, as it aligns with requirements
INSERT INTO Product_Category (Category_ID, Parent_Category_ID, Category_Name, Description) VALUES
(1, NULL, 'Footwear', 'All types of shoes and sandals'),
(2, NULL, 'Apparel', 'Clothing items for sports and casual wear'),
(3, NULL, 'Accessories', 'Fashion and sports accessories'),
(4, NULL, 'Equipment', 'Sports equipment and gear'),
(5, NULL, 'Bags', 'Bags for sports, travel, and daily use'),
(6, 1, 'Running Shoes', 'Shoes designed for running'),
(7, 1, 'Sneakers', 'Casual and lifestyle sneakers'),
(8, 1, 'Sandals', 'Open-toe footwear'),
(9, 1, 'Cleats', 'Shoes with spikes for soccer, baseball, etc.'),
(10, 2, 'T-Shirts', 'Casual and athletic t-shirts'),
(11, 2, 'Shorts', 'Sports and casual shorts'),
(12, 2, 'Jackets', 'Jackets and windbreakers'),
(13, 2, 'Compression Wear', 'Compression shirts, leggings, etc.'),
(14, 3, 'Hats', 'Caps and hats for sports and fashion'),
(15, 3, 'Socks', 'Athletic and casual socks'),
(16, 3, 'Wristbands', 'Sweatbands and wrist accessories'),
(17, 5, 'Backpacks', 'Backpacks for sports or school'),
(18, 5, 'Duffel Bags', 'Large bags for gym or travel'),
(19, 5, 'Waist Packs', 'Compact waist bags for carrying essentials');

-- Customer: Unchanged, as it aligns with requirements
INSERT INTO Customer (Customer_ID, Email, Phone, Name, Address) VALUES
(1, 'john.doe@example.com', '1234567890', 'John Doe', '123 Main St, New York, NY'),
(2, 'jane.smith@example.com', '0987654321', 'Jane Smith', '456 Elm St, Los Angeles, CA'),
(3, 'alice.nguyen@example.com', '0912345678', 'Alice Nguyen', '789 Oak St, Chicago, IL'),
(4, 'bob.tanaka@example.com', '0801234567', 'Bob Tanaka', '321 Pine St, Tokyo, Japan'),
(5, 'emma.wang@example.com', '0709876543', 'Emma Wang', '654 Maple St, Beijing, China'),
(6, 'lucas.martin@example.com', '0612345678', 'Lucas Martin', '987 Birch St, Paris, France'),
(7, 'sofia.lee@example.com', '0501122334', 'Sofia Lee', '147 Cedar St, Seoul, South Korea'),
(8, 'liam.kim@example.com', '0402233445', 'Liam Kim', '258 Walnut St, Busan, South Korea'),
(9, 'olivia.chen@example.com', '0303344556', 'Olivia Chen', '369 Chestnut St, Taipei, Taiwan'),
(10, 'noah.tran@example.com', '0204455667', 'Noah Tran', '741 Spruce St, Hanoi, Vietnam'),
(11, 'ava.saito@example.com', '0905566778', 'Ava Saito', '852 Willow St, Osaka, Japan'),
(12, 'mason.kawasaki@example.com', '0816677889', 'Mason Kawasaki', '963 Poplar St, Kyoto, Japan'),
(13, 'mia.hoang@example.com', '0827788990', 'Mia Hoang', '159 Aspen St, Ho Chi Minh City, Vietnam'),
(14, 'ethan.yamada@example.com', '0838899001', 'Ethan Yamada', '753 Fir St, Sapporo, Japan'),
(15, 'isabella.takahashi@example.com', '0849900112', 'Isabella Takahashi', '456 Redwood St, Nagoya, Japan'),
(16, 'logan.pham@example.com', '0851011121', 'Logan Pham', '654 Sycamore St, Da Nang, Vietnam'),
(17, 'amelia.nakamura@example.com', '0862122232', 'Amelia Nakamura', '987 Palm St, Fukuoka, Japan'),
(18, 'james.vo@example.com', '0873233343', 'James Vo', '321 Dogwood St, Can Tho, Vietnam'),
(19, 'charlotte.ito@example.com', '0884344454', 'Charlotte Ito', '147 Beech St, Kobe, Japan'),
(20, 'benjamin.truong@example.com', '0895455565', 'Benjamin Truong', '258 Cedar St, Hue, Vietnam');

-- Payment_Method: 10 common payment methods
INSERT INTO Payment_Method (Payment_Method_ID, Method_Name, Description) VALUES
(1, 'Credit Card', 'Visa, MasterCard, or other credit cards'),
(2, 'Debit Card', 'Linked bank debit cards'),
(3, 'PayPal', 'Online payment via PayPal'),
(4, 'Apple Pay', 'Mobile payment using Apple devices'),
(5, 'Google Pay', 'Digital wallet with Google account'),
(6, 'Bank Transfer', 'Direct transfer from bank account'),
(7, 'Cash on Delivery', 'Pay with cash upon delivery'),
(8, 'Mobile Banking', 'Payment via smartphone banking apps'),
(9, 'Alipay', 'Popular digital wallet in China'),
(10, 'WeChat Pay', 'Mobile payment integrated with WeChat');

-- Shipping_Method: 5 common shipping methods
INSERT INTO Shipping_Method (Shipping_Method_ID, Method_Name, Description, Cost_per_product, average_delivery_time_per_km) VALUES
(1, 'Standard Shipping', 'Basic delivery with standard timing', 2.50, 0.60),
(2, 'Express Shipping', 'Fast delivery within 1–2 days', 5.00, 0.40),
(3, 'Same-Day Delivery', 'Delivery on the same day of order', 10.00, 0.15),
(4, 'In-Store Pickup', 'Customer picks up item in-store', 0.00, 0.00),
(5, 'International Standard', 'Standard international delivery', 12.00, 0.50);

-- Shipping_Address: Fixed inconsistencies (invalid data, missing fields)
INSERT INTO Shipping_Address (Address_ID, Customer_ID, Receiver_Name, Receiver_Phone, Country, City, Province_State, Postal_Code, Is_Default) VALUES
(1, 1, 'John Doe', '1234567890', 'USA', 'New York', 'NY', '10001', TRUE),
(2, 2, 'Jane Smith', '0987654321', 'USA', 'Los Angeles', 'CA', '90001', TRUE),
(3, 3, 'Alice Nguyen', '0912345678', 'USA', 'Chicago', 'IL', '60601', TRUE),
(4, 4, 'Bob Tanaka', '0801234567', 'Japan', 'Tokyo', 'Tokyo', '100-0001', TRUE),
(5, 5, 'Emma Wang', '0709876543', 'China', 'Beijing', 'Beijing', '100000', TRUE),
(6, 6, 'Lucas Martin', '0612345678', 'France', 'Paris', 'Île-de-France', '75001', TRUE),
(7, 7, 'Sofia Lee', '0501122334', 'South Korea', 'Seoul', 'Seoul', '04524', TRUE),
(8, 8, 'Liam Kim', '0402233445', 'South Korea', 'Busan', 'Busan', '48794', TRUE),
(9, 9, 'Olivia Chen', '0303344556', 'Taiwan', 'Taipei', 'Taipei', '100', TRUE),
(10, 10, 'Noah Tran', '0204455667', 'Vietnam', 'Hanoi', 'Hanoi', '100000', TRUE),
(11, 11, 'Ava Saito', '0905566778', 'Japan', 'Osaka', 'Osaka', '530-0001', TRUE),
(12, 12, 'Mason Kawasaki', '0816677889', 'Japan', 'Kyoto', 'Kyoto', '600-8001', TRUE),
(13, 13, 'Mia Hoang', '0827788990', 'Vietnam', 'Ho Chi Minh City', 'HCMC', '700000', TRUE),
(14, 14, 'Ethan Yamada', '0838899001', 'Japan', 'Sapporo', 'Hokkaido', '060-0001', TRUE),
(15, 15, 'Isabella Takahashi', '0849900112', 'Japan', 'Nagoya', 'Aichi', '450-0001', TRUE),
(16, 16, 'Logan Pham', '0851011121', 'Vietnam', 'Da Nang', 'Da Nang', '550000', TRUE),
(17, 17, 'Amelia Nakamura', '0862122232', 'Japan', 'Fukuoka', 'Fukuoka', '810-0001', TRUE),
(18, 18, 'James Vo', '0873233343', 'Vietnam', 'Can Tho', 'Can Tho', '900000', TRUE),
(19, 19, 'Charlotte Ito', '0884344454', 'Japan', 'Kobe', 'Hyogo', '650-0001', TRUE),
(20, 20, 'Benjamin Truong', '0895455565', 'Vietnam', 'Hue', 'Thua Thien-Hue', '530000', TRUE);

-- Promotion: 10 promotions with varied types and statuses
INSERT INTO Promotion (Promotion_ID, Description, Discount_Type, Discount_Value, Start_Date, End_Date, Coupon_Code, Minimum_Order, Status) VALUES
(1, 'Summer Sale 10% Off', 'percentage', 10.00, '2025-06-01', '2025-06-30', 'SUMMER10', 50.00, 'active'),
(2, '$15 Off Your Order', 'fixed_amount', 15.00, '2025-07-01', '2025-07-15', 'SAVE15', 75.00, 'active'),
(3, 'Black Friday 25%', 'percentage', 25.00, '2025-11-28', '2025-11-28', 'BLACK25', 100.00, 'inactive'),
(4, 'Holiday $20 Off', 'fixed_amount', 20.00, '2025-12-20', '2025-12-31', 'HOLIDAY20', 150.00, 'inactive'),
(5, 'Free Shipping', 'fixed_amount', 5.00, '2025-01-01', '2025-01-10', 'FREESHIP', 30.00, 'expired'),
(6, 'Welcome Bonus $10', 'fixed_amount', 10.00, '2025-01-01', '2025-12-31', 'WELCOME10', 20.00, 'active'),
(7, 'Student Discount 12%', 'percentage', 12.00, '2025-02-01', '2025-12-31', 'STUDENT12', 40.00, 'active'),
(8, 'VIP Deal $25 Off', 'fixed_amount', 25.00, '2025-05-01', '2025-05-31', 'VIP25', 200.00, 'active'),
(9, 'Birthday Promo 15%', 'percentage', 15.00, '2025-01-01', '2025-12-31', 'BDAY15', 30.00, 'active'),
(10, 'Refer a Friend $5', 'fixed_amount', 5.00, '2025-01-01', '2025-12-31', 'REFER5', 10.00, 'active');

-- Product: Realistic names, descriptions, and specifications, with timestamps
INSERT INTO Product (Product_ID, Product_Name, Category_ID, Brand_ID, Description, Price, Stock_Quantity, Image_URLs, Specifications, Created_Date, Updated_Date) VALUES
(1, 'Nike Air Zoom Pegasus 39', 6, 1, 'High-performance running shoes with Zoom Air cushioning for responsiveness.', 130.00, 100, 'https://example.com/nike_pegasus.jpg', 'Weight: 10.2 oz, Drop: 10mm, Cushioning: Zoom Air', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(2, 'Adidas Ultraboost 22', 6, 2, 'Premium running shoes with Boost midsole for energy return.', 180.00, 80, 'https://example.com/adidas_ultraboost.jpg', 'Weight: 11.8 oz, Drop: 10mm, Upper: Primeknit', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(3, 'Puma RS-X3 Puzzle Sneakers', 7, 3, 'Stylish sneakers with bold design and cushioned sole.', 110.00, 120, 'https://example.com/puma_rsx3.jpg', 'Material: Mesh/Synthetic, Sole: Rubber', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(4, 'Under Armour Charged Bandana', 14, 4, 'Lightweight running cap with moisture-wicking technology.', 25.00, 200, 'https://example.com/ua_bandana.jpg', 'Material: Polyester, Fit: Adjustable', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(5, 'Asics Gel-Kayano 29', 6, 5, 'Stability running shoes with Gel cushioning for comfort.', 160.00, 60, 'https://example.com/asics_kayano.jpg', 'Weight: 10.9 oz, Drop: 10mm, Cushioning: Gel', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(6, 'New Balance Fresh Foam T-Shirt', 10, 6, 'Breathable athletic t-shirt with NB Dry technology.', 35.00, 150, 'https://example.com/nb_tshirt.jpg', 'Material: Polyester, Technology: NB Dry', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(7, 'Converse Chuck 70 Low Top', 7, 7, 'Classic low-top sneakers with canvas upper.', 80.00, 90, 'https://example.com/converse_chuck70.jpg', 'Material: Canvas, Sole: Rubber', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(8, 'Fila Heritage Crew Socks', 15, 8, 'Comfortable athletic socks with cushioned sole.', 12.00, 300, 'https://example.com/fila_socks.jpg', 'Material: Cotton Blend, Pack: 3 pairs', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(9, 'Skechers D-Lites Sneakers', 7, 9, 'Lightweight sneakers with Air-Cooled Memory Foam.', 65.00, 150, 'https://example.com/skechers_dlites.jpg', 'Material: Leather/Mesh, Cushioning: Memory Foam', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(10, 'Vans Old Skool Sneakers', 7, 10, 'Iconic skate shoes with suede and canvas upper.', 70.00, 100, 'https://example.com/vans_oldskool.jpg', 'Material: Suede/Canvas, Sole: Waffle Rubber', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(11, 'Nike React Infinity Run 3', 6, 1, 'Running shoes with React foam for smooth ride.', 150.00, 70, 'https://example.com/nike_react.jpg', 'Weight: 10.5 oz, Drop: 9mm, Cushioning: React Foam', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(12, 'Adidas Performance Shorts', 11, 2, 'Lightweight shorts with Aeroready moisture-wicking.', 40.00, 120, 'https://example.com/adidas_shorts.jpg', 'Material: Polyester, Technology: Aeroready', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(13, 'Puma Essential Backpack', 17, 3, 'Durable backpack with padded straps.', 45.00, 80, 'https://example.com/puma_backpack.jpg', 'Material: Polyester, Capacity: 25L', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(14, 'Under Armour Hustle Jacket', 12, 4, 'Water-resistant jacket with fleece lining.', 90.00, 60, 'https://example.com/ua_jacket.jpg', 'Material: Polyester, Lining: Fleece', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(15, 'Asics Gel-Nimbus 24', 6, 5, 'Cushioned running shoes with Gel technology.', 150.00, 50, 'https://example.com/asics_nimbus.jpg', 'Weight: 11.1 oz, Drop: 10mm, Cushioning: Gel', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(16, 'New Balance Impact Shorts', 11, 6, 'Athletic shorts with inner brief.', 35.00, 100, 'https://example.com/nb_shorts.jpg', 'Material: Polyester, Length: 7-inch', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(17, 'Converse Slide Sandals', 8, 7, 'Comfortable sandals with cushioned footbed.', 30.00, 150, 'https://example.com/converse_sandals.jpg', 'Material: Synthetic, Sole: EVA', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(18, 'Fila Classic Cap', 14, 8, 'Adjustable cap with embroidered logo.', 20.00, 200, 'https://example.com/fila_cap.jpg', 'Material: Cotton, Fit: Adjustable', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(19, 'Skechers Go Run Fast', 6, 9, 'Lightweight running shoes with responsive cushioning.', 80.00, 90, 'https://example.com/skechers_gorun.jpg', 'Weight: 8.5 oz, Drop: 8mm, Cushioning: Hyper Burst', '2025-01-01 10:00:00', '2025-01-01 10:00:00'),
(20, 'Vans Classic Duffel Bag', 18, 10, 'Spacious duffel bag with side pocket.', 50.00, 70, 'https://example.com/vans_duffel.jpg', 'Material: Polyester, Capacity: 30L', '2025-01-01 10:00:00', '2025-01-01 10:00:00');

-- Order: Updated to reference valid IDs and use new schema
INSERT INTO "Order" (
    Order_ID, Customer_ID, Payment_Method_ID, Shipping_Method_ID, Shipping_Address_ID, Promotion_ID,
    Order_Date, Total_Amount, Shipping_Fee, Discount, Payment_Status, Order_Status, Estimated_Delivery_Date, Note
) VALUES
(1, 1, 1, 1, 1, 1, '2025-04-01 10:30:00', 150.00, 5.00, 15.00, 'paid', 'Processing', '2025-04-05', 'Leave at front door'),
(2, 2, 2, 2, 2, 2, '2025-04-02 15:00:00', 200.00, 10.00, 15.00, 'paid', 'Shipped', '2025-04-07', ''),
(3, 3, 1, 1, 3, 3, '2025-04-03 09:45:00', 80.00, 4.00, 20.00, 'pending', 'Pending', '2025-04-08', 'Call before delivery'),
(4, 4, 3, 2, 4, 4, '2025-04-04 14:20:00', 300.00, 12.00, 20.00, 'paid', 'Delivered', '2025-04-06', ''),
(5, 5, 2, 1, 5, NULL, '2025-04-05 11:10:00', 50.00, 3.00, 0.00, 'unpaid', 'Pending', '2025-04-10', ''),
(6, 1, 1, 2, 1, 5, '2025-04-06 12:00:00', 120.00, 5.00, 5.00, 'paid', 'Cancelled', '2025-04-09', ''),
(7, 2, 3, 1, 2, NULL, '2025-04-07 13:45:00', 95.00, 4.50, 0.00, 'pending', 'Processing', '2025-04-11', ''),
(8, 3, 2, 2, 3, 6, '2025-04-08 10:30:00', 130.00, 6.00, 10.00, 'paid', 'Shipped', '2025-04-12', ''),
(9, 4, 1, 1, 4, 7, '2025-04-09 16:15:00', 210.00, 8.00, 25.20, 'unpaid', 'Processing', '2025-04-14', ''),
(10, 5, 2, 3, 5, 8, '2025-04-10 11:00:00', 175.00, 7.50, 25.00, 'paid', 'Delivered', '2025-04-13', ''),
(11, 1, 1, 1, 1, NULL, '2025-04-11 09:20:00', 90.00, 4.00, 0.00, 'paid', 'Shipped', '2025-04-15', ''),
(12, 2, 3, 2, 2, 9, '2025-04-12 14:30:00', 160.00, 6.00, 24.00, 'paid', 'Delivered', '2025-04-16', ''),
(13, 3, 1, 1, 3, NULL, '2025-04-13 13:15:00', 45.00, 2.00, 0.00, 'unpaid', 'Cancelled', '2025-04-17', ''),
(14, 4, 2, 3, 4, 10, '2025-04-14 12:45:00', 220.00, 9.00, 5.00, 'paid', 'Processing', '2025-04-18', ''),
(15, 5, 3, 2, 5, NULL, '2025-04-15 16:10:00', 300.00, 10.00, 0.00, 'paid', 'Shipped', '2025-04-19', ''),
(16, 1, 1, 1, 1, 1, '2025-04-16 11:35:00', 70.00, 3.00, 7.00, 'pending', 'Pending', '2025-04-20', ''),
(17, 2, 2, 4, 2, NULL, '2025-04-17 10:50:00', 85.00, 0.00, 0.00, 'unpaid', 'Cancelled', '2025-04-21', ''),
(18, 3, 9, 3, 3, 2, '2025-04-18 14:00:00', 110.00, 6.00, 15.00, 'paid', 'Processing', '2025-04-22', ''),
(19, 4, 1, 2, 4, NULL, '2025-04-19 13:25:00', 65.00, 4.00, 0.00, 'paid', 'Delivered', '2025-04-23', ''),
(20, 5, 2, 5, 5, 3, '2025-04-20 09:40:00', 190.00, 12.00, 47.50, 'paid', 'Shipped', '2025-04-24', 'Gift order');

-- Order_Item: Updated to reference valid Product_IDs
INSERT INTO Order_Item (Order_ID, Product_ID, Quantity) VALUES
(1, 1, 2),
(1, 3, 1),
(2, 2, 3),
(2, 4, 2),
(3, 1, 2),
(3, 5, 1),
(4, 3, 2),
(4, 2, 3),
(5, 4, 1),
(5, 1, 3),
(6, 2, 2),
(6, 3, 1),
(7, 5, 2),
(8, 4, 3),
(9, 1, 1),
(9, 2, 2),
(10, 3, 2),
(11, 1, 2),
(12, 4, 2),
(13, 5, 1),
(14, 2, 3),
(15, 3, 2),
(16, 1, 1),
(17, 4, 2),
(18, 5, 2),
(19, 2, 1),
(20, 3, 3);

-- Review: Updated with Review_Date and valid IDs
INSERT INTO Review (Review_ID, Product_ID, Customer_ID, Rating, Comment, Review_Date, Images) VALUES
(1, 1, 1, 5, 'Love these running shoes, super comfortable!', '2025-04-05 12:00:00', 'https://example.com/review_nike_pegasus.jpg'),
(2, 2, 2, 4, 'Great energy return, but a bit pricey.', '2025-04-06 14:00:00', 'https://example.com/review_adidas_ultraboost.jpg'),
(3, 3, 3, 3, 'Stylish but not ideal for long walks.', '2025-04-07 10:00:00', 'https://example.com/review_puma_rsx3.jpg'),
(4, 4, 4, 5, 'Perfect cap for running, stays in place.', '2025-04-08 16:00:00', 'https://example.com/review_ua_bandana.jpg'),
(5, 5, 5, 2, 'Expected better durability for the price.', '2025-04-09 11:00:00', 'https://example.com/review_asics_kayano.jpg'),
(6, 6, 6, 4, 'Really soft and breathable t-shirt.', '2025-04-10 13:00:00', 'https://example.com/review_nb_tshirt.jpg'),
(7, 7, 7, 5, 'Classic style, goes with everything.', '2025-04-11 09:00:00', 'https://example.com/review_converse_chuck70.jpg'),
(8, 8, 8, 3, 'Decent socks, but wear out quickly.', '2025-04-12 15:00:00', 'https://example.com/review_fila_socks.jpg'),
(9, 9, 9, 4, 'Comfortable sneakers for daily wear.', '2025-04-13 10:00:00', 'https://example.com/review_skechers_dlites.jpg'),
(10, 10, 10, 1, 'Not durable, sole wore out fast.', '2025-04-14 12:00:00', 'https://example.com/review_vans_oldskool.jpg'),
(11, 11, 11, 5, 'Smooth ride, great for long runs.', '2025-04-15 14:00:00', 'https://example.com/review_nike_react.jpg'),
(12, 12, 12, 2, 'Shorts are okay, but sizing is off.', '2025-04-16 11:00:00', 'https://example.com/review_adidas_shorts.jpg'),
(13, 13, 13, 4, 'Spacious and sturdy backpack.', '2025-04-17 13:00:00', 'https://example.com/review_puma_backpack.jpg'),
(14, 14, 14, 5, 'Warm and lightweight jacket.', '2025-04-18 15:00:00', 'https://example.com/review_ua_jacket.jpg'),
(15, 15, 15, 3, 'Good cushioning, but a bit heavy.', '2025-04-19 10:00:00', 'https://example.com/review_asics_nimbus.jpg'),
(16, 16, 16, 4, 'Comfortable shorts for workouts.', '2025-04-20 12:00:00', 'https://example.com/review_nb_shorts.jpg'),
(17, 17, 17, 2, 'Sandals are stiff, not very comfy.', '2025-04-21 14:00:00', 'https://example.com/review_converse_sandals.jpg'),
(18, 18, 18, 5, 'Great cap, love the design.', '2025-04-22 11:00:00', 'https://example.com/review_fila_cap.jpg'),
(19, 19, 19, 3, 'Average running shoes, nothing special.', '2025-04-23 13:00:00', 'https://example.com/review_skechers_gorun.jpg'),
(20, 20, 20, 4, 'Solid duffel bag, good for gym.', '2025-04-24 15:00:00', 'https://example.com/review_vans_duffel.jpg');

