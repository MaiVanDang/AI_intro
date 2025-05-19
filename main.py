from typing import Union
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper

app = FastAPI()


def extract_session_id(context_name: str) -> str:
    """
    Extract session ID from Dialogflow context name.
    Example: projects/<project>/agent/sessions/<session_id>/contexts/<context>
    """
    try:
        return context_name.split('/sessions/')[1].split('/')[0]
    except IndexError:
        return ""
    
@app.post("/")
async def handle_request(request: Request):
    """
    Handle incoming requests from Dialogflow.
    """
    try:
        payload = await request.json()
        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        output_contexts = payload['queryResult']['outputContexts']
        session_id = extract_session_id(output_contexts[0]["name"])

        intent_handler_dict = {
            'showlist.confirm - context: ongoing-tracking': show_customer_orders,
            'delete - context: ongoing-tracking': delete_order_handler,
            'update.address.confirm - context: ongoing-tracking':update_shipping_address_handler,
          
        }

        if intent not in intent_handler_dict:
            return JSONResponse(content={
                "fulfillmentText": "Sorry, I don't understand this request."
            })

        return intent_handler_dict[intent](parameters, session_id)
    except Exception as e:
        print(f"Error handling request: {e}")
        return JSONResponse(content={
            "fulfillmentText": "An error occurred while processing your request."
        })

def show_customer_orders(parameters: dict, session_id: str):
    """
    Handle 'show customer orders' intent to display all orders for a customer.
    """
    customer_id = parameters.get('number')
    customer_name = parameters.get('person')

    # Convert customer_id to int if provided
    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            customer_id = None

    # Fetch orders using db_helper
    orders = db_helper.get_customer_orders(customer_id=customer_id, customer_name=customer_name)

    if not orders:
        fulfillment_text = "No orders found for this customer. Please check the ID or name and try again."
    else:
        # Format the orders into a readable string
        # order_details = []
        # for order in orders:
        #     order_str = (f"Order ID: {order['Order_ID']}, "
        #                  f"Date: {order['Order_Date']}, "
        #                  f"Total: ${order['Total_Amount']}, "
        #                  f"Status: {order['Order_Status']}")
        #     order_details.append(order_str)
        order_details = []
        for order in orders:
            products = order['Product_Names'] if order['Product_Names'] else "No products"
            order_str = (
                 f"Order ID: {order['Order_ID']}, "
                 f"Products: {products}, "
                 f"Total: ${order['Total_Amount']:,.2f}, "
                 f"Payment Method: {order['Payment_Method']}, "
                 f"Status: {order['Order_Status']}")
            order_details.append(order_str)
        fulfillment_text = "Here are your orders:\n" + "\n".join(order_details)
        # Assuming orders is the result from get_customer_orders
    
    return JSONResponse(content={"fulfillmentText": fulfillment_text})



def delete_order_handler(parameters: dict, session_id: str):
    """
    Handle 'delete order' intent to delete a specific order by Order_ID if its status is 'processing'.
    """
    order_id = parameters.get('order_id')

    # Validate input
    if not order_id:
        fulfillment_text = "Please provide an Order ID."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    try:
        order_id = int(order_id)
    except ValueError:
        fulfillment_text = "Invalid Order ID. Please provide a valid number."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    # Delete the order
    success = db_helper.delete_order(order_id)
    if success:
        fulfillment_text = f"Successfully deleted Order ID {order_id}."
    else:
        fulfillment_text = f"Failed to delete Order ID {order_id}. It may not exist or the order status is not 'processing'."

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def update_shipping_address_handler(parameters: dict, session_id: str):
    """
    Handle 'update shipping address' intent to update the shipping address for a specific order.
    """
    order_id = parameters.get('order_id')
    customer_id = parameters.get('number')
    # receiver_name = parameters.get('person')
    receiver_name = parameters.get('person', {}).get('name') if isinstance(parameters.get('person'), dict) else parameters.get('person')
    receiver_phone = parameters.get('phone-number')
    country = parameters.get('geo-country')
    city = parameters.get('geo-city')
    province_state = parameters.get('province')
    postal_code = parameters.get('country_code')

    # Validate inputs
    required_fields = {
        'Order ID': order_id,
        'Customer ID': customer_id,
        'Receiver Name': receiver_name,
        'Receiver Phone': receiver_phone,
        'Country': country,
        'City': city,
        'Province/State': province_state,
        'Postal Code': postal_code
    }
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        fulfillment_text = f"Please provide all required fields: {', '.join(missing_fields)}."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    try:
        order_id = int(order_id)
        customer_id = int(customer_id)
    except ValueError:
        fulfillment_text = "Invalid Order ID or Customer ID. Please provide valid numbers."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    # Update the shipping address
    success = db_helper.update_shipping_address(
        order_id, customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code
    )
    if success:
        fulfillment_text = f"Successfully updated shipping address for Order ID {order_id}."
    else:
        fulfillment_text = (f"Failed to update shipping address for Order ID {order_id}. "
                           "It may not exist, not belong to the customer, or its status is not 'processing'.")

    return JSONResponse(content={"fulfillmentText": fulfillment_text})