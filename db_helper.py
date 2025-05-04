import psycopg2
global cnx

cnx = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="admin",
    database="shopDB"
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

def get_promotion_by_code(coupon_code: str):
    cursor = cnx.cursor()
    try:
        query = """
            SELECT coupon_code, discount_value
            FROM promotion
            WHERE coupon_code = %s
        """
        cursor.execute(query, (coupon_code,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[ERROR] get_promotion_by_code failed: {e}")
        return None
    finally:
        cursor.close()

# def get_default_address_by_session(session_id: str):
#     cursor = cnx.cursor()
#     try:
#         query = """
#             SELECT address_line
#             FROM user_session us
#             JOIN user u ON us.user_id = u.user_id
#             WHERE us.session_id = %s
#         """
#         cursor.execute(query, (session_id,))
#         result = cursor.fetchone()
#         return result[0] if result else None
#     except Exception as e:
#         print(f"[ERROR] get_default_address_by_session failed: {e}")
#         return None
#     finally:
#         cursor.close()
