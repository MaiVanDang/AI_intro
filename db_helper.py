import mysql.connector
from mysql.connector import Error

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'A1234567bv@',
    'database': 'ShopDB'
}

# Global connection
cnx = None

def init_db_connection():
    global cnx
    try:
        cnx = mysql.connector.connect(**db_config)
        print("Database connection established successfully!")
    except Error as err:
        print(f"Error connecting to database: {err}")
        cnx = None

# Initialize connection
init_db_connection()

def get_customer_orders(customer_id=None, customer_name=None):
    """
    Fetch all orders for a customer by ID or Name.
    Returns a list of dictionaries containing order details.
    """
    if not cnx:
        init_db_connection()
        if not cnx:
            return []

    try:
        cursor = cnx.cursor(dictionary=True)
        if customer_id:
            query = """

                SELECT 
                o.Order_ID,
                 GROUP_CONCAT(p.Product_Name) AS Product_Names,
                 o.Total_Amount,
                pm.Method_Name AS Payment_Method,
                o.Order_Status
                FROM `Order` o
                JOIN Order_Item oi ON o.Order_ID = oi.Order_ID
                JOIN Product p ON oi.Product_ID = p.Product_ID
                JOIN Payment_Method pm ON o.Payment_Method_ID = pm.Payment_Method_ID
                JOIN Customer c ON o.Customer_ID = c.Customer_ID
                WHERE c.Customer_ID = %s
                GROUP BY o.Order_ID, o.Total_Amount, pm.Method_Name, o.Order_Status
                ORDER BY o.Order_Date DESC;

            """
            cursor.execute(query, (customer_id,))
        elif customer_name:
            query = """
                
                SELECT 
                o.Order_ID,
                p.Product_Name,
                pm.Method_Name AS Payment_Method,
                o.Order_Date,
                o.Order_Status
                FROM `Order` o
                JOIN Order_Item oi ON o.Order_ID = oi.Order_ID
                JOIN Product p ON oi.Product_ID = p.Product_ID
                JOIN Payment_Method pm ON o.Payment_Method_ID = pm.Payment_Method_ID
                JOIN Customer c ON o.Customer_ID = c.Customer_ID
                WHERE c.Name LIKE %s
                ORDER BY o.Order_Date DESC
                
            """
            cursor.execute(query, (f"%{customer_name}%",))
        else:
            return []

        orders = cursor.fetchall()
        cursor.close()
        return orders
    except Error as err:
        print(f"Error fetching customer orders: {err}")
        return []
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
            SELECT COUNT(*) FROM `Order`
            WHERE Order_ID = %s AND Order_Status = 'processing'
        """
        cursor.execute(check_query, (order_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.close()
            return False

        # Delete from Order_Item first (due to foreign key constraint)
        cursor.execute("DELETE FROM Order_Item WHERE Order_ID = %s", (order_id,))
        # Delete from Order
        cursor.execute("DELETE FROM `Order` WHERE Order_ID = %s", (order_id,))

        cnx.commit()
        cursor.close()
        return True
    except Error as err:
        print(f"Error deleting order {order_id}: {err}")
        cnx.rollback()
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
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

    try:
        cursor = cnx.cursor()
        # Check if the order exists, has status 'processing', and belongs to the customer
        check_query = """
            SELECT COUNT(*) FROM `Order`
            WHERE Order_ID = %s AND Customer_ID = %s AND Order_Status = 'processing'
        """
        cursor.execute(check_query, (order_id, customer_id))
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.close()
            return False

        # Insert new shipping address
        insert_address_query = """
            INSERT INTO Shipping_Address (Customer_ID, Receiver_Name, Receiver_Phone, Country, City, Province_State, Postal_Code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_address_query, (customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code))
        cnx.commit()

        # Get the ID of the newly inserted address
        new_address_id = cursor.lastrowid

        # Update Order with the new Shipping_Address_ID
        update_order_query = """
            UPDATE `Order`
            SET Shipping_Address_ID = %s
            WHERE Order_ID = %s
        """
        cursor.execute(update_order_query, (new_address_id, order_id))
        cnx.commit()

        cursor.close()
        return True
    except Error as err:
        print(f"Error updating shipping address for order {order_id}: {err}")
        cnx.rollback()
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        cnx.rollback()
        return False