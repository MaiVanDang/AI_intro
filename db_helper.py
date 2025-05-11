import psycopg2
from datetime import datetime, timedelta

global cnx

cnx = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="huyentrang",
    database="ShopDB"
)

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
            WHERE p.product_name LIKE %s;
        """
        cursor.execute(query, (f"%{product_name}%",))
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