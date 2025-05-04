from venv import logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper

app = FastAPI()

# Global dictionary to track in-progress orders per session
inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = payload.get('session', 'unknown_session')

    if intent == "search.by.brand - context: ongoing-order":
        return search_by_brand(parameters)
    
    if intent == "search.by.price - context: ongoing-order":
        return search_by_price(parameters)
    
    if intent == "show.product.detail.by.id : context: ongoing-order":
        return search_by_id(parameters)
    
    if intent == "choose.cheapest.product - context: ongoing-order":
        return choose_cheapest_product(parameters)

    if intent == "confirm.product.order : context: ongoing-order":
        return confirm_order(parameters, session_id)
    elif intent == "Update.order : context: edit-order":
            return update_order(parameters, session_id)
    
    if intent =="user.confirm_checkout : context: ongoing-order":
        return proceed_to_checkout(parameters, session_id)
    
    if intent =="apply-coupon-code : context: ongoing-applyCode":
        return apply_coupon_code(parameters, session_id)

def search_by_brand(parameters: dict):
    brand_name_item = parameters["brand-name-item"]
    products = db_helper.get_list_products_by_brand(brand_name_item)

    if products:
        response_text = "id    product_name\n"
        for prod_id, prod_name in products:
            response_text += f"{prod_id:<5} {prod_name}\n"
        return JSONResponse(content={"fulfillmentText": response_text.strip()})
    else:
        return JSONResponse(content={"fulfillmentText": f"No product found for brand '{brand_name_item}'."})

def search_by_price(parameters: dict):
    brand_name_item = parameters.get("brand-name-item", "")
    price_range = parameters.get("price-range", "")
    price = parameters.get("number")

    if price_range == "Under" and isinstance(price, (list, tuple)):
        price = price[0] 
    elif price_range == "Between" and (not isinstance(price, (list, tuple)) or len(price) != 2):
        return JSONResponse(content={"fulfillmentText": "Price range 'Between' requires two numbers."})

    products = db_helper.get_list_products_by_price(brand_name_item, price_range, price)

    if products:
        response_text = "id    product_name\n"
        for prod_id, prod_name in products:
            response_text += f"{prod_id:<5} {prod_name}\n"
        return JSONResponse(content={"fulfillmentText": response_text.strip()})
    else:
        return JSONResponse(content={"fulfillmentText": f"No product found for the given criteria."})

def search_by_id(parameters: dict):
    product_id = parameters.get("number")
    if isinstance(product_id, list) and len(product_id) > 0:
        product_id = product_id[0]
    if isinstance(product_id, float):
        product_id = int(product_id)

    if product_id:
        products = db_helper.get_list_products_by_id(product_id)
        if products:
            product = products[0]
            (
                product_name,
                product_description,
                price,
                specification,
                brand_name,
                brand_description,
                origin_country
            ) = product

            response_text = (
                f"Name: {product_name} - {product_description} "
                f"Price: ${price} "
                f"Brand: {brand_name} - {brand_description} from {origin_country}"
            )
            return JSONResponse(content={"fulfillmentText": response_text})
        else:
            return JSONResponse(content={"fulfillmentText": f"No product found for id '{product_id}'."})
    else:
        return JSONResponse(content={"fulfillmentText": "Product ID is required."})

def choose_cheapest_product(parameters: dict):
    product = db_helper.get_product_cheapest()
    if product:  
        (
            product_name,
            product_description,
            price,
            specification,
            brand_name,
            brand_description,
            origin_country
        ) = product

        response_text = (
            f"Name: {product_name} - {product_description} "
            f"Price: ${price} "
            f"Brand: {brand_name} - {brand_description} from {origin_country}"
        )
        return JSONResponse(content={"fulfillmentText": response_text})
    else:
        return JSONResponse(content={"fulfillmentText": "No product found."})

def confirm_order(parameters: dict, session_id: str):
    product_names = parameters.get("product-name", [])
    quantities = parameters.get("number-integer", [])

    if not product_names or not quantities or len(product_names) != len(quantities):
        return JSONResponse(content={"fulfillmentText": "Please provide matching product names and quantities."})

    confirm_lines = []
    not_found_lines = []
    insufficient_stock_lines = []

    order_list = []

    for product_name, quantity in zip(product_names, quantities):
        products = db_helper.get_products_by_name(product_name)
        if not products:
            not_found_lines.append(f"- No products found with the name '{product_name}'.")
            continue

        for product in products:
            (
                product_id,
                name,
                product_description,
                price,
                specification,
                brand_name,
                origin_country,
                stock_quantity
            ) = product

            # Convert stock_quantity to int if it's a string
            if isinstance(stock_quantity, str):
                stock_quantity = int(stock_quantity)
                
            # Convert quantity to int if it's a float
            if isinstance(quantity, float):
                quantity = int(quantity) 

            if stock_quantity < quantity:
                insufficient_stock_lines.append(
                    f"- {name} (ID: {product_id}) only has {stock_quantity} in store, but you requested {quantity}."
                )
                continue

            confirm_lines.append(
                f"- ID: {product_id}  Name: {name}  Quantity: {quantity}  "
                f"Price: ${price}  Brand: {brand_name} from {origin_country}"
            )
            order_list.append((product_id, quantity))

    # Save the confirmed items to session if any
    if session_id and order_list:
        inprogress_orders[session_id] = order_list

    if not confirm_lines:
        messages = []
        if not_found_lines:
            messages.append("Not found:\n" + "\n".join(not_found_lines))
        if insufficient_stock_lines:
            messages.append("Insufficient stock:\n" + "\n".join(insufficient_stock_lines))
        return JSONResponse(content={"fulfillmentText": "\n\n".join(messages)})

    confirm_text = "I would like to confirm your order as follows:\n"
    confirm_text += "\n".join(confirm_lines)

    if insufficient_stock_lines:
        confirm_text += "\n\nStock warnings:\n" + "\n".join(insufficient_stock_lines)
    if not_found_lines:
        confirm_text += "\n\nNot found:\n" + "\n".join(not_found_lines)

    confirm_text += "\n\n(If incorrect, re-enter in the format:Update Name: product_name - Quantity: number. If you add more products, please enter in the format: Add Name: product_name - Quantity: number.)"

    return JSONResponse(content={"fulfillmentText": confirm_text})

def update_order(parameters: dict, session_id: str) -> JSONResponse:
    
    product_ids = parameters.get("number", [])
    quantities = parameters.get("number-integer", [])
    state = parameters.get("state")
    
    logger.info(f"Updating order: product_ids={product_ids}, quantities={quantities}, session={session_id}")

    if not isinstance(product_ids, list):
        product_ids = [product_ids]
    if not isinstance(quantities, list):
        quantities = [quantities]

    if (not product_ids) or not quantities:
        return JSONResponse(content={"fulfillmentText": "Please provide ID and quantity for update."})
    
    if product_ids and len(product_ids) != len(quantities):
        return JSONResponse(content={"fulfillmentText": "Product ID and quantity do not match."})

    if session_id not in inprogress_orders:
        return JSONResponse(content={"fulfillmentText": "No pending orders found. Please create a new order first."})

    current_order = inprogress_orders[session_id]
    updated = False
    not_found_lines = []
    insufficient_stock_lines = []
    update_lines = []
    
    if product_ids and product_ids[0]:
        for product_id, quantity in zip(product_ids, quantities):
            try:
                product_id = int(product_id)
                products = db_helper.get_list_products_by_id(product_id)
                
                if not products:
                    not_found_lines.append(f"- No products found with ID '{product_id}'.")
                    continue

                for product in products:
                    # Dựa trên truy vấn SQL trong pgAdmin, thứ tự các cột là:
                    # 0: product_name
                    # 1: product_description
                    # 2: price
                    # 3: specifications
                    # 4: brand_name
                    # 5: stock_quantity
                    # 6: brand_description
                    # 7: origin_country
                    
                    product_name = product[0]
                    price = product[2]
                    stock_quantity = product[5]
                    brand_name = product[4]
                    origin_country = product[7]
                
                if isinstance(stock_quantity, str):
                    stock_quantity = int(stock_quantity)
                    
                if isinstance(quantity, float):
                    quantity = int(quantity)
                    
                if stock_quantity < quantity:
                    insufficient_stock_lines.append(
                        f"- {name} (ID: {product_id}) only has {stock_quantity} in store, but you requested {quantity}."
                    )
                    continue

                product_found = False
                for i, (current_id, current_quantity) in enumerate(current_order):
                    if current_id == product_id:
                        current_order[i] = (product_id, quantity)
                        update_lines.append(
                            f"- Updated: {product_name} (ID: {product_id}) - Quantity: {quantity}"
                        )
                        product_found = True
                        updated = True
                        break
                
                if not product_found:
                    current_order.append((product_id, quantity))
                    update_lines.append(
                        f"- New added: {product_name} (ID: {product_id}) - Quantity: {quantity}"
                    )
                    updated = True
            except ValueError:
                not_found_lines.append(f"- ID product '{product_id}' invalid.")

    if updated:
        inprogress_orders[session_id] = current_order
        logger.info(f"Updated order in session {session_id}: {current_order}")

    current_products = []
    for product_id, quantity in current_order:
        products = db_helper.get_list_products_by_id(product_id)
        if products:
            product = products[0]
            name = product[0]  # product_name
            price = product[2]  # price
            brand_name = product[4]  # brand_name
            origin_country = product[7]  # origin_country
            
            current_products.append({
                "id": product_id,
                "name": name,
                "quantity": quantity,
                "price": price,
                "brand": brand_name,
                "origin": origin_country
            })

    if not updated:
        messages = []
        if not_found_lines:
            messages.append("No product found:\n" + "\n".join(not_found_lines))
        if insufficient_stock_lines:
            messages.append("Not enough stock:\n" + "\n".join(insufficient_stock_lines))
        
        if messages:
            return JSONResponse(content={"fulfillmentText": "\n\n".join(messages)})
        else:
            return JSONResponse(content={"fulfillmentText": "No changes can be made to the order."})

    response_text = "Order updated:\n"
    response_text += "\n".join(update_lines)
    
    if insufficient_stock_lines:
        response_text += "\n\nInventory Alerts:\n" + "\n".join(insufficient_stock_lines)
    if not_found_lines:
        response_text += "\n\nNot found:\n" + "\n".join(not_found_lines)
    
    response_text += "\n\nCurrent orders:\n"
    for product in current_products:
        response_text += f"- ID: {product['id']}  Name: {product['name']}  Quantity: {product['quantity']}  "
        response_text += f"Price: ${product['price']}  brand: {product['brand']} from {product['origin']}\n"
    
    response_text += "\n(You can continue to update your order or confirm to complete.)"

    return JSONResponse(content={"fulfillmentText": response_text})

def proceed_to_checkout(parameters: dict, session_id: str):
    # 1. Lấy đơn hàng từ session
    order_list = inprogress_orders.get(session_id, [])

    if not order_list:
        return JSONResponse(content={"fulfillmentText": "You have not added any items to your cart yet."})

    total_amount = 0
    order_summary_lines = []

    # 2. Tính tổng tiền
    for product_id, quantity in order_list:
        products = db_helper.get_list_products_by_id(product_id)
        if not products:
            continue
        product = products[0]
        
        # Trích xuất thông tin sản phẩm từ tuple đúng cách
        product_name = product[0]
        price = product[2]
        brand_name = product[4]
        origin_country = product[7]

        # Nếu price là chuỗi, chuyển về float
        if isinstance(price, str):
            price = float(price)

        line_total = price * quantity
        total_amount += line_total

        order_summary_lines.append(
            f"- {product_name} x{quantity} (${price:.2f} each) = ${line_total:.2f} | Brand: {brand_name} from {origin_country}"
        )

    # 3. Tìm khuyến mãi thỏa điều kiện
    promotions = db_helper.get_valid_promotions(min_order=total_amount)

    if promotions:
        promo_lines = [
            f"- Code: {promo['coupon_code']} - {promo['description']} (min order: ${promo['minimum_order']})"
            for promo in promotions
        ]
        promotion_text = "\n\n🎁 Available promotions:\n" + "\n".join(promo_lines)
    else:
        promotion_text = "\n\n(There are currently no promotions available for your order.)"

    # 4. Trả phản hồi cho người dùng
    response_text = (
        f"🧾 Your current order total is: ${total_amount:.2f}\n"
        + "\n".join(order_summary_lines)
        + promotion_text
        + "\n\nPlease reply with the promotion code you want to apply or say 'No promotion'."
    )

    return JSONResponse(content={"fulfillmentText": response_text})

def apply_coupon_code(parameters: dict, session_id: str):
    coupon_code = parameters.get("coupon_code", "").strip().upper()
    order_list = inprogress_orders.get(session_id, [])

    if not coupon_code or not order_list:
        return JSONResponse(content={"fulfillmentText": "Invalid coupon or no items in your cart."})

    total_amount = 0
    for product_id, quantity in order_list:
        product = db_helper.get_list_products_by_id(product_id)
        if not product:
            continue
        product = product[0]
        price = float(product[2])
        total_amount += price * quantity

    promotion = db_helper.get_promotion_by_code(coupon_code)
    if not promotion:
        return JSONResponse(content={"fulfillmentText": f"Sorry, the code {coupon_code} is not valid."})

    promo_code, discount_value = promotion

    discount_amount = total_amount * (float(discount_value) / 100)

    total_after_discount = total_amount - discount_amount

    response_text = (
        f"Thanks! Your promo code has been applied. Order Summary:\n"
        f"Total before discount: ${total_amount:.2f}\n"
        f"Discount ({promo_code}): – ${discount_amount:.2f}\n"
        f"Total after discount: ${total_after_discount:.2f}\n\n"
        "Would you like to use your default address, or do you want to enter a new one?\n"
        "You can reply with: 'Use default address' or 'New address'."
    )

    return JSONResponse(content={"fulfillmentText": response_text})

# def use_default_shipping_address(session_id: str):
#
#     default_address = db_helper.get_default_address_by_session(session_id)

#     if not default_address:
#         return JSONResponse(content={"fulfillmentText": "Sorry, we couldn't find your default shipping address."})

#     response_text = (
#         "Got it! We'll use your default shipping address as follows:\n"
#         f"{default_address}\n\n"
#         "Please confirm if this is correct or say 'Change address' to provide a new one."
#     )

#     return JSONResponse(content={"fulfillmentText": response_text})

