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

# Cập nhật hàm get_promotion_by_code để trả về promotion_id
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

# Thêm hàm lưu địa chỉ mới
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

# Cập nhật hàm get_payment_methods để trả về thêm payment_method_id
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
                WHERE c.name ILIKE 'Emma Wang'
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
        print(f"An error occurred: {e}")
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