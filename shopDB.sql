-- =================================================================
-- SCRIPT TẠO DATABASE TỪ ĐẦU - DÙNG CHO QUERY TOOL
-- Dữ liệu đã được làm đa dạng và thực tế hơn.
-- =================================================================

-- Bắt đầu một transaction: nếu có lỗi, tất cả sẽ được khôi phục.
BEGIN;

-- =================================================================
-- PHẦN 1: TẠO CÁC KIỂU DỮ LIỆU TÙY CHỈNH (ENUMs)
-- =================================================================

CREATE TYPE public.discount_type AS ENUM (
    'percentage',
    'fixed_amount'
);

CREATE TYPE public.payment_status AS ENUM (
    'paid',
    'unpaid',
    'pending'
);

CREATE TYPE public.promotion_status AS ENUM (
    'active',
    'inactive',
    'expired'
);

-- =================================================================
-- PHẦN 2: TẠO CẤU TRÚC CÁC BẢNG
-- =================================================================

CREATE TABLE public.brand (
    brand_id integer NOT NULL,
    brand_name character varying(255) NOT NULL,
    description text,
    logo_url character varying(500),
    origin_country character varying(100)
);

CREATE TABLE public.product_category (
    category_id integer NOT NULL,
    parent_category_id integer,
    category_name character varying(255) NOT NULL,
    description text
);

CREATE TABLE public.customer (
    customer_id integer NOT NULL,
    email character varying(255),
    phone character varying(20),
    name character varying(255),
    address text
);

CREATE TABLE public.payment_method (
    payment_method_id integer NOT NULL,
    method_name character varying(100),
    description text
);

CREATE TABLE public.shipping_method (
    shipping_method_id integer NOT NULL,
    method_name character varying(100),
    description text,
    cost_per_product numeric(10,2),
    average_delivery_time_per_km numeric(5,2)
);

CREATE TABLE public.shipping_address (
    address_id integer NOT NULL,
    customer_id integer,
    receiver_name character varying(255),
    receiver_phone character varying(20),
    country character varying(100),
    city character varying(100),
    province_state character varying(100),
    postal_code character varying(20),
    is_default boolean DEFAULT false
);

CREATE TABLE public.promotion (
    promotion_id integer NOT NULL,
    description text,
    discount_type public.discount_type,
    discount_value numeric(10,2),
    start_date date,
    end_date date,
    coupon_code character varying(50),
    minimum_order numeric(10,2),
    status public.promotion_status
);

CREATE TABLE public.product (
    product_id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    category_id integer,
    brand_id integer,
    description text,
    price numeric(10,2),
    stock_quantity integer,
    image_urls text,
    specifications text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public."Order" (
    order_id integer NOT NULL,
    customer_id integer,
    payment_method_id integer,
    shipping_method_id integer,
    shipping_address_id integer,
    promotion_id integer,
    order_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    total_amount numeric(12,2),
    shipping_fee numeric(10,2),
    discount numeric(10,2),
    payment_status public.payment_status,
    order_status character varying(100),
    estimated_delivery_date date,
    note text
);

CREATE TABLE public.order_item (
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity integer
);

CREATE TABLE public.review (
    review_id integer NOT NULL,
    product_id integer,
    customer_id integer,
    rating integer,
    comment text,
    review_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    images text,
    CONSTRAINT review_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


-- =================================================================
-- PHẦN 3: CHÈN DỮ LIỆU MỚI VÀO CÁC BẢNG
-- =================================================================

-- Brand
INSERT INTO Brand (brand_id, brand_name, description, logo_url, origin_country) VALUES
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

-- Product_Category
INSERT INTO Product_Category (category_id, parent_category_id, category_name, description) VALUES
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

-- Customer (Updated emails)
INSERT INTO Customer (customer_id, email, phone, name, address) VALUES
(1, 'john.doe@gmail.com', '1234567890', 'John Doe', '123 Main St, New York, NY'),
(2, 'jane.smith@gmail.com', '0987654321', 'Jane Smith', '456 Elm St, Los Angeles, CA'),
(3, 'alice.nguyen@gmail.com', '0912345678', 'Alice Nguyen', '789 Oak St, Chicago, IL'),
(4, 'bob.tanaka@gmail.com', '0801234567', 'Bob Tanaka', '321 Pine St, Tokyo, Japan'),
(5, 'emma.wang@gmail.com', '0709876543', 'Emma Wang', '654 Maple St, Beijing, China'),
(6, 'lucas.martin@gmail.com', '0612345678', 'Lucas Martin', '987 Birch St, Paris, France'),
(7, 'sofia.lee@gmail.com', '0501122334', 'Sofia Lee', '147 Cedar St, Seoul, South Korea'),
(8, 'liam.kim@gmail.com', '0402233445', 'Liam Kim', '258 Walnut St, Busan, South Korea'),
(9, 'olivia.chen@gmail.com', '0303344556', 'Olivia Chen', '369 Chestnut St, Taipei, Taiwan'),
(10, 'noah.tran@gmail.com', '0204455667', 'Noah Tran', '741 Spruce St, Hanoi, Vietnam'),
(11, 'ava.saito@gmail.com', '0905566778', 'Ava Saito', '852 Willow St, Osaka, Japan'),
(12, 'mason.kawasaki@gmail.com', '0816677889', 'Mason Kawasaki', '963 Poplar St, Kyoto, Japan'),
(13, 'mia.hoang@gmail.com', '0827788990', 'Mia Hoang', '159 Aspen St, Ho Chi Minh City, Vietnam'),
(14, 'ethan.yamada@gmail.com', '0838899001', 'Ethan Yamada', '753 Fir St, Sapporo, Japan'),
(15, 'isabella.takahashi@gmail.com', '0849900112', 'Isabella Takahashi', '456 Redwood St, Nagoya, Japan'),
(16, 'logan.pham@gmail.com', '0851011121', 'Logan Pham', '654 Sycamore St, Da Nang, Vietnam'),
(17, 'amelia.nakamura@gmail.com', '0862122232', 'Amelia Nakamura', '987 Palm St, Fukuoka, Japan'),
(18, 'james.vo@gmail.com', '0873233343', 'James Vo', '321 Dogwood St, Can Tho, Vietnam'),
(19, 'charlotte.ito@gmail.com', '0884344454', 'Charlotte Ito', '147 Beech St, Kobe, Japan'),
(20, 'benjamin.truong@gmail.com', '0895455565', 'Benjamin Truong', '258 Cedar St, Hue, Vietnam');

-- Payment_Method
INSERT INTO Payment_Method (payment_method_id, method_name, description) VALUES
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

-- Shipping_Method
INSERT INTO Shipping_Method (shipping_method_id, method_name, description, cost_per_product, average_delivery_time_per_km) VALUES
(1, 'Standard Shipping', 'Basic delivery with standard timing', 2.50, 0.60),
(2, 'Express Shipping', 'Fast delivery within 1–2 days', 5.00, 0.40),
(3, 'Same-Day Delivery', 'Delivery on the same day of order', 10.00, 0.15),
(4, 'In-Store Pickup', 'Customer picks up item in-store', 0.00, 0.00),
(5, 'International Standard', 'Standard international delivery', 12.00, 0.50);

-- Shipping_Address
INSERT INTO Shipping_Address (address_id, customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code, is_default) VALUES
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

-- Promotion
INSERT INTO Promotion (promotion_id, description, discount_type, discount_value, start_date, end_date, coupon_code, minimum_order, status) VALUES
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

-- Product (Diverse and realistic data)
INSERT INTO Product (product_id, product_name, category_id, brand_id, description, price, stock_quantity, image_urls, specifications, created_date, updated_date) VALUES
(1, 'Nike Air Max 270', 7, 1, 'Features the first-ever Max Air unit created specifically for Nike Sportswear.', 150.00, 100, 'https://example.com/nike_airmax.jpg', 'Color: Black/White, Upper: Knit', '2025-01-15 10:00:00', '2025-01-15 10:00:00'),
(2, 'Adidas Ultraboost Light', 6, 2, 'Our lightest Ultraboost ever, made with 30% lighter BOOST material.', 180.00, 80, 'https://example.com/adidas_ultraboost.jpg', 'Weight: 10.5 oz, Midsole: Light BOOST', '2025-01-15 10:00:00', '2025-01-15 10:00:00'),
(3, 'Puma Suede Classic XXI', 7, 3, 'An iconic sneaker that has been a style staple for over 50 years.', 75.00, 120, 'https://example.com/puma_suede.jpg', 'Material: Suede, Sole: Rubber', '2025-02-01 11:00:00', '2025-02-01 11:00:00'),
(4, 'Under Armour Tech 2.0 T-Shirt', 10, 4, 'Loose, light, and it keeps you cool. It''s everything you need.', 25.00, 200, 'https://example.com/ua_tech_tee.jpg', 'Fabric: UA Tech, Fit: Loose', '2025-02-01 11:00:00', '2025-02-01 11:00:00'),
(5, 'Asics Gel-Kayano 30', 6, 5, 'Provides advanced stability and softer cushioning for a comfortable run.', 160.00, 60, 'https://example.com/asics_kayano.jpg', 'Cushioning: GEL Technology, Support: 4D GUIDANCE SYSTEM', '2025-02-10 09:30:00', '2025-02-10 09:30:00'),
(6, 'New Balance 990v6', 7, 6, 'The 990v6 embraces a streamlined approach with a focus on performance.', 200.00, 50, 'https://example.com/nb_990v6.jpg', 'Midsole: FuelCell, Upper: Suede/Mesh', '2025-02-20 14:00:00', '2025-02-20 14:00:00'),
(7, 'Converse Chuck Taylor All Star', 7, 7, 'The timeless and iconic high-top sneaker.', 60.00, 150, 'https://example.com/converse_chuck.jpg', 'Upper: Canvas, Outsole: Diamond Tread', '2025-03-05 16:20:00', '2025-03-05 16:20:00'),
(8, 'Fila Disruptor II Premium', 7, 8, 'The iconic chunky sneaker with a bold, retro look.', 65.00, 90, 'https://example.com/fila_disruptor.jpg', 'Material: Leather, Midsole: EVA', '2025-03-10 10:10:00', '2025-03-10 10:10:00'),
(9, 'Skechers Go Walk Arch Fit', 7, 9, 'Get all the support you need for your long walks with Arch Fit technology.', 85.00, 110, 'https://example.com/skechers_gowalk.jpg', 'Insole: Arch Fit, Outsole: High-rebound', '2025-03-12 18:00:00', '2025-03-12 18:00:00'),
(10, 'Vans Old Skool Backpack', 17, 10, 'A classic backpack with a large main compartment and a front zip pocket.', 45.00, 130, 'https://example.com/vans_backpack.jpg', 'Capacity: 22L, Material: Polyester', '2025-03-15 11:45:00', '2025-03-15 11:45:00'),
(11, 'Nike Dri-FIT Legend Tee', 10, 1, 'A soft, sweat-wicking tee to keep you dry and comfortable.', 30.00, 250, 'https://example.com/nike_drifit_tee.jpg', 'Technology: Dri-FIT, Material: Polyester', '2025-03-20 09:00:00', '2025-03-20 09:00:00'),
(12, 'Adidas Tiro 23 Training Pants', 13, 2, 'Slim-fitting pants with AEROREADY to keep you dry on the pitch.', 50.00, 140, 'https://example.com/adidas_tiro.jpg', 'Pockets: Zip Pockets, Fit: Slim', '2025-03-22 13:00:00', '2025-03-22 13:00:00'),
(13, 'Puma Essentials Logo Hoodie', 12, 3, 'A classic hoodie for everyday comfort and style.', 55.00, 100, 'https://example.com/puma_hoodie.jpg', 'Material: Cotton/Polyester, Lining: Fleece', '2025-04-01 10:00:00', '2025-04-01 10:00:00'),
(14, 'Under Armour Play Up Shorts 3.0', 11, 4, 'Lightweight knit construction delivers superior comfort & breathability.', 30.00, 180, 'https://example.com/ua_shorts.jpg', 'Inseam: 3", Pockets: Side hand pockets', '2025-04-02 15:00:00', '2025-04-02 15:00:00'),
(15, 'Asics GT-2000 12', 6, 5, 'A versatile stability trainer that’s functional for various distances.', 140.00, 75, 'https://example.com/asics_gt2000.jpg', 'Support: Stability, Drop: 8mm', '2025-04-05 12:00:00', '2025-04-05 12:00:00'),
(16, 'New Balance 574 Core', 7, 6, 'A collectible icon, the 574 is a hybrid road/trail design.', 85.00, 160, 'https://example.com/nb_574.jpg', 'Cushioning: ENCAP, Upper: Suede/Mesh', '2025-04-10 17:00:00', '2025-04-10 17:00:00'),
(17, 'Converse Run Star Hike', 7, 7, 'A chunky platform and jagged rubber sole put an unexpected twist on your everyday Chucks.', 110.00, 85, 'https://example.com/converse_runstar.jpg', 'Platform: Lugged, Insole: SmartFOAM', '2025-04-11 11:30:00', '2025-04-11 11:30:00'),
(18, 'Fila Unisex Bucket Hat', 14, 8, 'A classic bucket hat for a cool, casual look.', 25.00, 220, 'https://example.com/fila_bucket_hat.jpg', 'Material: 100% Cotton Twill', '2025-04-12 14:00:00', '2025-04-12 14:00:00'),
(19, 'Skechers Max Cushioning Elite', 6, 9, 'Experience ultimate comfort and response with Skechers Max Cushioning.', 95.00, 105, 'https://example.com/skechers_maxcushion.jpg', 'Platform: ULTRA GO, Insole: Goga Mat', '2025-04-15 09:00:00', '2025-04-15 09:00:00'),
(20, 'Vans Ward Cross Body Pack', 19, 10, 'A durable waist pack for on-the-go convenience.', 30.00, 190, 'https://example.com/vans_waistpack.jpg', 'Material: CORDURA fabrics', '2025-04-18 16:00:00', '2025-04-18 16:00:00');

-- Order
INSERT INTO "Order" (order_id, customer_id, payment_method_id, shipping_method_id, shipping_address_id, promotion_id, order_date, total_amount, shipping_fee, discount, payment_status, order_status, estimated_delivery_date, note) VALUES
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

-- Order_Item (Updated to reference new products)
INSERT INTO Order_Item (order_id, product_id, quantity) VALUES
(1, 1, 1), (1, 11, 2), (2, 2, 1), (2, 12, 1), (3, 3, 1), (4, 4, 3), (4, 14, 1),
(5, 5, 1), (6, 6, 1), (7, 7, 2), (8, 8, 1), (9, 9, 2), (9, 19, 1), (10, 10, 1),
(11, 15, 1), (12, 16, 2), (13, 17, 1), (14, 18, 4), (15, 13, 1), (16, 1, 1),
(17, 4, 1), (18, 5, 1), (19, 2, 1), (20, 3, 1);

-- Review (Updated with relevant comments for new products)
INSERT INTO Review (review_id, product_id, customer_id, rating, comment, review_date, images) VALUES
(1, 1, 1, 5, 'The Air Max 270 is so comfortable for everyday wear!', '2025-04-05 12:00:00', 'https://example.com/review_airmax.jpg'),
(2, 2, 2, 4, 'Ultraboost has amazing energy return, but it is a bit pricey.', '2025-04-06 14:00:00', 'https://example.com/review_ultraboost.jpg'),
(3, 3, 3, 5, 'Love the classic look of the Puma Suede. Goes with everything.', '2025-04-07 10:00:00', NULL),
(4, 4, 4, 4, 'This UA shirt is great for the gym. Very breathable.', '2025-04-08 16:00:00', 'https://example.com/review_uatee.jpg'),
(5, 5, 5, 5, 'Asics Gel-Kayano provides the best stability for my long runs. Highly recommend.', '2025-04-09 11:00:00', NULL),
(6, 6, 6, 4, 'The New Balance 990v6 is incredibly well-made. Worth the price.', '2025-04-10 13:00:00', 'https://example.com/review_nb990.jpg'),
(7, 7, 7, 5, 'Can never go wrong with a classic pair of Chucks.', '2025-04-11 09:00:00', NULL),
(8, 8, 8, 3, 'The Fila Disruptors are stylish but a bit too heavy for me.', '2025-04-12 15:00:00', 'https://example.com/review_disruptor.jpg'),
(9, 9, 9, 5, 'Skechers Arch Fit is a lifesaver for my flat feet. So comfortable!', '2025-04-13 10:00:00', NULL),
(10, 10, 10, 4, 'This Vans backpack is durable and has plenty of space.', '2025-04-14 12:00:00', NULL),
(11, 11, 1, 5, 'Another great Dri-FIT shirt from Nike. Perfect for workouts.', '2025-04-15 14:00:00', 'https://example.com/review_drifit.jpg'),
(12, 12, 2, 4, 'The Tiro pants are perfect for training or just lounging.', '2025-04-16 11:00:00', NULL),
(13, 13, 3, 4, 'Cozy hoodie, good quality.', '2025-04-17 13:00:00', 'https://example.com/review_pumahoodie.jpg'),
(14, 14, 4, 3, 'These UA shorts are a bit shorter than I expected.', '2025-04-18 15:00:00', NULL),
(15, 15, 5, 5, 'The GT-2000 is my go-to running shoe. Reliable and comfortable.', '2025-04-19 10:00:00', 'https://example.com/review_gt2000.jpg'),
(16, 16, 6, 4, 'New Balance 574 is a stylish and comfortable retro sneaker.', '2025-04-20 12:00:00', NULL),
(17, 17, 7, 3, 'The Run Star Hike platform is cool but takes some getting used to.', '2025-04-21 14:00:00', 'https://example.com/review_runstar.jpg'),
(18, 18, 8, 5, 'Love this Fila bucket hat!', '2025-04-22 11:00:00', NULL),
(19, 19, 9, 4, 'Very light and responsive shoes from Skechers.', '2025-04-23 13:00:00', 'https://example.com/review_maxcushion.jpg'),
(20, 20, 10, 5, 'Perfect size for a waist pack. Great quality from Vans.', '2025-04-24 15:00:00', NULL);

-- =================================================================
-- PHẦN 4: THIẾT LẬP ID TỰ TĂNG (SEQUENCES)
-- =================================================================

-- Tạo Sequences
CREATE SEQUENCE public."Order_order_id_seq" AS integer;
CREATE SEQUENCE public.brand_brand_id_seq AS integer;
CREATE SEQUENCE public.customer_customer_id_seq AS integer;
CREATE SEQUENCE public.payment_method_payment_method_id_seq AS integer;
CREATE SEQUENCE public.product_category_category_id_seq AS integer;
CREATE SEQUENCE public.product_product_id_seq AS integer;
CREATE SEQUENCE public.promotion_promotion_id_seq AS integer;
CREATE SEQUENCE public.review_review_id_seq AS integer;
CREATE SEQUENCE public.shipping_address_address_id_seq AS integer;
CREATE SEQUENCE public.shipping_method_shipping_method_id_seq AS integer;

-- Gán Sequences làm giá trị mặc định cho các cột ID
ALTER TABLE public."Order" ALTER COLUMN order_id SET DEFAULT nextval('public."Order_order_id_seq"'::regclass);
ALTER TABLE public.brand ALTER COLUMN brand_id SET DEFAULT nextval('public.brand_brand_id_seq'::regclass);
ALTER TABLE public.customer ALTER COLUMN customer_id SET DEFAULT nextval('public.customer_customer_id_seq'::regclass);
ALTER TABLE public.payment_method ALTER COLUMN payment_method_id SET DEFAULT nextval('public.payment_method_payment_method_id_seq'::regclass);
ALTER TABLE public.product ALTER COLUMN product_id SET DEFAULT nextval('public.product_product_id_seq'::regclass);
ALTER TABLE public.product_category ALTER COLUMN category_id SET DEFAULT nextval('public.product_category_category_id_seq'::regclass);
ALTER TABLE public.promotion ALTER COLUMN promotion_id SET DEFAULT nextval('public.promotion_promotion_id_seq'::regclass);
ALTER TABLE public.review ALTER COLUMN review_id SET DEFAULT nextval('public.review_review_id_seq'::regclass);
ALTER TABLE public.shipping_address ALTER COLUMN address_id SET DEFAULT nextval('public.shipping_address_address_id_seq'::regclass);
ALTER TABLE public.shipping_method ALTER COLUMN shipping_method_id SET DEFAULT nextval('public.shipping_method_shipping_method_id_seq'::regclass);

-- Cập nhật giá trị hiện tại của Sequences để khớp với dữ liệu đã chèn
SELECT setval('public.brand_brand_id_seq', (SELECT MAX(brand_id) FROM public.brand));
SELECT setval('public.product_category_category_id_seq', (SELECT MAX(category_id) FROM public.product_category));
SELECT setval('public.customer_customer_id_seq', (SELECT MAX(customer_id) FROM public.customer));
SELECT setval('public.payment_method_payment_method_id_seq', (SELECT MAX(payment_method_id) FROM public.payment_method));
SELECT setval('public.shipping_method_shipping_method_id_seq', (SELECT MAX(shipping_method_id) FROM public.shipping_method));
SELECT setval('public.shipping_address_address_id_seq', (SELECT MAX(address_id) FROM public.shipping_address));
SELECT setval('public.promotion_promotion_id_seq', (SELECT MAX(promotion_id) FROM public.promotion));
SELECT setval('public.product_product_id_seq', (SELECT MAX(product_id) FROM public.product));
SELECT setval('public."Order_order_id_seq"', (SELECT MAX(order_id) FROM public."Order"));
SELECT setval('public.review_review_id_seq', (SELECT MAX(review_id) FROM public.review));


-- =================================================================
-- PHẦN 5: TẠO CÁC RÀNG BUỘC (CONSTRAINTS)
-- =================================================================

-- Khóa chính (Primary Keys)
ALTER TABLE public."Order" ADD CONSTRAINT "Order_pkey" PRIMARY KEY (order_id);
ALTER TABLE public.brand ADD CONSTRAINT brand_pkey PRIMARY KEY (brand_id);
ALTER TABLE public.customer ADD CONSTRAINT customer_pkey PRIMARY KEY (customer_id);
ALTER TABLE public.order_item ADD CONSTRAINT order_item_pkey PRIMARY KEY (order_id, product_id);
ALTER TABLE public.payment_method ADD CONSTRAINT payment_method_pkey PRIMARY KEY (payment_method_id);
ALTER TABLE public.product_category ADD CONSTRAINT product_category_pkey PRIMARY KEY (category_id);
ALTER TABLE public.product ADD CONSTRAINT product_pkey PRIMARY KEY (product_id);
ALTER TABLE public.promotion ADD CONSTRAINT promotion_pkey PRIMARY KEY (promotion_id);
ALTER TABLE public.review ADD CONSTRAINT review_pkey PRIMARY KEY (review_id);
ALTER TABLE public.shipping_address ADD CONSTRAINT shipping_address_pkey PRIMARY KEY (address_id);
ALTER TABLE public.shipping_method ADD CONSTRAINT shipping_method_pkey PRIMARY KEY (shipping_method_id);

-- Ràng buộc duy nhất (Unique Constraints)
ALTER TABLE public.customer ADD CONSTRAINT customer_email_key UNIQUE (email);

-- Khóa ngoại (Foreign Keys)
ALTER TABLE public."Order" ADD CONSTRAINT "Order_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES public.customer(customer_id);
ALTER TABLE public."Order" ADD CONSTRAINT "Order_payment_method_id_fkey" FOREIGN KEY (payment_method_id) REFERENCES public.payment_method(payment_method_id);
ALTER TABLE public."Order" ADD CONSTRAINT "Order_promotion_id_fkey" FOREIGN KEY (promotion_id) REFERENCES public.promotion(promotion_id);
ALTER TABLE public."Order" ADD CONSTRAINT "Order_shipping_address_id_fkey" FOREIGN KEY (shipping_address_id) REFERENCES public.shipping_address(address_id);
ALTER TABLE public."Order" ADD CONSTRAINT "Order_shipping_method_id_fkey" FOREIGN KEY (shipping_method_id) REFERENCES public.shipping_method(shipping_method_id);
ALTER TABLE public.order_item ADD CONSTRAINT order_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES public."Order"(order_id);
ALTER TABLE public.order_item ADD CONSTRAINT order_item_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(product_id);
ALTER TABLE public.product ADD CONSTRAINT product_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.brand(brand_id);
ALTER TABLE public.product ADD CONSTRAINT product_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_category(category_id);
ALTER TABLE public.product_category ADD CONSTRAINT product_category_parent_category_id_fkey FOREIGN KEY (parent_category_id) REFERENCES public.product_category(category_id);
ALTER TABLE public.review ADD CONSTRAINT review_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer(customer_id);
ALTER TABLE public.review ADD CONSTRAINT review_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(product_id);
ALTER TABLE public.shipping_address ADD CONSTRAINT shipping_address_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer(customer_id);

-- Kết thúc transaction và xác nhận các thay đổi
COMMIT;