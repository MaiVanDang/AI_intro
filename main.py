from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import db_helper
import generic_helper

import logging
logger = logging.getLogger(__name__)

inprogress_orders = {}
customer_id = 1


def safe_extract_session_id(context_name: str) -> str:
    try:
        if generic_helper:
            return generic_helper.extract_session_id(context_name)
        else:
            parts = context_name.split('/')
            for part in parts:
                if 'sessions' in part:
                    return part.split('sessions/')[-1].split('/')[0]
            return "default_session"
    except Exception as e:
        return "default_session"
    
def create_response(text: str, contexts: Optional[list] = None) -> JSONResponse:
    """Create a standardized response for Dialogflow"""
    response = {
        "fulfillmentText": text,
        "source": "shopdb-chatbot"
    }
    
    if contexts:
        response["outputContexts"] = contexts
    
    return JSONResponse(content=response)

# Intent handler functions
def handle_welcome(parameters: dict, contexts: list, session_id: str):
    """Handle welcome intent"""
    return create_response(
        "Xin chào! Tôi là trợ lý ảo của ShopDB. "
        "Tôi có thể giúp bạn:\n"
        "• Tìm kiếm sản phẩm theo thương hiệu hoặc giá\n"
        "• Tra cứu thông tin đơn hàng\n"
        "• Hỗ trợ đặt hàng và thanh toán\n"
        "• Quản lý thông tin khách hàng\n\n"
        "Bạn cần hỗ trợ gì hôm nay?"
    )

def handle_order_inquiry(parameters: dict, contexts: list, session_id: str):
    """Handle order inquiry"""
    return create_response(
        "Để tra cứu đơn hàng, bạn có thể:\n"
        "• Cung cấp ID khách hàng\n"
        "• Cung cấp tên khách hàng\n"
        "• Cung cấp email hoặc số điện thoại\n\n"
        "Ví dụ: 'Tôi muốn xem đơn hàng của khách hàng ID 123'"
    )

def convert_decimals_to_floats(product_list):
    """Convert decimal prices to floats for JSON serialization"""
    try:
        return [
            (item[0], float(item[1]), item[2], item[3])
            for item in product_list
        ]
    except Exception as e:
        logger.error(f"Error converting decimals: {e}")
        return product_list

async def handle_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    intent_handler_dict = {
        'search.by.brand - context: ongoing-order': search_by_brand,
        'search.by.price - context: ongoing-order': search_by_price,
        'show.product.detail.by.id : context: ongoing-order': search_by_id,
        'choose.cheapest.product - context: ongoing-order': choose_cheapest_product,
        'confirm.product.order : context: ongoing-order': confirm_order,
        'Update.order : context: edit-order': update_order,
        'user.confirm_checkout : context: ongoing-order': proceed_to_checkout,
        'apply-coupon-code : context: ongoing-applyCode': apply_coupon_code,
        'identify-customer - context: ongoing-identify': identify_customer,
        'confirm-customer-info - context: ongoing-confirm-info': confirm_customer_info,
        'use-default-address - context: ongoing-address': use_default_address,
        'new-shipping-address - context: ongoing-address': request_new_shipping_address,
        'provide-new-shipping-address - context: ongoing-new-address': process_new_shipping_address,
        'confirm-new-address - context: ongoing-new-address': confirm_new_address,
        'confirm-shipping-method - context: ongoing-shipping-method': confirm_shipping_method,
        'select-payment-method - context: ongoing-payment-method': select_payment_method,
        'confirm-order - context: ongoing-order-confirmation': confirm_order_placement,
        'cancel-order - context: ongoing-order-confirmation': cancel_order,
        'remove-items - context: ongoing-order-confirmation': remove_items,
        'end-conversation - context: ongoing-order-complete': end_conversation,
        'showlist.confirm - context: ongoing-tracking': show_customer_orders,
        'delete - context: ongoing-tracking': delete_order_handler,
        'update.address.confirm - context: ongoing-tracking': update_shipping_address_handler,
        'submit_review_start': submit_review_start,
        'submit_review_product_confirm': submit_review_product_confirm,
        'submit_review_details_collect': submit_review_details_collect,
        'submit_review_edit': submit_review_edit,
        'submit_review_submit': submit_review_submit,
        'submit_review_end': submit_review_end,
        'submit_review_cancel': submit_review_cancel,
        'submit_review_select_different_product': submit_review_select_different_product,
        'submit_review_continue': submit_review_continue
    }

    if intent in intent_handler_dict:
        return intent_handler_dict[intent](parameters, output_contexts, session_id)
    else:
        return JSONResponse(content={
            "fulfillmentText": f"Sorry, I don't understand the intent '{intent}'. Please try again."
        })
    
def handle_customer_inquiry(parameters: dict, contexts: list, session_id: str):
    """Handle customer inquiry"""
    return create_response(
        "Tôi có thể giúp bạn tìm kiếm thông tin khách hàng theo:\n"
        "• Email\n"
        "• Số điện thoại\n"
        "• ID khách hàng\n\n"
        "Bạn có thể cung cấp thông tin nào để tôi tìm kiếm?"
    )

def search_by_brand(parameters: dict, output_contexts, session_id):
    brand_name_item = parameters["brand-name-item"]
    products = db_helper.get_list_products_by_brand(brand_name_item)

    if products:
        response_text = "id    product_name\n"
        for prod_id, prod_name in products: 
            response_text += f"{prod_id:<5} {prod_name}\n"
        return JSONResponse(content={"fulfillmentText": response_text.strip()})
    else:
        return JSONResponse(content={"fulfillmentText": f"No product found for brand '{brand_name_item}'."})

def search_by_price(parameters: dict, output_contexts, session_id):
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

def search_by_id(parameters: dict, output_contexts, session_id):
    product_id = parameters.get("number-integer")
    print(f"Received product_id: {product_id}")
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
                stock_quantity,
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

def choose_cheapest_product(parameters: dict, output_contexts, session_id):
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

def confirm_order(parameters: dict, output_contexts, session_id: str):
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

            if isinstance(stock_quantity, str):
                stock_quantity = int(stock_quantity)
                
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

    if session_id and order_list:
        if session_id in inprogress_orders:
            # Cập nhật order hiện tại
            current_order = inprogress_orders[session_id]
            if "order_list" in current_order:
                # Merge với order cũ
                existing_orders = dict(current_order["order_list"])
                for product_id, quantity in order_list:
                    if product_id in existing_orders:
                        existing_orders[product_id] += quantity
                    else:
                        existing_orders[product_id] = quantity
                current_order["order_list"] = list(existing_orders.items())
            else:
                current_order["order_list"] = order_list
            inprogress_orders[session_id] = current_order
        else:
            # Tạo order mới
            inprogress_orders[session_id] = {
                "order_list": order_list,
                "customer_info": None,
                "shipping_address": None
            }

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

def update_order(parameters: dict, output_contexts, session_id: str) -> JSONResponse:
    product_names = parameters.get("product-name", [])
    quantities = parameters.get("number-integer", [])
    
    logger.info(f"Updating order: product_name={product_names}, quantities={quantities}, session={session_id}")

    # Chuẩn hoá dữ liệu đầu vào
    if not isinstance(product_names, list):
        product_names = [product_names]
    if not isinstance(quantities, list):
        quantities = [quantities]

    if not product_names or not quantities:
        return JSONResponse(content={"fulfillmentText": "Please provide product name and quantity for update."})
    
    if len(product_names) != len(quantities):
        return JSONResponse(content={"fulfillmentText": "Product name and quantity do not match."})

    if session_id not in inprogress_orders:
        return JSONResponse(content={"fulfillmentText": "No pending orders found. Please create a new order first."})

    current_order = inprogress_orders[session_id]["order_list"]
    updated = False
    not_found_lines = []
    insufficient_stock_lines = []
    update_lines = []

    for name, qty in zip(product_names, quantities):
        try:
            qty = int(qty)
            if qty <= 0:  # Validate số lượng
                not_found_lines.append(f"- Invalid quantity {qty} for '{name}'.")
                continue
                
            products = db_helper.get_products_by_name(name)
            if not products:
                not_found_lines.append(f"- No products found with name '{name}'.")
                continue

            product = products[0]
            product_id = product[0] 
            product_name = product[1]
            product_description = product[2]
            price = product[3]
            product_specification = product[4]
            brand_name = product[5]
            origin_country = product[6]
            stock = int(product[7])

            if stock < qty:
                insufficient_stock_lines.append(
                    f"- {product_name} (ID: {product_id}) only has {stock} in stock, but you requested {qty}."
                )
                continue

            #So sánh đúng kiểu dữ liệu
            for i, (curr_id, _) in enumerate(current_order):
                if curr_id == product_id:
                    current_order[i] = (product_id, qty)
                    update_lines.append(f"- Updated: {product_name} (ID: {product_id}) - Quantity: {qty}")
                    updated = True
                    break
            else:
                current_order.append((product_id, qty))
                update_lines.append(f"- New added: {product_name} (ID: {product_id}) - Quantity: {qty}")
                updated = True

        except ValueError:  #Handle int conversion error
            not_found_lines.append(f"- Invalid quantity '{qty}' for '{name}'.")
        except Exception as e:
            logger.error(f"Error updating product '{name}': {e}")
            not_found_lines.append(f"- Error processing '{name}'.")

    # Cập nhật nếu có thay đổi
    if updated:
        inprogress_orders[session_id]["order_list"] = current_order
        logger.info(f"Updated order in session {session_id}: {current_order}")

    #Hiển thị đơn hàng đúng cách
    current_products = []
    for product_id, quantity in current_order:  #Đặt tên biến đúng
        products = db_helper.get_list_products_by_id(product_id)  #Tìm theo ID
        if products:
            product = products[0] if isinstance(products, list) else products
            current_products.append({
                "id": product[0],
                "name": product[1],  # Lấy tên từ DB
                "quantity": quantity,
                "price": product[3],
                "brand": product[5],
                "origin": product[6]
            })

    # Tạo thông điệp phản hồi (giữ nguyên phần này)
    if not updated:
        messages = []
        if not_found_lines:
            messages.append("No product found:\n" + "\n".join(not_found_lines))
        if insufficient_stock_lines:
            messages.append("Not enough stock:\n" + "\n".join(insufficient_stock_lines))
        return JSONResponse(content={"fulfillmentText": "\n\n".join(messages) or "No changes can be made to the order."})

    response_text = "Order updated:\n" + "\n".join(update_lines)
    if insufficient_stock_lines:
        response_text += "\n\nInventory Alerts:\n" + "\n".join(insufficient_stock_lines)
    if not_found_lines:
        response_text += "\n\nNot found:\n" + "\n".join(not_found_lines)

    response_text += "\n\nCurrent orders:\n"
    for p in current_products:
        response_text += (
            f"- ID: {p['id']}  Name: {p['name']}  Quantity: {p['quantity']}  "
            f"Price: ${p['price']}  Brand: {p['brand']} from {p['origin']}\n"
        )

    response_text += "\n(You can continue to update your order or confirm to complete.)"

    return JSONResponse(content={"fulfillmentText": response_text})

def proceed_to_checkout(parameters: dict, output_contexts, session_id: str):

    # Kiểm tra session tồn tại như code mẫu
    if session_id not in inprogress_orders:
        fulfillment_text = "You have not added any items to your cart yet."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})
    
    session_data = inprogress_orders.get(session_id, {})
    order_list = session_data.get("order_list", [])

    if not order_list:
        return JSONResponse(content={"fulfillmentText": "You have not added any items to your cart yet."})

    total_amount = 0
    order_summary_lines = []

    for product_id, quantity in order_list:
        products = db_helper.get_list_products_by_id(product_id)
        if not products:
            continue
        product = products[0]
        
        product_name = product[0]
        price = product[2]
        brand_name = product[4]
        origin_country = product[7]

        if isinstance(price, str):
            price = float(price)

        line_total = price * quantity
        total_amount += line_total

        order_summary_lines.append(
            f"- {product_name} x{quantity} (${price:.2f} each) = ${line_total:.2f}\n  Brand: {brand_name} from {origin_country}"
        )

    promotions = db_helper.get_valid_promotions(min_order=total_amount)

    if promotions:
        promo_lines = []
        promo_lines.append("═══════════════════════════════════")
        promo_lines.append("           ORDER SUMMARY")
        promo_lines.append("═══════════════════════════════════")
        promo_lines.append("")
        for promo in promotions:
            promo_lines.append(f"- Code: {promo['coupon_code']} - {promo['description']}")
            promo_lines.append(f"  (min order: ${promo['minimum_order']})")
        promotion_text = "\n\n🎁 Available promotions:\n" + "\n".join(promo_lines)
    else:
        promotion_text = "\n\n(There are currently no promotions available for your order.)"

    response_text = f"🧾 Your current order total is: ${total_amount:.2f}\n\n" + "\n".join(order_summary_lines) + promotion_text + "\n\nPlease reply with the promotion code you want to apply or say 'No promotion'."

    return JSONResponse(content={"fulfillmentText": response_text})

def apply_coupon_code(parameters: dict, output_contexts, session_id: str):
    coupon_code = parameters.get("coupon_code", "").strip().upper()
    session_data = inprogress_orders.get(session_id, {})
    order_list = session_data.get("order_list", [])

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

    # Sửa lại: Lấy coupon_code và discount_value từ promotion
    _, promo_code, discount_value = promotion  # promotion trả về (promotion_id, coupon_code, discount_value)

    discount_amount = total_amount * (float(discount_value) / 100)
    total_after_discount = total_amount - discount_amount

    # Lưu thông tin discount vào session
    inprogress_orders[session_id]["discount"] = {
        "promo_code": promo_code,
        "discount_amount": discount_amount
    }

    response_text = (
        f"Thanks! Your promo code has been applied. Order Summary:\n"
        f"Total before discount: ${total_amount:.2f}\n"
        f"Discount ({promo_code}): – ${discount_amount:.2f}\n"
        f"Total after discount: ${total_after_discount:.2f}\n\n"
        "Please provide your email or phone number to identify yourself (e.g., 'My email is john.doe@example.com' or 'My phone is 1234567890')."
    )

    return JSONResponse(content={"fulfillmentText": response_text})

def identify_customer(parameters: dict, output_contexts, session_id: str):
    email = parameters.get("email", "").strip()
    phone = parameters.get("phone-number", "").strip()

    if not email and not phone:
        return JSONResponse(content={
            "fulfillmentText": "Please provide your email or phone number to identify yourself (e.g., 'My email is john.doe@example.com' or 'My phone is 1234567890')."
        })

    customer = db_helper.get_customer_by_email_or_phone(email, phone)
    if customer:
        customer_id = customer[0]
        customer_info = db_helper.get_customer_info(customer_id)
        if customer_info and len(customer_info) >= 3:
            customer_text = (
                f"Email: {customer_info[1]}\n"
                f"Phone: {customer_info[2]}"
            )
            if session_id not in inprogress_orders:
                inprogress_orders[session_id] = {"order_list": [], "customer_info": None, "shipping_address": None}
            inprogress_orders[session_id]["customer_info"] = {"email": customer_info[1], "phone": customer_info[2]}
            return JSONResponse(content={
                "fulfillmentText": f"Thank you! Your information has been found:\n{customer_text}\nPlease confirm if this is correct. Reply with 'Yes, that’s correct' or 'No, that’s wrong'."
            })
    return JSONResponse(content={
        "fulfillmentText": "Customer not found. Please provide a valid email or phone number (e.g., 'My email is john.doe@example.com' or 'My phone is 1234567890')."
    })

def confirm_customer_info(parameters: dict, output_contexts, session_id: str):
    confirmation = parameters.get("confirmation", "").lower()

    if session_id not in inprogress_orders or not inprogress_orders[session_id].get("customer_info"):
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please provide your email or phone number again to identify yourself."
        })

    email = inprogress_orders[session_id]["customer_info"]["email"]
    phone = inprogress_orders[session_id]["customer_info"]["phone"]

    customer = db_helper.get_customer_by_email_or_phone(email, phone)
    if not customer:
        return JSONResponse(content={
            "fulfillmentText": "Customer not found. Please provide a valid email or phone number."
        })

    customer_id = customer[0]
    if "yes" in confirmation or "correct" in confirmation:
        default_address = db_helper.get_default_address_by_customer(customer_id)
        if default_address:
            address_text = (
                f"Receiver Name: {default_address[1]}\n"
                f"Receiver Phone: {default_address[2]}\n"
                f"Country: {default_address[3]}\n"
                f"City: {default_address[4]}\n"
                f"Province/State: {default_address[5]}\n"
                f"Postal Code: {default_address[6]}"
            )
            return JSONResponse(content={
                "fulfillmentText": f"Thank you for confirming your information!\nGot it! Your default shipping address is:\n{address_text}\nWould you like to use this address, or enter a new one? Reply with 'Use default address' or 'New address'."
            })
        else:
            return JSONResponse(content={
                "fulfillmentText": "Thank you for confirming your information!\nNo default address found. Please enter a new address with 'New address'."
            })
    else:
        return JSONResponse(content={
            "fulfillmentText": "Let’s update your information. Please provide your correct email or phone number (e.g., 'My email is john.doe@example.com' or 'My phone is 1234567890')."
        })

def use_default_address(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id].get("customer_info"):
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please provide your email or phone number again to identify yourself."
        })

    email = inprogress_orders[session_id]["customer_info"]["email"]
    phone = inprogress_orders[session_id]["customer_info"]["phone"]

    customer = db_helper.get_customer_by_email_or_phone(email, phone)
    if not customer:
        return JSONResponse(content={
            "fulfillmentText": "Customer not found. Please provide a valid email or phone number."
        })

    customer_id = customer[0]
    default_address = db_helper.get_default_address_by_customer(customer_id)
    if default_address:
        # Lưu địa chỉ mặc định vào session
        address_id, receiver_name, receiver_phone, country, city, province_state, postal_code = default_address
        inprogress_orders[session_id]["shipping_address"] = {
            "address_id": address_id,
            "receiver_name": receiver_name,
            "receiver_phone": receiver_phone,
            "country": country,
            "city": city,
            "province_state": province_state,
            "postal_code": postal_code,
            "is_default": True  # Địa chỉ mặc định nên có is_default là True
        }

        # Lấy danh sách phương thức giao hàng
        shipping_methods = db_helper.get_shipping_methods()
        if not shipping_methods:
            return JSONResponse(content={
                "fulfillmentText": "Sorry, no shipping methods are available at the moment. Please contact support."
            })

        # Tính tổng số lượng sản phẩm trong đơn hàng
        order_list = inprogress_orders[session_id]["order_list"]
        total_quantity = sum(quantity for _, quantity in order_list)

        # Giả định khoảng cách (km) để tính thời gian giao hàng
        ASSUMED_DISTANCE_KM = 100  # Giả định khoảng cách 100km (có thể thay đổi)

        # Tính ngày hiện tại
        current_date = datetime.now()

        # Tạo danh sách phương thức giao hàng
        shipping_options_text = "Here are the available shipping methods for your order:\n"
        for idx, method in enumerate(shipping_methods, 1):
            shipping_fee = method["cost_per_product"] * total_quantity
            delivery_time_days = method["average_delivery_time_per_km"] * ASSUMED_DISTANCE_KM
            estimated_date = (current_date + timedelta(days=delivery_time_days)).strftime("%Y-%m-%d")
            shipping_options_text += (
                f"Option {idx} - {method['method_name']}: ${shipping_fee:.2f}, "
                f"Estimated Delivery: {estimated_date}\n"
            )

        response_text = (
            f"Thanks for confirming your delivery address!\n"
            f"{shipping_options_text}\n"
            "Please let me know which shipping method you'd like to use. (For example: 'I’ll go with Express Shipping')"
        )
        return JSONResponse(content={"fulfillmentText": response_text})
    else:
        return JSONResponse(content={
            "fulfillmentText": "No default address found. Please provide a new address with 'New address'."
        })

def request_new_shipping_address(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id].get("customer_info"):
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please provide your email or phone number again to identify yourself."
        })

    email = inprogress_orders[session_id]["customer_info"]["email"]
    phone = inprogress_orders[session_id]["customer_info"]["phone"]

    customer = db_helper.get_customer_by_email_or_phone(email, phone)
    if not customer:
        return JSONResponse(content={
            "fulfillmentText": "Customer not found. Please provide a valid email or phone number."
        })

    response_text = (
        "Sure! Please enter your new shipping address using the following format:\n"
        "Receiver Name: [Your Full Name]\n"
        "Receiver Phone: [Phone Number]\n"
        "Country: [Country]\n"
        "City: [City]\n"
        "Province: [Province or State]\n"
        "Postal Code: [ZIP or Postal Code]\n"
        "Default: [Yes or No]\n\n"
        "Example:\n"
        "Receiver Name: Alex Johnson\n"
        "Receiver Phone: +1 555-123-4567\n"
        "Country: USA\n"
        "City: Los Angeles\n"
        "Province: California\n"
        "Postal Code: 90001\n"
        "Default: Yes"
    )
    return JSONResponse(content={"fulfillmentText": response_text})

def process_new_shipping_address(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id].get("customer_info"):
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please provide your email or phone number again to identify yourself."
        })

    email = inprogress_orders[session_id]["customer_info"]["email"]
    phone = inprogress_orders[session_id]["customer_info"]["phone"]

    customer = db_helper.get_customer_by_email_or_phone(email, phone)
    if not customer:
        return JSONResponse(content={
            "fulfillmentText": "Customer not found. Please provide a valid email or phone number."
        })

    customer_id = customer[0]

    # Lấy các tham số từ Dialogflow và xử lý giá trị
    receiver_name = parameters.get("person", "")
    if isinstance(receiver_name, dict):
        receiver_name = receiver_name.get("name", "")
    receiver_name = receiver_name.strip() if isinstance(receiver_name, str) else ""

    receiver_phone = parameters.get("phone-number", "")
    if isinstance(receiver_phone, dict):
        receiver_phone = receiver_phone.get("number", "")
    receiver_phone = receiver_phone.strip() if isinstance(receiver_phone, str) else ""

    country = parameters.get("geo-country", "")
    if isinstance(country, dict):
        country = country.get("country", "")
    country = country.strip() if isinstance(country, str) else ""

    city = parameters.get("geo-city", "")
    if isinstance(city, dict):
        city = city.get("city", "")
    city = city.strip() if isinstance(city, str) else ""

    province = parameters.get("province", "")
    if isinstance(province, dict):
        province = province.get("province", "")
    province = province.strip() if isinstance(province, str) else ""

    postal_code = parameters.get("zip-code", "")
    if isinstance(postal_code, dict):
        postal_code = postal_code.get("zip-code", "")
    postal_code = postal_code.strip() if isinstance(postal_code, str) else ""

    is_default = parameters.get("is_default", "")
    if isinstance(is_default, dict):
        is_default = is_default.get("is_default", "")
    is_default = is_default.lower() in ["yes", "y", "true"] if isinstance(is_default, str) else False

    # Kiểm tra nếu có trường nào thiếu
    if not all([receiver_name, receiver_phone, country, city, province, postal_code]):
        response_text = (
            "Sorry but it looks like some information is missing or incorrectly formatted.\n"
            "Please make sure to include all required fields using this format:\n"
            "Receiver Name: [Your Full Name]\n"
            "Receiver Phone: [Phone Number]\n"
            "Country: [Country]\n"
            "City: [City]\n"
            "Province: [Province or State]\n"
            "Postal Code: [ZIP or Postal Code]\n"
            "Default: [Yes or No]\n\n"
            "Example:\n"
            "Receiver Name: Alex Johnson\n"
            "Receiver Phone: +1 555-123-4567\n"
            "Country: USA\n"
            "City: Los Angeles\n"
            "Province: California\n"
            "Postal Code: 90001\n"
            "Default: Yes"
        )
        return JSONResponse(content={"fulfillmentText": response_text})

    # Lưu địa chỉ mới
    new_address_id = db_helper.save_new_shipping_address(
        customer_id,
        receiver_name,
        receiver_phone,
        country,
        city,
        province,
        postal_code,
        is_default
    )
    if new_address_id:
        # Đảm bảo địa chỉ được lưu vào session
        inprogress_orders[session_id]["shipping_address"] = {
            "address_id": new_address_id,
            "receiver_name": receiver_name,
            "receiver_phone": receiver_phone,
            "country": country,
            "city": city,
            "province_state": province,
            "postal_code": postal_code,
            "is_default": is_default
        }
        address_text = (
            f"Receiver Name: {receiver_name}\n"
            f"Receiver Phone: {receiver_phone}\n"
            f"Country: {country}\n"
            f"City: {city}\n"
            f"Province: {province}\n"
            f"Postal Code: {postal_code}\n"
            f"Is Default: {str(is_default).capitalize()}"
        )
        response_text = (
            f"Great! Here is the delivery address you provided:\n{address_text}\n"
            "Please confirm: Is this delivery address correct? (You can reply with 'Yes' to confirm, or let me know what you'd like to change.)"
        )
        return JSONResponse(content={"fulfillmentText": response_text})
    else:
        return JSONResponse(content={
            "fulfillmentText": "Sorry, there was an error saving your new address. Please try again."
        })

def confirm_new_address(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id].get("shipping_address"):
        return JSONResponse(content={
            "fulfillmentText": "No shipping address found. Please provide a new address."
        })

    confirmation = parameters.get("confirmation", "").lower()
    edit_keywords = ["change", "fix", "edit", "wrong", "incorrect", "different"]

    if any(keyword in confirmation for keyword in edit_keywords):
        response_text = (
            "Sure! Please enter your new shipping address using the following format:\n"
            "Receiver Name: [Your Full Name]\n"
            "Receiver Phone: [Phone Number]\n"
            "Country: [Country]\n"
            "City: [City]\n"
            "Province: [Province or State]\n"
            "Postal Code: [ZIP or Postal Code]\n"
            "Default: [Yes or No]\n\n"
            "Example:\n"
            "Receiver Name: Alex Johnson\n"
            "Receiver Phone: +1 555-123-4567\n"
            "Country: USA\n"
            "City: Los Angeles\n"
            "Province: California\n"
            "Postal Code: 90001\n"
            "Default: Yes"
        )
        return JSONResponse(content={"fulfillmentText": response_text})

    if "yes" in confirmation or "correct" in confirmation:
        # Đảm bảo địa chỉ vẫn tồn tại trong session
        address = inprogress_orders[session_id].get("shipping_address")
        if not address:
            return JSONResponse(content={
                "fulfillmentText": "No shipping address found. Please provide a new address."
            })

        # Lấy danh sách phương thức giao hàng
        shipping_methods = db_helper.get_shipping_methods()
        if not shipping_methods:
            return JSONResponse(content={
                "fulfillmentText": "Sorry, no shipping methods are available at the moment. Please contact support."
            })

        # Tính tổng số lượng sản phẩm trong đơn hàng
        order_list = inprogress_orders[session_id]["order_list"]
        total_quantity = sum(quantity for _, quantity in order_list)

        # Giả định khoảng cách (km) để tính thời gian giao hàng
        ASSUMED_DISTANCE_KM = 100

        # Tính ngày hiện tại
        current_date = datetime.now()

        # Tạo danh sách phương thức giao hàng
        shipping_options_text = "Here are the available shipping methods for your order:\n"
        for idx, method in enumerate(shipping_methods, 1):
            shipping_fee = method["cost_per_product"] * total_quantity
            delivery_time_days = method["average_delivery_time_per_km"] * ASSUMED_DISTANCE_KM
            estimated_date = (current_date + timedelta(days=delivery_time_days)).strftime("%Y-%m-%d")
            shipping_options_text += (
                f"Option {idx} - {method['method_name']}: ${shipping_fee:.2f}, "
                f"Estimated Delivery: {estimated_date}\n"
            )

        response_text = (
            f"Thanks for confirming your delivery address!\n"
            f"{shipping_options_text}\n"
            "Please let me know which shipping method you'd like to use. (For example: 'I’ll go with Express Shipping')"
        )
        return JSONResponse(content={"fulfillmentText": response_text})

    return JSONResponse(content={
        "fulfillmentText": "Please confirm if the address is correct (e.g., 'Yes' or let me know what to change)."
    })

def confirm_shipping_method(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please start your order again."
        })

    # Lấy phương thức vận chuyển được chọn
    shipping_method_name = parameters.get("shipping-method", "")
    if not shipping_method_name:
        return JSONResponse(content={
            "fulfillmentText": "Please specify a shipping method (e.g., 'I’ll go with Express Shipping')."
        })

    # Lấy danh sách phương thức vận chuyển từ database
    shipping_methods = db_helper.get_shipping_methods()
    if not shipping_methods:
        return JSONResponse(content={
            "fulfillmentText": "Sorry, no shipping methods are available at the moment. Please contact support."
        })

    # Tìm phương thức vận chuyển khớp với lựa chọn của khách hàng
    selected_method = None
    for method in shipping_methods:
        if method["method_name"].lower() == shipping_method_name.lower():
            selected_method = method
            break

    if not selected_method:
        return JSONResponse(content={
            "fulfillmentText": f"Sorry, the shipping method '{shipping_method_name}' is not available. Please choose another method."
        })

    # Tính tổng số lượng sản phẩm
    order_list = inprogress_orders[session_id]["order_list"]
    total_quantity = sum(quantity for _, quantity in order_list)

    # Tính phí vận chuyển và thời gian giao hàng
    shipping_fee = selected_method["cost_per_product"] * total_quantity
    ASSUMED_DISTANCE_KM = 100
    delivery_time_days = selected_method["average_delivery_time_per_km"] * ASSUMED_DISTANCE_KM
    current_date = datetime.now()
    estimated_delivery = (current_date + timedelta(days=delivery_time_days)).strftime("%Y-%m-%d")

    # Lưu thông tin phương thức vận chuyển vào session
    inprogress_orders[session_id]["shipping_info"] = {
        "method_name": selected_method["method_name"],
        "shipping_fee": shipping_fee,
        "estimated_delivery": estimated_delivery
    }

    # Kiểm tra và lấy địa chỉ giao hàng
    address = inprogress_orders[session_id].get("shipping_address")
    if not address:
        return JSONResponse(content={
            "fulfillmentText": "No shipping address found. Please provide a delivery address using 'New address' or confirm a default address."
        })

    # Tổng hợp thông tin đơn hàng
    items_ordered = []
    subtotal = 0
    for product_id, quantity in order_list:
        product = db_helper.get_list_products_by_id(product_id)
        if not product:
            continue
        product = product[0]
        product_name = product[0]
        price = float(product[2])
        line_total = price * quantity
        subtotal += line_total
        items_ordered.append(f"- {product_name} x{quantity} (${price:.2f} each) = ${line_total:.2f}")

    # Discount (nếu có)
    discount_info = inprogress_orders[session_id].get("discount", None)
    discount_text = ""
    discount_amount = 0
    if discount_info:
        promo_code = discount_info.get("promo_code", "")
        discount_amount = discount_info.get("discount_amount", 0)
        discount_text = f"- Discount ({promo_code}): -${discount_amount:.2f}"

    # Delivery address
    address_text = (
        f"Receiver Name: {address['receiver_name']}, "
        f"Receiver Phone: {address['receiver_phone']}, "
        f"{address['city']}, {address['province_state']}, "
        f"{address['country']}, Postal Code: {address['postal_code']}"
    )

    # Tổng hợp thông tin
    total_amount = subtotal - discount_amount + shipping_fee

    summary_text = (
        f"Great! Here is a summary of your order:\n"
        f"- Items ordered:\n"
        f"{' '.join(items_ordered)}\n"
        f"- Subtotal: ${subtotal:.2f}\n"
        f"{discount_text}\n"
        f"- Shipping method: {selected_method['method_name']}\n"
        f"- Shipping fee: ${shipping_fee:.2f}\n"
        f"- Delivery address: {address_text}\n"
        f"- Estimated delivery: {estimated_delivery}\n"
        f"🛒 Total amount: ${total_amount:.2f}\n\n"
        "Please select a payment method. You can choose from: Credit Card, PayPal, Cash on Delivery, Bank Transfer...\n"
        "Which payment method would you like to use?"
    )

    return JSONResponse(content={"fulfillmentText": summary_text})

def select_payment_method(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please start your order again."
        })

    # Lấy phương thức thanh toán được chọn
    payment_method = parameters.get("payment-method", "").strip()
    if not payment_method:
        return JSONResponse(content={
            "fulfillmentText": "Please specify a payment method (e.g., 'I’ll go with COD' or 'PayPal, please')."
        })

    # Lấy danh sách phương thức thanh toán hợp lệ từ database
    payment_methods = db_helper.get_payment_methods()  # Cần thêm hàm này trong db_helper.py
    valid_methods = [method["method_name"] for method in payment_methods]

    # Kiểm tra phương thức thanh toán có hợp lệ không
    if payment_method not in valid_methods:
        valid_methods_text = "\n".join([f"- {method}" for method in valid_methods])
        return JSONResponse(content={
            "fulfillmentText": f"Sorry, '{payment_method}' is not a valid payment method. Please choose from the following:\n{valid_methods_text}"
        })

    # Lưu phương thức thanh toán vào session
    inprogress_orders[session_id]["payment_method"] = payment_method

    # Tổng hợp thông tin đơn hàng
    order_list = inprogress_orders[session_id]["order_list"]
    shipping_info = inprogress_orders[session_id].get("shipping_info", {})
    shipping_method = shipping_info.get("method_name", "Not specified")
    estimated_delivery = shipping_info.get("estimated_delivery", "Not specified")
    discount_info = inprogress_orders[session_id].get("discount", {})
    address = inprogress_orders[session_id].get("shipping_address", {})

    items_ordered = []
    subtotal = 0
    for product_id, quantity in order_list:
        product = db_helper.get_list_products_by_id(product_id)
        if not product:
            continue
        product = product[0]
        product_name = product[0]
        price = float(product[2])
        line_total = price * quantity
        subtotal += line_total
        items_ordered.append(f"[{product_name}] – Quantity: {quantity} – Price: ${price:.2f}")

    discount_text = ""
    discount_amount = discount_info.get("discount_amount", 0)
    if discount_amount > 0:
        promo_code = discount_info.get("promo_code", "N/A")
        discount_text = f"- Discount Applied: {promo_code} (-${discount_amount:.2f})"

    shipping_fee = shipping_info.get("shipping_fee", 0)
    total_amount = subtotal - discount_amount + shipping_fee

    # Hiển thị thông tin chi tiết và hỏi xác nhận
    address_text = (
        f"Receiver Name: {address.get('receiver_name', 'Not specified')}, "
        f"Receiver Phone: {address.get('receiver_phone', 'Not specified')}, "
        f"{address.get('city', '')}, {address.get('province_state', '')}, "
        f"{address.get('country', '')}, Postal Code: {address.get('postal_code', '')}"
    )
    summary_text = (
        f"Here’s a summary of your order before we proceed to payment:\n"
        f"- Items:\n"
        f"{' '.join(items_ordered)}\n"
        f"- Total Price: ${subtotal:.2f}\n"
        f"- Shipping Address: {shipping_method} – {estimated_delivery}\n"
        f"- Payment Method: {payment_method}\n"
        f"{discount_text}\n"
        f"- Final Total: ${total_amount:.2f}\n"
        "Please review your order carefully. Everything looks correct? Let me know if you need any changes, or if I can proceed with placing your order."
    )

    return JSONResponse(content={"fulfillmentText": summary_text})

def confirm_order_placement(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "Session not found. Please start your order again."
        })

    # Kiểm tra xem thông tin cần thiết đã sẵn sàng chưa
    if not all(key in inprogress_orders[session_id] for key in ["order_list", "shipping_address", "shipping_info", "payment_method", "customer_info"]):
        return JSONResponse(content={
            "fulfillmentText": "Order information is incomplete. Please ensure all steps (products, shipping, and payment) are confirmed."
        })

    # Lấy thông tin từ session
    order_list = inprogress_orders[session_id]["order_list"]
    shipping_info = inprogress_orders[session_id]["shipping_info"]
    payment_method = inprogress_orders[session_id]["payment_method"]
    address = inprogress_orders[session_id]["shipping_address"]
    discount_info = inprogress_orders[session_id].get("discount", {})
    customer_info = inprogress_orders[session_id]["customer_info"]

    # Tính toán tổng giá trị
    subtotal = 0
    for product_id, quantity in order_list:
        product = db_helper.get_list_products_by_id(product_id)
        if not product:
            continue
        product = product[0]
        price = float(product[2])
        line_total = price * quantity
        subtotal += line_total

    discount_amount = discount_info.get("discount_amount", 0)
    shipping_fee = shipping_info["shipping_fee"]
    total_amount = subtotal - discount_amount + shipping_fee

    # Lấy customer_id
    customer = db_helper.get_customer_by_email_or_phone(customer_info["email"], customer_info["phone"])
    if not customer:
        return JSONResponse(content={
            "fulfillmentText": "Customer not found in database. Please try again."
        })
    customer_id = customer[0]

    # Lấy payment_method_id
    payment_methods = db_helper.get_payment_methods()
    payment_method_id = None
    for method in payment_methods:
        if method["method_name"].lower() == payment_method.lower():
            payment_method_id = method["method_id"]
            break
    if not payment_method_id:
        return JSONResponse(content={
            "fulfillmentText": f"Payment method '{payment_method}' not found in database."
        })

    # Lấy shipping_method_id
    shipping_methods = db_helper.get_shipping_methods()
    shipping_method_id = None
    for method in shipping_methods:
        if method["method_name"].lower() == shipping_info["method_name"].lower():
            shipping_method_id = method["method_id"]
            break
    if not shipping_method_id:
        return JSONResponse(content={
            "fulfillmentText": f"Shipping method '{shipping_info['method_name']}' not found in database."
        })

    # Lấy shipping_address_id
    shipping_address_id = address["address_id"]

    # Lấy promotion_id (nếu có)
    promotion_id = None
    if discount_info:
        promo_code = discount_info.get("promo_code")
        promotion = db_helper.get_promotion_by_code(promo_code)
        if promotion:
            promotion_id = promotion[0]  # Giả định promotion[0] là promotion_id

    # Lưu order vào database
    order_details = {
        "customer_id": customer_id,
        "payment_method_id": payment_method_id,
        "shipping_method_id": shipping_method_id,
        "shipping_address_id": shipping_address_id,
        "promotion_id": promotion_id,
        "total_amount": total_amount,
        "shipping_fee": shipping_fee,
        "discount": discount_amount,
        "estimated_delivery_date": shipping_info["estimated_delivery"],
        "order_list": order_list
    }
    order_id = db_helper.place_order(order_details, session_id)

    if not order_id:
        return JSONResponse(content={
            "fulfillmentText": "Failed to place your order due to a database error. Please try again."
        })

    # Trả về order_id để Dialogflow sử dụng trong default response
    return JSONResponse(content={
        "fulfillmentText": f"Order placed successfully! Order ID: {order_id}. Is there anything else I can help you with today?",
        "outputContexts": [
            {
                "name": f"{session_id}/contexts/ongoing-order-confirmation",
                "parameters": {
                    "order_id": order_id
                }
            }
        ]
    })

def end_conversation(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders or "payment_method" not in inprogress_orders[session_id]:
        return JSONResponse(content={
            "fulfillmentText": "It seems your order was not completed. Please start a new order if needed."
        })

    payment_method = inprogress_orders[session_id]["payment_method"]
    is_cod = payment_method.lower() == "cash on delivery"

    if is_cod:
        end_responses = [
            "It was a pleasure assisting you. Thank you for shopping with us, we hope you enjoy your purchase! If you have any questions later, feel free to come back and chat with us. Have a wonderful day!"
        ]
    else:
        end_responses = [
            f"Thank you! Since you’ve chosen {payment_method}, we’ll now redirect you to the secure payment page to complete your transaction. If you have questions in the future, don’t hesitate to ask."
        ]

    response_text = end_responses

    # Xóa session sau khi hoàn tất
    if session_id in inprogress_orders:
        del inprogress_orders[session_id]

    # Tạo session path để xóa các context liên quan
    session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]

    return JSONResponse(content={
        "fulfillmentText": response_text,
        "outputContexts": [
            # Xóa tất cả các context liên quan đến submit_review
            {
                "name": f"{session_path}/contexts/ongoing-order",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/ongoing-new-address",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/ongoing-new-adress",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/ongoing-confirm-info",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/ongoing-default-address",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/ongoing-identify",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/edit-order",
                "lifespanCount": 0
            }
        ]
        })

def cancel_order(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "No order found to cancel. You can start a new order if you'd like!"
        })

    # Xóa toàn bộ session
    del inprogress_orders[session_id]

    # Sử dụng default response từ Dialogflow
    return JSONResponse(content={"fulfillmentText": "Got it! Your order has been canceled as requested. If you change your mind, feel free to start a new order anytime. Thank you for visiting us. Let me know if there's anything else I can help with!"})

def remove_items(parameters: dict, output_contexts, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "No order found to modify. You can start a new order if you'd like!"
        })

    order_list = inprogress_orders[session_id].get("order_list", [])
    if not order_list:
        return JSONResponse(content={
            "fulfillmentText": "Your order is empty. You can start adding items if you'd like!"
        })

    # Lấy danh sách product_id cần xóa
    product_ids_to_remove = parameters.get("number", [])
    if not product_ids_to_remove:
        return JSONResponse(content={
            "fulfillmentText": "Please specify the product ID(s) you want to remove (e.g., 'Remove item ID 2')."
        })

    # Chuyển product_ids_to_remove thành danh sách các số nguyên
    try:
        product_ids_to_remove = [int(pid) for pid in product_ids_to_remove]
    except (ValueError, TypeError):
        return JSONResponse(content={
            "fulfillmentText": "Invalid product ID(s). Please provide valid numeric IDs (e.g., 'Remove item ID 2')."
        })

    # Danh sách sản phẩm bị xóa
    removed_items = []
    updated_order_list = []

    for product_id, quantity in order_list:
        if product_id in product_ids_to_remove:
            # Lấy thông tin sản phẩm để hiển thị tên
            product = db_helper.get_list_products_by_id(product_id)
            if product:
                product_name = product[0][0]
                removed_items.append(product_name)
        else:
            updated_order_list.append((product_id, quantity))

    if not removed_items:
        return JSONResponse(content={
            "fulfillmentText": "None of the specified items were found in your order. Please check the IDs and try again."
        })

    # Cập nhật order_list trong session
    inprogress_orders[session_id]["order_list"] = updated_order_list

    # Nếu order_list trống sau khi xóa, hủy toàn bộ đơn hàng
    if not updated_order_list:
        del inprogress_orders[session_id]
        return JSONResponse(content={
            "fulfillmentText": "All items have been removed, and your order has been canceled. You can start a new order if you'd like!"
        })

    # Tính lại tổng giá trị đơn hàng
    total_amount = 0
    for product_id, quantity in updated_order_list:
        product = db_helper.get_list_products_by_id(product_id)
        if not product:
            continue
        price = float(product[0][2])
        total_amount += price * quantity

    # Xóa mã giảm giá hiện tại (vì tổng giá trị đơn hàng đã thay đổi)
    if "discount" in inprogress_orders[session_id]:
        del inprogress_orders[session_id]["discount"]

    # Lấy danh sách mã giảm giá hợp lệ
    promotions = db_helper.get_available_promotions(total_amount)
    if not promotions:
        return JSONResponse(content={
            "fulfillmentText": (
                f"The following item(s) have been successfully removed from your order:\n"
                f"• {' • '.join(removed_items)}\n"
                f"Your updated order total is now ${total_amount:.2f}.\n"
                "No discount codes are available for your current order total. "
                "Please provide your email or phone number to identify yourself (e.g., 'My email is john.doe@example.com')."
            )
        })

    # Hiển thị danh sách mã giảm giá
    promo_text = "Here are the available discount codes for your order:\n"
    for promo in promotions:
        promo_code, discount_value = promo[1], promo[2]
        promo_text += f"• {promo_code}: {discount_value}% off (minimum order ${promo[3]:.2f})\n"

    response_text = (
        f"The following item(s) have been successfully removed from your order:\n"
        f"• {' • '.join(removed_items)}\n"
        f"Your updated order total is now ${total_amount:.2f}.\n"
        f"Since your order total has changed, let's check if you can apply any discount codes again.\n"
        f"{promo_text}\n"
        "Which of these discount codes would you like to use? You can enter the code of the promotion you'd like to apply (e.g., SUMMER15)."
    )

    return JSONResponse(content={"fulfillmentText": response_text})

def show_customer_orders(parameters: dict, output_contexts, session_id: str):
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
        order_details = []
        for order in orders:
            # Xử lý trường hợp Product_Names có thể null
            products = order.get('product_names') or order.get('Product_Names', 'No products')
            
            # Format số tiền an toàn hơn
            total_amount = order.get('total_amount') or order.get('Total_Amount', 0)
            try:
                formatted_amount = f"${float(total_amount):,.2f}"
            except (ValueError, TypeError):
                formatted_amount = "$0.00"
            
            order_str = (
                f"Order ID: {order.get('order_id') or order.get('Order_ID', 'N/A')}, "
                f"Products: {products}, "
                f"Total: {formatted_amount}, "
                f"Payment Method: {order.get('payment_method') or order.get('Payment_Method', 'N/A')}, "
                f"Status: {order.get('order_status') or order.get('Order_Status', 'N/A')}"
            )
            order_details.append(order_str)
        
        fulfillment_text = "Here are your orders:\n" + "\n".join(order_details)

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def delete_order_handler(parameters: dict, output_contexts, session_id: str):
    """
    Handle 'delete order' intent to delete a specific order by Order_ID if its status is 'processing'.
    """
    order_id = parameters.get('Order_ID')

    # Validate input
    if not order_id:
        fulfillment_text = "Please provide an Order ID."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    try:
        order_id = int(order_id)
    except ValueError:
        fulfillment_text = "Invalid Order ID. Please provide a valid number."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    success = db_helper.delete_order(order_id)
    if success:
        fulfillment_text = f"Successfully deleted Order ID {order_id}."
    else:
        fulfillment_text = f"Failed to delete Order ID {order_id}. It may not exist or the order status is not 'processing'."

    # Tạo session path để xóa các context liên quan
    session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [
            # Xóa tất cả các context liên quan đến submit_review
            {
                "name": f"{session_path}/contexts/ongoing-tracking",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/delete-tracking-ordered",
                "lifespanCount": 0
            }
        ]
    })

def update_shipping_address_handler(parameters: dict, output_contexts, session_id: str):
    """
    Handle 'update shipping address' intent to update the shipping address for a specific order.
    """
    order_id = parameters.get('Order_ID')
    customer_id = parameters.get('number')

    person_param = parameters.get('person')
    if isinstance(person_param, dict):
        receiver_name = person_param.get('name')
    elif isinstance(person_param, list) and len(person_param) > 0:

        receiver_name = person_param[0]
    else:
        receiver_name = person_param
    
    receiver_phone = parameters.get('phone-number')
    country = parameters.get('geo-country')
    city = parameters.get('geo-city')
    province_state = parameters.get('province')
    postal_code = parameters.get('postal_code') 

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
    except (ValueError, TypeError): 
        fulfillment_text = "Invalid Order ID or Customer ID. Please provide valid numbers."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    success = db_helper.update_shipping_address(
        order_id, customer_id, receiver_name, receiver_phone, country, city, province_state, postal_code
    )
    if success:
        fulfillment_text = f"Successfully updated shipping address for Order ID {order_id}."
    else:
        fulfillment_text = (f"Failed to update shipping address for Order ID {order_id}. "
                           "It may not exist, not belong to the customer, or its status is not 'processing'.")

    # Tạo session path để xóa các context liên quan
    session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [
            # Xóa tất cả các context liên quan đến submit_review
            {
                "name": f"{session_path}/contexts/ongoing-tracking",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/delete-tracking-ordered",
                "lifespanCount": 0
            }
        ]
    })

def submit_review_start(parameters: dict, output_contexts: list, session_id: str):
    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None

    if not unreviewed_products:
        fulfillment_text = "It looks like you haven’t purchased any products yet, or all your products are already reviewed!"
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    if product:
        product_details = db_helper.get_product_details(product)
        if product_details:
            product_details = list(product_details)
            product_details[1] = float(product_details[1])  # Chuyển đổi Decimal thành float
        product_names = [p[0] for p in unreviewed_products]
        if product_details and product in product_names:
            fulfillment_text = (f"Thanks for sharing, John! For {product} (${product_details[1]}, {product_details[5]} brand, "
                               f"{product_details[6]} category): Rating: Would you like to give it a rating from 1 to 5 stars? "
                               f"Comment: Please confirm or provide additional details, and I’ll submit the review for you, or say 'cancel' to exit.")
            return JSONResponse(content={"fulfillmentText": fulfillment_text})
        else:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
            fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                               f"Please choose from the following unreviewed products: {product_list}, or say 'cancel' to exit.")
    else:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Awesome, we’d love to hear your feedback! Based on your order history, "
                           f"here are your unreviewed products: {product_list}. "
                           f"Please specify which product you’d like to review (e.g., 'Product 1'), or say 'cancel' to exit.")

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def submit_review_product_confirm(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None
    initial_comment = parameters.get("initial_comment", "")
    if isinstance(initial_comment, list):
        initial_comment = initial_comment[0] if initial_comment else ""

    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    if not product:
        for context in output_contexts:
            if context["name"].endswith("submit_review_active"):
                params = context.get("parameters", {})
                product = params.get("product")
                break

    if not product:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = f"Please specify a product to review from the list: {product_list}, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    product_details = db_helper.get_product_details(product)
    if product_details:
        product_details = list(product_details)
        product_details[1] = float(product_details[1])  # Chuyển đổi Decimal thành float
    product_names = [p[0] for p in unreviewed_products]
    if not product_details or product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                           f"Please choose from your unreviewed products: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    name, price, _, _, _, brand, category = product_details
    fulfillment_text = (f"Thanks for sharing, John! For {name} (${price}, {brand} brand, {category} category): "
                       f"Rating: Would you like to give it a rating from 1 to 5 stars? "
                       f"Comment: {initial_comment} "
                       f"Please confirm or provide additional details, and I’ll submit the review for you, or say 'cancel' to exit.")
    return JSONResponse(content={"fulfillmentText": fulfillment_text,})

def submit_review_details_collect(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product") or parameters.get("product-name")
    rating = parameters.get("rating")
    comment = parameters.get("comment", "")
    
    if isinstance(product, list):
        product = product[0] if product else None
    if isinstance(rating, list):
        rating = rating[0] if rating else None
    if isinstance(comment, list):
        comment = comment[0] if comment else ""

    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    if not product:
        for context in output_contexts:
            if context["name"].endswith("submit_review_active"):
                params = context.get("parameters", {})
                context_product = params.get("product") or params.get("product-name")
                # Xử lý context product cũng có thể là array
                if isinstance(context_product, list):
                    product = context_product[0] if context_product else None
                else:
                    product = context_product
                break

    product_names = [p[0] for p in unreviewed_products]
    if not product or product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        if not unreviewed_products:
            fulfillment_text = "It looks like you haven’t purchased any products yet, or all your products are already reviewed!"
        else:
            fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                               f"Please choose from: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    if not rating:
        fulfillment_text = f"Please provide a rating from 1 to 5 stars for {product}, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    # Chuyển rating thành float để đảm bảo giá trị hợp lệ
    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        fulfillment_text = f"Please provide a valid rating from 1 to 5 stars for {product}, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    fulfillment_text = (f"Here’s your review for {product}: "
                       f"Rating: {rating}/5 "
                       f"Comment: {comment} "
                       f"Would you like to edit your rating or comment before I submit it? Or say 'submit it now' to proceed, or 'cancel' to exit.")
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def submit_review_edit(parameters: dict, output_contexts: list, session_id: str):
    # Trích xuất từ context
    product = None
    rating = None
    comment = None
    unreviewed_products = None
    for context in output_contexts:
        if context["name"].endswith("submit_review_confirm"):
            params = context.get("parameters", {})
            product = params.get("product")
            rating = params.get("rating")
            comment = params.get("comment")
            unreviewed_products = params.get("unreviewed_products")
            break

    # Xử lý kiểu dữ liệu
    if isinstance(product, list):
        product = product[0] if product else None
    if isinstance(rating, list):
        rating = rating[0] if rating else None
    if isinstance(comment, list):
        comment = comment[0] if comment else None
    if isinstance(unreviewed_products, list):
        unreviewed_products = unreviewed_products if unreviewed_products else []

    # Debug log để kiểm tra giá trị từ context
    debug_info = f"Context values - product: {product}, rating: {rating}, comment: {comment}, unreviewed_products: {unreviewed_products}"

    # Chuyển rating thành float nếu có
    try:
        rating = float(rating) if rating else None
    except (ValueError, TypeError):
        rating = None

    # Trích xuất new_rating từ @Rating
    new_rating = parameters.get("new_rating")
    if isinstance(new_rating, list):
        new_rating = new_rating[0] if new_rating else None
    if new_rating:  # Chỉ xử lý nếu new_rating không rỗng
        try:
            # Trích xuất số từ @Rating (ví dụ: "4 stars" -> 4)
            num = ''.join(filter(str.isdigit, str(new_rating)))
            new_rating = float(num) if num else None
            if new_rating and (new_rating < 1 or new_rating > 5):
                new_rating = None  # Giữ rating cũ nếu không hợp lệ
        except (ValueError, TypeError):
            new_rating = None

    # Trích xuất new_comment
    new_comment = parameters.get("new_comment")
    if isinstance(new_comment, list):
        new_comment = new_comment[0] if new_comment else None
    new_comment = new_comment if new_comment else None

    # Cập nhật rating và comment
    rating = new_rating if new_rating is not None and new_rating != "" else rating
    comment = new_comment if new_comment is not None else comment

    # Kiểm tra required fields
    if not product or rating is None:
        full_unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        full_unreviewed_products = convert_decimals_to_floats(full_unreviewed_products)
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in full_unreviewed_products])
        fulfillment_text = (f"Error: Missing required fields in edit. {debug_info}. "
                           f"Please provide a rating from 1 to 5 stars for {product}, or choose a product from: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    fulfillment_text = (f"I’ve updated your review for {product}: "
                       f"Rating: {rating}/5 "
                       f"Comment: {comment} "
                       f"Would you like to make more changes, or say 'submit it now' to proceed, or 'cancel' to exit?")
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def submit_review_submit(parameters: dict, output_contexts: list, session_id: str):
    product = None
    rating = None
    comment = None
    new_rating = None
    new_comment = None
    unreviewed_products = None
    
    # Lấy thông tin từ context submit_review_confirm
    for context in output_contexts:
        if context["name"].endswith("submit_review_confirm"):
            params = context.get("parameters", {})
            product = params.get("product") or params.get("product-name")
            rating = params.get("rating")
            comment = params.get("comment")
            new_rating = params.get("new_rating")
            new_comment = params.get("new_comment")
            unreviewed_products = params.get("unreviewed_products")
            break

    # Xử lý kiểu dữ liệu cho các giá trị cũ
    if isinstance(product, list):
        product = product[0] if product else None
    if isinstance(rating, list):
        rating = rating[0] if rating else None
    if isinstance(comment, list):
        comment = comment[0] if comment else ""
    if isinstance(unreviewed_products, list):
        unreviewed_products = unreviewed_products if unreviewed_products else []

    # Xử lý kiểu dữ liệu cho các giá trị mới
    if isinstance(new_rating, list):
        new_rating = new_rating[0] if new_rating else None
    if isinstance(new_comment, list):
        new_comment = new_comment[0] if new_comment else None

    # Ưu tiên giá trị mới nếu có, không thì lấy giá trị cũ
    final_rating = new_rating if new_rating is not None and new_rating != "" else rating
    final_comment = new_comment if new_comment is not None and new_comment != "" else comment
    
    print(f"Debug info - final_rating: {final_rating}, final_comment: {final_comment}, product: {product}")
    
    # Chuyển đổi rating thành số
    try:
        final_rating = float(final_rating) if final_rating else None
    except (ValueError, TypeError):
        final_rating = None

    # Lấy danh sách sản phẩm chưa review từ database
    try:
        full_unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        full_unreviewed_products = convert_decimals_to_floats(full_unreviewed_products)
        
        # Nếu unreviewed_products rỗng, lấy từ database
        if not unreviewed_products:
            unreviewed_products = [p[0] for p in full_unreviewed_products]
            
    except Exception as e:
        print(f"Error getting unreviewed products: {str(e)}")
        return JSONResponse(content={
            "fulfillmentText": "Sorry, there was an error retrieving your products. Please try again later."
        })

    # Kiểm tra product và rating
    if not product or final_rating is None:
        if full_unreviewed_products:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in full_unreviewed_products])
            fulfillment_text = f"Sorry, I couldn't submit the review for {product}. Please provide a rating and product, or choose from: {product_list}, or say 'cancel' to exit."
        else:
            fulfillment_text = "Sorry, I couldn't submit the review. Please provide a valid product and rating, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    # Xác nhận sản phẩm hợp lệ
    product_names = [p[0] for p in full_unreviewed_products]
    if product not in product_names:
        if full_unreviewed_products:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in full_unreviewed_products])
            fulfillment_text = (f"Sorry, I couldn't submit the review for {product}. It's either not in your purchase history or has not been delivered yet. "
                               f"Please choose from: {product_list}, or say 'cancel' to exit.")
        else:
            fulfillment_text = f"Sorry, {product} is not available for review. You have no unreviewed products at the moment."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    # Submit review
    try:
        review_id = db_helper.insert_review(product, customer_id, final_rating, final_comment)
        print(f"Review submitted successfully with ID: {review_id}")
        review_date = datetime.now().strftime("%Y-%m-%d")
        
        # Tạo session path
        session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]
        
        # Lấy danh sách sản phẩm còn lại sau khi submit
        remaining_products = db_helper.get_unreviewed_products(customer_id)
        remaining_products = convert_decimals_to_floats(remaining_products)
        
        # Base message cho review đã submit thành công
        base_message = (f"Perfect! Here's the review for {product}: "
                       f"Rating: {final_rating}/5 "
                       f"Comment: {final_comment} "
                       f"Customer: John Doe "
                       f"Review Date: {review_date} "
                       f"I've submitted the review, and it'll appear on the product page soon. "
                       f"Your review will help other customers a lot! ")
        
        if remaining_products:
            # Còn sản phẩm chưa review
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in remaining_products])
            fulfillment_text = (base_message + 
                               f"Here are your remaining unreviewed products: {product_list}. "
                               f"Please specify which product you'd like to review next, or say 'cancel' to exit.")
            
            return JSONResponse(content={
                "fulfillmentText": fulfillment_text,
                "outputContexts": [
                    {
                        "name": f"{session_path}/contexts/submit_review_continue-followup",
                        "lifespanCount": 5,
                        "parameters": {
                            "remaining_products": [p[0] for p in remaining_products],
                            "flow_state": "continue_selection",
                            "product": product,
                            "last_review_id": review_id,
                        }
                    },
                    {
                        "name": f"{session_path}/contexts/submit_review_delete",
                        "lifespanCount": 5,
                        "parameters": {
                            "remaining_products": [p[0] for p in remaining_products],
                            "flow_state": "continue_selection",
                            "product": product,
                            "last_review_id": review_id,
                        }
                    },
                    # Disable các context khác để tránh conflict
                    {
                        "name": f"{session_path}/contexts/submit_review_active",
                        "lifespanCount": 0
                    },
                    {
                        "name": f"{session_path}/contexts/submit_review_confirm",
                        "lifespanCount": 0
                    }
                ]
            })
        else:
            # Đã review hết tất cả sản phẩm
            fulfillment_text = (base_message + 
                               "Great! You've reviewed all your products. Thank you for your feedback!")
            
            return JSONResponse(content={
                "fulfillmentText": fulfillment_text,
                "outputContexts": [
                    {
                        "name": f"{session_path}/contexts/submit_review_delete",
                        "lifespanCount": 5,
                        "parameters": {
                            "flow_state": "completed",
                            "product": product,
                            "last_review_id": review_id,
                        }
                    },
                    # Clear tất cả contexts khác
                    {
                        "name": f"{session_path}/contexts/submit_review_active",
                        "lifespanCount": 0
                    },
                    {
                        "name": f"{session_path}/contexts/submit_review_confirm",
                        "lifespanCount": 0
                    },
                    {
                        "name": f"{session_path}/contexts/submit_review_continue-followup",
                        "lifespanCount": 0
                    }
                ]
            })
        
    except Exception as e:
        print(f"Error submitting review: {str(e)}")
        fulfillment_text = f"Error: Failed to save review to database. Debug info - error: {str(e)}. Please try again, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})
        
def submit_review_continue(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None

    # Lấy remaining_products từ context nếu có
    remaining_products_from_context = None
    for context in output_contexts:
        if "continue_review_mode" in context["name"] or "submit_review_continue-followup" in context["name"]:
            params = context.get("parameters", {})
            remaining_products_from_context = params.get("remaining_products") or params.get("unreviewed_products")
            break

    # Nếu không có context, lấy từ database
    if not remaining_products_from_context:
        unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    else:
        # Nếu có context nhưng cần full info, vẫn query database
        unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        unreviewed_products = convert_decimals_to_floats(unreviewed_products)

    if not unreviewed_products:
        fulfillment_text = "It looks like you've reviewed all your purchased products! If you need help with something else, just let me know, or say 'cancel' to exit."
        return JSONResponse(content={"fulfillmentText": fulfillment_text})

    if product:
        product_details = db_helper.get_product_details(product)
        if product_details:
            product_details = list(product_details)
            product_details[1] = float(product_details[1])
        
        product_names = [p[0] for p in unreviewed_products]
        if product_details and product in product_names:
            # Chuyển sang intent để nhập rating và comment
            session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]
            
            fulfillment_text = (f"Thanks for choosing {product} (${product_details[1]}, {product_details[5]} brand, "
                               f"{product_details[6]} category)! Please provide your rating (1-5 stars) and any comments for this product.")
            
            return JSONResponse(content={"fulfillmentText": fulfillment_text})
        else:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
            fulfillment_text = (f"Sorry, {product} is either not in your purchase history, has not been delivered yet, or has already been reviewed. "
                               f"Please choose from the following unreviewed products: {product_list}, or say 'cancel' to exit.")
    else:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Great! Based on your order history, here are your remaining unreviewed products: {product_list}. "
                           f"Please specify which product you'd like to review (e.g., 'Product 1'), or say 'cancel' to exit.")

    return JSONResponse(content={"fulfillment_text": fulfillment_text})

def submit_review_end(parameters: dict, output_contexts: list, session_id: str):
    fulfillment_text = ("You’re welcome, John! Thanks for taking the time to share your review. "
                        "Your feedback is valuable and helps us improve our products and services. "
                        "If you have any other questions or need assistance with anything else, "
                        "just let me know. Have a great day!")
    
    # Tạo session path để xóa các context liên quan
    session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [
            # Xóa tất cả các context liên quan đến submit_review
            {
                "name": f"{session_path}/contexts/submit_review_active",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/submit_review_confirm",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/submit_review_continue-followup",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/submit_review_collect",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/submit_review_finalize",
                "lifespanCount": 0
            },
            {
                "name": f"{session_path}/contexts/submit_review_delete",
                "lifespanCount": 0
            }
        ]
    })

def submit_review_cancel(parameters: dict, output_contexts: list, session_id: str):
    review_id = None
    
    # Tìm review_id từ các output contexts
    for context in output_contexts:
        context_params = context.get("parameters", {})
        if "last_review_id" in context_params:
            review_id = context_params["last_review_id"]
            print(f"Found review_id in context {context['name']}: {review_id}")
            break
    
    # Fallback: thử lấy từ parameters nếu không tìm thấy trong contexts
    if review_id is None:
        review_id = parameters.get("last_review_id")
        print(f"Review_id from parameters: {review_id}")
    
    print(f"Final review_id to delete: {review_id}")
    
    # Xóa review nếu có review_id
    if review_id:
        try:
            db_helper.delete_review_by_id(review_id)
            print(f"Successfully deleted review with ID: {review_id}")
        except Exception as e:
            print(f"Error deleting review {review_id}: {str(e)}")
    else:
        print("No review_id found to delete")
    
    fulfillment_text = ("No problem, John! I've canceled the review process. "
                        "If you need help with something else, like tracking orders or finding new products.")
    
    # Tạo session path để xóa các context liên quan
    session_path = session_id.split('/sessions/')[0] + '/sessions/' + session_id.split('/sessions/')[1]
    
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def submit_review_select_different_product(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None

    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    product_details = db_helper.get_product_details(product)
    if product_details:
        product_details = list(product_details)
        product_details[1] = float(product_details[1])  # Chuyển đổi Decimal thành float

    product_names = [p[0] for p in unreviewed_products]
    if not product_details or product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                           f"Please choose from: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": [p[0] for p in unreviewed_products]}
            }]
        })

    name, price, _, _, _, brand, category = product_details
    fulfillment_text = (f"Thanks for letting me know, John! For {name} (${price}, {brand} brand, {category} category): "
                       f"Rating: Would you like to give it a rating from 1 to 5 stars? "
                       f"Comment: "
                       f"Please confirm or provide additional details, and I’ll submit the review for you, or say 'cancel' to exit.")
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [{
            "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
            "lifespanCount": 5,
            "parameters": {
                "product": product,
                "unreviewed_products": [p[0] for p in unreviewed_products]
            }
        }]
    })