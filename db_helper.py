import mysql.connector
global cnx

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sohyun280697.",
    database="ShopDB"
)

def insert_order_item(product_name, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # Find Product_ID based on Product_Name
        cursor.execute("SELECT Product_ID, Price FROM Product WHERE Product_Name = %s", (product_name,))
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
    query = """
        SELECT p.Product_Name, p.Price, b.Brand_Name, pc.Category_Name
        FROM Product p
        JOIN Product_Category pc ON p.Category_ID = pc.Category_ID
        JOIN Brand b ON p.Brand_ID = b.Brand_ID
        WHERE 1=1
    """
    params = []
    if category:
        query += " AND pc.Category_Name = %s"
        params.append(category)
    if brand:
        query += " AND b.Brand_Name = %s"
        params.append(brand)
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    return results

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
        "SELECT Promotion_ID, Discount_Type, Discount_Value, Minimum_Order FROM Promotion WHERE Coupon_Code = %s",
        (coupon_code,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result

def insert_review(product_name, customer_id, rating, comment):
    if not product_name:
        raise ValueError("Product name cannot be None or empty")
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT Product_ID FROM Product WHERE Product_Name = %s",
        (product_name,)
    )
    result = cursor.fetchone()
    if not result:
        cursor.close()
        raise ValueError(f"Product {product_name} not found in database")
    product_id = result[0]
    cursor.execute(
        """
        INSERT INTO Review (Product_ID, Customer_ID, Rating, Comment, Review_Date)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (product_id, customer_id, rating, comment)
    )
    cnx.commit()
    cursor.close()

def get_unreviewed_products(customer_id):
    cursor = cnx.cursor()
    query = """
        SELECT DISTINCT p.Product_Name, p.Price, b.Brand_Name, pc.Category_Name
        FROM Product p
        JOIN Order_Item oi ON p.Product_ID = oi.Product_ID
        JOIN `Order` o ON oi.Order_ID = o.Order_ID
        JOIN Product_Category pc ON p.Category_ID = pc.Category_ID
        JOIN Brand b ON p.Brand_ID = b.Brand_ID
        LEFT JOIN Review r ON p.Product_ID = r.Product_ID AND r.Customer_ID = %s
        WHERE o.Customer_ID = %s AND r.Review_ID IS NULL
    """
    cursor.execute(query, (customer_id, customer_id))
    results = cursor.fetchall()
    cursor.close()
    return results