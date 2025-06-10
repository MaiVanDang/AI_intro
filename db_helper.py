from binascii import Error
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

# global cnx

# cnx = psycopg2.connect(
#     host="localhost",
#     user="postgres",
#     password="admin",
#     database="shopDB"
# )

def init_db_connection():
    global cnx
    try:
        cnx = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="admin",
            database="shopDB"
        )
        print("Database connection initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database connection: {e}")
        cnx = None

init_db_connection()

def get_list_products_by_brand(brand_name):
    cursor = cnx.cursor()
    query = """
        SELECT product_id, product_name 
        FROM product 
        JOIN brand ON product.brand_id = brand.brand_id 
        WHERE brand.brand_name = %s;
    """
    cursor.execute(query, (brand_name,))
    results = cursor.fetchall()
    cursor.close()
    return results

def get_list_products_by_price(brand_name, price_range, price):
    cursor = cnx.cursor()
    try:
        if price_range == "Under":
            min_price = 0
            max_price = price
        elif price_range == "Between":
            if not isinstance(price, (list, tuple)) or len(price) != 2:
                return [] 
            min_price, max_price = price
        else:
            return [] 

        if brand_name == "":
            query = """
                SELECT product_id, product_name 
                FROM product 
                WHERE price BETWEEN %s AND %s;
            """
            cursor.execute(query, (min_price, max_price))
        else:
            query = """
                SELECT product_id, product_name 
                FROM product 
                JOIN brand ON product.brand_id = brand.brand_id 
                WHERE brand.brand_name = %s AND price BETWEEN %s AND %s;
            """
            cursor.execute(query, (brand_name, min_price, max_price))

        results = cursor.fetchall()
        return results
    finally:
        cursor.close()

def get_list_products_by_id(product_id):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT 
                p.product_name, 
                p.description AS product_description,
                p.price, 
                p.specifications, 
                b.brand_name, 
                p.stock_quantity,
                b.description AS brand_description,
                b.origin_country 
            FROM product p 
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s;
        """
        cursor.execute(query, (product_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        cnx.rollback()  
        print(f"[ERROR] Failed to execute query: {e}")
        return []
    finally:
        cursor.close()

def get_product_cheapest():
    cursor = cnx.cursor()
    try:
        query = """
            SELECT 
                p.product_name, 
                p.description AS product_description,
                p.price, 
                p.specifications, 
                b.brand_name, 
                b.description AS brand_description,
                b.origin_country 
            FROM product p 
            JOIN brand b ON p.brand_id = b.brand_id
            ORDER BY p.price ASC LIMIT 1;
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[ERROR] Failed to execute query: {e}")
        return None
    finally:
        cursor.close()

def get_products_by_name(product_name):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT 
                p.product_id,
                p.product_name, 
                p.description AS product_description,
                p.price, 
                p.specifications, 
                b.brand_name, 
                b.origin_country, 
                p.stock_quantity
            FROM product p 
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE p.product_name = %s;
        """
        cursor.execute(query, (product_name,))
        return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR] Failed to query products by name: {e}")
        return None
    finally:
        cursor.close()

def get_valid_promotions(min_order: float):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT 
                coupon_code, 
                description, 
                minimum_order
            FROM promotion
            WHERE minimum_order <= %s AND status = 'active'
        """
        cursor.execute(query, (min_order,))
        results = cursor.fetchall()
        return [
            {
                "coupon_code": row[0],
                "description": row[1],
                "minimum_order": row[2]
            }
            for row in results
        ]
    except Exception as e:
        print(f"[ERROR] Failed to get promotions: {e}")
        return []
    finally:
        cursor.close()

def get_promotion_by_code(coupon_code: str):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT Promotion_ID, coupon_code, discount_value
            FROM promotion
            WHERE coupon_code = %s
        """
        cursor.execute(query, (coupon_code,))
        result = cursor.fetchone()
        return result  # (promotion_id, coupon_code, discount_value)
    except Exception as e:
        print(f"[ERROR] get_promotion_by_code failed: {e}")
        return None
    finally:
        cursor.close()

def get_customer_by_email_or_phone(email: str, phone: str):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT customer_id FROM customer
            WHERE email = %s OR phone = %s
        """
        cursor.execute(query, (email, phone))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[ERROR] Failed to get customer by email or phone: {e}")
        return None
    finally:
        cursor.close()

def get_customer_info(customer_id: int):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT name, email, phone
            FROM customer
            WHERE customer_id = %s
        """
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[ERROR] Failed to get customer info: {e}")
        return None
    finally:
        cursor.close()

def get_default_address_by_customer(customer_id: int):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT address_id, receiver_name, receiver_phone, country, city, province_state, postal_code
            FROM shipping_address
            WHERE customer_id = %s AND is_default = TRUE
        """
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[ERROR] Failed to get default address: {e}")
        return None
    finally:
        cursor.close()

def get_shipping_methods():
    cursor = cnx.cursor()
    try:
        query = """
            SELECT shipping_method_id, method_name, cost_per_product, average_delivery_time_per_km
            FROM shipping_method
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return [
            {
                "method_id": row[0],
                "method_name": row[1],
                "cost_per_product": float(row[2]),
                "average_delivery_time_per_km": float(row[3])
            }
            for row in results
        ]
    except Exception as e:
        print(f"[ERROR] Failed to get shipping methods: {e}")
        return []
    finally:
        cursor.close()

def save_new_shipping_address(customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code, is_default):
    cursor = cnx.cursor()
    try:
        query = """
            INSERT INTO shipping_address (customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING address_id
        """
        cursor.execute(query, (customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code, is_default))
        new_address_id = cursor.fetchone()[0]
        cnx.commit()
        return new_address_id
    except Exception as e:
        cnx.rollback()
        print(f"[ERROR] Failed to save new shipping address: {e}")
        return None
    finally:
        cursor.close()

def get_payment_methods():
    cursor = cnx.cursor()
    try:
        query = """
            SELECT Payment_Method_ID, Method_Name, Description
            FROM Payment_Method
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return [
            {
                "method_id": row[0],
                "method_name": row[1],
                "description": row[2]
            }
            for row in results
        ]
    except Exception as e:
        print(f"[ERROR] Failed to get payment methods: {e}")
        return []
    finally:
        cursor.close()

def place_order(order_details: dict, session_id: str):
    cursor = cnx.cursor()
    try:
        # Lưu vào bảng Order
        query = """
            INSERT INTO "Order" (
                Customer_ID, Payment_Method_ID, Shipping_Method_ID, Shipping_Address_ID,
                Promotion_ID, Total_Amount, Shipping_Fee, Discount,
                Estimated_Delivery_Date, Payment_Status, Order_Status, Note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING Order_ID
        """
        cursor.execute(query, (
            order_details["customer_id"],
            order_details["payment_method_id"],
            order_details["shipping_method_id"],
            order_details["shipping_address_id"],
            order_details["promotion_id"],
            order_details["total_amount"],
            order_details["shipping_fee"],
            order_details["discount"],
            order_details["estimated_delivery_date"],
            "pending",  # Payment_Status
            "pending",  # Order_Status
            f"Order placed via chatbot (session: {session_id})"  # Note
        ))
        order_id = cursor.fetchone()[0]

        # Lưu chi tiết order vào bảng Order_Item
        for product_id, quantity in order_details["order_list"]:
            query = """
                INSERT INTO Order_Item (Order_ID, Product_ID, Quantity)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (order_id, product_id, quantity))

        cnx.commit()
        return order_id
    except Exception as e:
        cnx.rollback()
        print(f"[ERROR] Failed to place order: {e}")
        return None
    finally:
        cursor.close()

def get_available_promotions(minimum_order_value: float):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT Promotion_ID, Coupon_Code, Discount_Value, Minimum_Order
            FROM Promotion
            WHERE Status = 'active'
            AND Minimum_Order <= %s
            AND (End_Date IS NULL OR End_Date >= CURRENT_DATE)
        """
        cursor.execute(query, (minimum_order_value,))
        results = cursor.fetchall()
        return results  # (promotion_id, coupon_code, discount_value, minimum_order)
    except Exception as e:
        print(f"[ERROR] Failed to get available promotions: {e}")
        return []
    finally:
        cursor.close()

def get_customer_orders(customer_id=None, customer_name=None):
    if not cnx:
        init_db_connection()
        if not cnx:
            return []

    try:
        cursor = cnx.cursor(cursor_factory=RealDictCursor)

        if customer_id:
            query = """
                SELECT 
                    o.Order_ID,
                    STRING_AGG(p.Product_Name, ', ') AS Product_Names,
                    o.Total_Amount,
                    pm.Method_Name AS Payment_Method,
                    o.Order_Status,
                    o.Order_Date
                FROM "Order" o
                JOIN Order_Item oi ON o.Order_ID = oi.Order_ID
                JOIN Product p ON oi.Product_ID = p.Product_ID
                JOIN Payment_Method pm ON o.Payment_Method_ID = pm.Payment_Method_ID
                JOIN Customer c ON o.Customer_ID = c.Customer_ID
                WHERE c.Customer_ID = %s
                GROUP BY o.Order_ID, o.Total_Amount, pm.Method_Name, o.Order_Status, o.Order_Date
                ORDER BY o.Order_Date DESC;
            """
            cursor.execute(query, (customer_id,))
        elif customer_name:
            query = """
                SELECT 
                    o.order_id,
                    STRING_AGG(p.product_name, ', ') AS Product_Names,
                    o.total_amount,
                    pm.method_name AS Payment_Method,
                    o.order_status,
                    o.order_date
                FROM "Order" o
                JOIN order_item oi ON o.order_id = oi.order_id
                JOIN product p ON oi.product_id = p.product_id
                JOIN payment_method pm ON o.payment_method_id = pm.payment_method_id
                JOIN customer c ON o.customer_id = c.customer_id
                WHERE c.name ILIKE %s
                GROUP BY o.order_id, o.total_amount, pm.method_name, o.order_status, o.order_date
                ORDER BY o.order_date DESC;
            """
            cursor.execute(query, (f"%{customer_name}%",))
        else:
            return []

        orders = cursor.fetchall()
        cursor.close()
        return orders

    except Exception as e:
        print(f"An error occurred in get_customer_orders: {e}")
        return []
 
def delete_order(order_id):
    """
    Delete a specific order by Order_ID if its status is 'processing'.
    Returns True if successful, False if the order doesn't exist or status is not 'processing'.
    """
    if not cnx:
        init_db_connection()
        if not cnx:
            return False

    try:
        cursor = cnx.cursor()
        # Check if the order exists and has status 'processing'
        check_query = """
                SELECT COUNT(*) FROM "Order"
                WHERE order_id = %s AND order_status = 'Processing'
        """
        cursor.execute(check_query, (order_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.close()
            return False

        # Delete from Order_Item first (due to foreign key constraint)
        cursor.execute('DELETE FROM "order_item" WHERE order_id = %s', (order_id,))
        # Delete from Order
        cursor.execute('DELETE FROM "Order" WHERE order_id = %s', (order_id,))

        cnx.commit()
        cursor.close()
        return True
    except Error as err:
        print(f"Error deleting order {order_id}: {err}")
        if cnx:
            cnx.rollback()
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        if cnx:
            cnx.rollback()
        return False 
    
def update_shipping_address(order_id, customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code):
    """
    Update shipping address for a specific order by Order_ID if its status is 'processing'.
    Inserts a new address into Shipping_Address and updates Order with the new Shipping_Address_ID.
    Returns True if successful, False if the order doesn't exist, status is not 'processing', or error occurs.
    """
    if not cnx:
        init_db_connection()
        if not cnx:
            return False

    cursor = None  
    try:
        # Fix receiver_name if it's still a dict (fallback protection)
        if isinstance(receiver_name, dict):
            if 'name' in receiver_name:
                receiver_name = receiver_name['name']
            else:
                receiver_name = str(receiver_name)
        elif isinstance(receiver_name, list) and len(receiver_name) > 0:
            first_item = receiver_name[0]
            if isinstance(first_item, dict) and 'name' in first_item:
                receiver_name = first_item['name']
            else:
                receiver_name = str(first_item)
        
        # Debug: Print values and types before executing query
        print(f"Values being inserted:")
        print(f"order_id: {type(order_id)} = {order_id}")
        print(f"customer_id: {type(customer_id)} = {customer_id}")
        print(f"receiver_name: {type(receiver_name)} = {receiver_name}")
        print(f"receiver_phone: {type(receiver_phone)} = {receiver_phone}")
        print(f"country: {type(country)} = {country}")
        print(f"city: {type(city)} = {city}")
        print(f"province_state: {type(province_state)} = {province_state}")
        print(f"postal_code: {type(postal_code)} = {postal_code}")
        
        cursor = cnx.cursor()
        
        check_query = """
            SELECT COUNT(*) FROM "Order"
            WHERE order_id = %s AND customer_id = %s AND order_status = 'Processing'
        """
        cursor.execute(check_query, (order_id, customer_id))
        count = cursor.fetchone()[0]

        if count == 0:
            return False

        insert_address_query = """
            INSERT INTO "shipping_address" (customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING address_id
        """
        cursor.execute(insert_address_query, (customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code))
        
        new_address_id = cursor.fetchone()[0]

        update_order_query = """
            UPDATE "Order"
            SET shipping_address_id = %s
            WHERE order_id = %s
        """
        cursor.execute(update_order_query, (new_address_id, order_id))
        
        cnx.commit()
        
        return True
        
    except Error as err:
        print(f"Error updating shipping address for order {order_id}: {err}")
        if cnx:
            cnx.rollback()
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        if cnx:
            cnx.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def insert_order_item(product_name, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # Find Product_ID based on Product_Name
        cursor.execute("SELECT product_id, price FROM product WHERE product_name = %s", (product_name,))
        result = cursor.fetchone()
        if not result:
            print(f"Product {product_name} not found.")
            return -1

        product_id, price = result

        # Insert into Order_Item
        cursor.execute(
            "INSERT INTO Order_Item (Order_ID, Product_ID, Quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, quantity)
        )

        # Update Total_Amount in Order
        total_amount = quantity * price
        cursor.execute(
            "UPDATE `Order` SET Total_Amount = Total_Amount + %s WHERE Order_ID = %s",
            (total_amount, order_id)
        )

        cnx.commit()
        cursor.close()

        print(f"Inserted {quantity} of {product_name} into order {order_id}.")
        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        cnx.rollback()
        return -1

def insert_order(customer_id, shipping_method_id, shipping_address_id, promotion_id):
    try:
        cursor = cnx.cursor()

        # Calculate Shipping_Fee (based on Shipping_Method)
        cursor.execute(
            "SELECT Cost_per_product FROM Shipping_Method WHERE Shipping_Method_ID = %s",
            (shipping_method_id,)
        )
        shipping_fee = cursor.fetchone()[0]

        # Apply Promotion (if any)
        discount = 0
        if promotion_id:
            cursor.execute(
                "SELECT Discount_Type, Discount_Value, Minimum_Order FROM Promotion WHERE Promotion_ID = %s",
                (promotion_id,)
            )
            promo = cursor.fetchone()
            if promo:
                discount_type, discount_value, min_order = promo
                if discount_type == 'percentage':
                    discount = discount_value  # Will be applied as percentage later
                else:
                    discount = discount_value

        # Insert new Order
        cursor.execute(
            """
            INSERT INTO `Order` (Customer_ID, Payment_Method_ID, Shipping_Method_ID, Shipping_Address_ID, Promotion_ID,
            Order_Date, Total_Amount, Shipping_Fee, Discount, Payment_Status, Order_Status, Estimated_Delivery_Date)
            VALUES (%s, %s, %s, %s, %s, NOW(), 0.00, %s, %s, 'pending', 'Pending', DATE_ADD(NOW(), INTERVAL 3 DAY))
            """,
            (customer_id, 1, shipping_method_id, shipping_address_id, promotion_id, shipping_fee, discount)
        )

        order_id = cursor.lastrowid
        cnx.commit()
        cursor.close()

        return order_id

    except mysql.connector.Error as err:
        print(f"Error inserting order: {err}")
        cnx.rollback()
        return -1

def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)",
        (order_id, status)
    )
    cursor.execute(
        "UPDATE `Order` SET Order_Status = %s WHERE Order_ID = %s",
        (status, order_id)
    )
    cnx.commit()
    cursor.close()

def get_total_order_price(order_id):
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT Total_Amount, Shipping_Fee, Discount, Promotion_ID FROM `Order` WHERE Order_ID = %s",
        (order_id,)
    )
    result = cursor.fetchone()
    if result:
        total_amount, shipping_fee, discount, promotion_id = result
        if promotion_id:
            cursor.execute(
                "SELECT Discount_Type, Discount_Value FROM Promotion WHERE Promotion_ID = %s",
                (promotion_id,)
            )
            promo = cursor.fetchone()
            if promo and promo[0] == 'percentage':
                discount = (total_amount * promo[1]) / 100
        final_amount = total_amount + shipping_fee - discount
        cursor.close()
        return final_amount
    cursor.close()
    return 0

def get_next_order_id():
    cursor = cnx.cursor()
    cursor.execute("SELECT MAX(Order_ID) FROM `Order`")
    result = cursor.fetchone()[0]
    cursor.close()
    return (result + 1) if result else 1

def get_order_status(order_id):
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT Order_Status FROM `Order` WHERE Order_ID = %s",
        (order_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def search_products(category=None, brand=None):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT 
                p.product_id as id,
                p.product_name as name,
                p.description,
                p.price,
                pc.category_name as category,
                p.stock_quantity as stock,
                COALESCE(AVG(r.rating), 4.5) as rating
            FROM product p
            JOIN product_category pc ON p.category_id = pc.category_id
            LEFT JOIN review r ON p.product_id = r.product_id
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND pc.category_name = %s"
            params.append(category)
        
        query += " GROUP BY p.product_id, p.product_name, p.description, p.price, pc.category_name, p.stock_quantity"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": row[3],
                "category": row[4],
                "stock": row[5],
                "rating": float(row[6])
            }
            for row in results
        ]
        
    except Exception as e:
        print(f"Error searching products: {e}")
        return []
    finally:
        cursor.close()
        
def get_product_details(product_name):
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT p.Product_Name, p.Price, p.Description, p.Specifications, p.Stock_Quantity, b.Brand_Name, pc.Category_Name
        FROM Product p
        JOIN Brand b ON p.Brand_ID = b.Brand_ID
        JOIN Product_Category pc ON p.Category_ID = pc.Category_ID
        WHERE p.Product_Name = %s
        """,
        (product_name,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result

def get_active_promotions():
    cursor = cnx.cursor()
    cursor.execute(
        """
        SELECT Coupon_Code, Description, Discount_Type, Discount_Value, Minimum_Order
        FROM Promotion
        WHERE Status = 'active' AND Start_Date <= NOW() AND End_Date >= NOW()
        """
    )
    results = cursor.fetchall()
    cursor.close()
    return results

def get_promotion_by_code(coupon_code):
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT Promotion_ID, Discount_Type, Discount_Value FROM Promotion WHERE Coupon_Code = %s",
        (coupon_code,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result

def insert_review(product_name, customer_id, rating, comment):
    if not product_name:
        raise ValueError("Product name cannot be None or empty")
    cursor = cnx.cursor()
    
    try:
        # Lấy Product_ID từ product name
        cursor.execute(
            "SELECT Product_ID FROM Product WHERE Product_Name = %s",
            (product_name,)
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Product {product_name} not found in database")
        product_id = result[0]
        
        # Insert review và trả về review_id bằng RETURNING clause (PostgreSQL)
        cursor.execute(
            """
            INSERT INTO Review (Product_ID, Customer_ID, Rating, Comment, Review_Date)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING Review_ID
            """,
            (product_id, customer_id, rating, comment)
        )
        
        # Lấy review_id từ RETURNING clause
        result = cursor.fetchone()
        if not result:
            raise Exception("Failed to retrieve review_id from database")
        review_id = result[0]
        
        cnx.commit()
        return review_id
        
    except Exception as e:
        cnx.rollback()  # Rollback nếu có lỗi
        raise e
    finally:
        cursor.close()

def get_unreviewed_products(customer_id):
    try:
        cursor = cnx.cursor()
        query = """
            SELECT DISTINCT p.product_name, p.price, b.brand_Name, pc.category_name
            FROM product p
            JOIN order_item oi ON p.product_id = oi.product_id
            JOIN "Order" o ON oi.order_id = o.order_id
            JOIN product_category pc ON p.category_id = pc.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            LEFT JOIN review r ON p.product_id = r.product_id AND r.customer_id = %s
            WHERE o.customer_id = %s AND r.review_id IS NULL
        """
        cursor.execute(query, (customer_id, customer_id))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database error in get_unreviewed_products: {e}")
        return []
    
def delete_review_by_id(review_id):
    print (f"Attempting to delete review with ID: {review_id}")
    cursor = cnx.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM review WHERE review_id = %s",
            (review_id,)
        )
        
        deleted_count = cursor.rowcount
        cnx.commit()
        cursor.close()
        
        return deleted_count
        
    except Exception as e:
        cursor.close()
        raise e