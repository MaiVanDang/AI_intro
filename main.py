from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
from datetime import datetime
from decimal import Decimal

app = FastAPI()

inprogress_orders = {}
customer_id = 1  # Giả sử customer_id cố định là 1 (John Doe), sau này có thể lấy từ session

# Hàm hỗ trợ để chuyển đổi Decimal thành float trong danh sách sản phẩm
def convert_decimals_to_floats(product_list):
    return [
        (item[0], float(item[1]), item[2], item[3], item[4], item[5], item[6])
        if len(item) >= 7 else (item[0], float(item[1]), item[2], item[3])
        for item in product_list
    ]

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    intent_handler_dict = {
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

def submit_review_start(parameters: dict, output_contexts: list, session_id: str):
    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None

    if not unreviewed_products:
        fulfillment_text = "It looks like you haven’t purchased any products yet, or all your products are already reviewed!"
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": []
        })

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
            return JSONResponse(content={
                "fulfillmentText": fulfillment_text,
                "outputContexts": [{
                    "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                    "lifespanCount": 5,
                    "parameters": {"product": product, "unreviewed_products": [p[0] for p in unreviewed_products]}
                }]
            })
        else:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
            fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                               f"Please choose from the following unreviewed products: {product_list}, or say 'cancel' to exit.")
    else:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Awesome, we’d love to hear your feedback! Based on your order history, "
                           f"here are your unreviewed products: {product_list}. "
                           f"Please specify which product you’d like to review (e.g., 'Product 1'), or say 'cancel' to exit.")

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [{
            "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
            "lifespanCount": 5,
            "parameters": {"unreviewed_products": [p[0] for p in unreviewed_products]}
        }]
    })

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
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": [p[0] for p in unreviewed_products]}
            }]
        })

    product_details = db_helper.get_product_details(product)
    if product_details:
        product_details = list(product_details)
        product_details[1] = float(product_details[1])  # Chuyển đổi Decimal thành float
    product_names = [p[0] for p in unreviewed_products]
    if not product_details or product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Sorry, {product} is either not in your purchase history or has not been delivered yet. "
                           f"Please choose from your unreviewed products: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": [p[0] for p in unreviewed_products]}
            }]
        })

    name, price, _, _, _, brand, category = product_details
    fulfillment_text = (f"Thanks for sharing, John! For {name} (${price}, {brand} brand, {category} category): "
                       f"Rating: Would you like to give it a rating from 1 to 5 stars? "
                       f"Comment: {initial_comment} "
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

def submit_review_details_collect(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product")
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
                product = params.get("product")
                break

    product_names = [p[0] for p in unreviewed_products]
    if not product or product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        if not unreviewed_products:
            fulfillment_text = "It looks like you haven’t purchased any products yet, or all your products are already reviewed!"
        else:
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

    if not rating:
        fulfillment_text = f"Please provide a rating from 1 to 5 stars for {product}, or say 'cancel' to exit."
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

    # Chuyển rating thành float để đảm bảo giá trị hợp lệ
    try:
        rating = float(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        fulfillment_text = f"Please provide a valid rating from 1 to 5 stars for {product}, or say 'cancel' to exit."
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

    fulfillment_text = (f"Here’s your review for {product}: "
                       f"Rating: {rating}/5 "
                       f"Comment: {comment} "
                       f"Would you like to edit your rating or comment before I submit it? Or say 'submit it now' to proceed, or 'cancel' to exit.")
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [{
            "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_confirm",
            "lifespanCount": 5,
            "parameters": {
                "product": product,
                "rating": rating,
                "comment": comment,
                "unreviewed_products": [p[0] for p in unreviewed_products]
            }
        }]
    })

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
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": [p[0] for p in full_unreviewed_products]}
            }]
        })

    fulfillment_text = (f"I’ve updated your review for {product}: "
                       f"Rating: {rating}/5 "
                       f"Comment: {comment} "
                       f"Would you like to make more changes, or say 'submit it now' to proceed, or 'cancel' to exit?")
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [{
            "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_confirm",
            "lifespanCount": 5,
            "parameters": {
                "product": product,
                "rating": rating,
                "comment": comment,
                "unreviewed_products": unreviewed_products  # Giữ nguyên danh sách
            }
        }]
    })

def submit_review_submit(parameters: dict, output_contexts: list, session_id: str):
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

    if isinstance(product, list):
        product = product[0] if product else None
    if isinstance(rating, list):
        rating = rating[0] if rating else None
    if isinstance(comment, list):
        comment = comment[0] if comment else ""
    if isinstance(unreviewed_products, list):
        unreviewed_products = unreviewed_products if unreviewed_products else []

    # Nếu unreviewed_products rỗng, lấy lại từ database để kiểm tra
    if not unreviewed_products:
        full_unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        full_unreviewed_products = convert_decimals_to_floats(full_unreviewed_products)
        unreviewed_products = [p[0] for p in full_unreviewed_products]
    else:
        full_unreviewed_products = db_helper.get_unreviewed_products(customer_id)
        full_unreviewed_products = convert_decimals_to_floats(full_unreviewed_products)

    # Kiểm tra product và rating
    if not product or not rating:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in full_unreviewed_products])
        fulfillment_text = (f"Sorry, I couldn’t submit the review for {product}. Please provide a rating and product, or choose from: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": unreviewed_products}
            }]
        })

    # Xác nhận sản phẩm hợp lệ nếu có unreviewed_products
    product_names = [p[0] for p in full_unreviewed_products]
    if product not in product_names:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in full_unreviewed_products])
        fulfillment_text = (f"Sorry, I couldn’t submit the review for {product}. It’s either not in your purchase history or has not been delivered yet. "
                           f"Please choose from: {product_list}, or say 'cancel' to exit.")
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
                "lifespanCount": 5,
                "parameters": {"unreviewed_products": unreviewed_products}
            }]
        })

    try:
        db_helper.insert_review(product, customer_id, rating, comment)
        review_date = datetime.now().strftime("%Y-%m-d")
        # Cập nhật unreviewed_products để loại bỏ sản phẩm đã reviewed
        if product in unreviewed_products:
            unreviewed_products = [p for p in unreviewed_products if p != product]
        fulfillment_text = (f"Perfect! Here’s the review for {product}: "
                           f"Rating: {rating}/5 "
                           f"Comment: {comment} "
                           f"Customer: John Doe "
                           f"Review Date: {review_date} "
                           f"I’ve submitted the review, and it’ll appear on the product page soon. "
                           f"Your review will help other customers a lot! "
                           f"Would you like to review another product or need help with something else, or say 'cancel' to exit?")
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_finalize",
                "lifespanCount": 5,
                "parameters": {
                    "unreviewed_products": unreviewed_products
                }
            }]
        })
    except Exception as e:
        fulfillment_text = f"Error: Failed to save review to database. Debug info - error: {str(e)}. Please try again, or say 'cancel' to exit."
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": [{
                "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_confirm",
                "lifespanCount": 5,
                "parameters": {
                    "product": product,
                    "rating": rating,
                    "comment": comment,
                    "unreviewed_products": unreviewed_products
                }
            }]
        })

def submit_review_continue(parameters: dict, output_contexts: list, session_id: str):
    product = parameters.get("product")
    if isinstance(product, list):
        product = product[0] if product else None

    unreviewed_products = db_helper.get_unreviewed_products(customer_id)
    unreviewed_products = convert_decimals_to_floats(unreviewed_products)

    if not unreviewed_products:
        fulfillment_text = "It looks like you’ve reviewed all your purchased products! If you need help with something else, just let me know, or say 'cancel' to exit."
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text,
            "outputContexts": []
        })

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
        else:
            product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
            fulfillment_text = (f"Sorry, {product} is either not in your purchase history, has not been delivered yet, or has already been reviewed. "
                               f"Please choose from the following unreviewed products: {product_list}, or say 'cancel' to exit.")
    else:
        product_list = ", ".join([f"{p[0]} (${p[1]}, {p[2]} brand, {p[3]} category)" for p in unreviewed_products])
        fulfillment_text = (f"Great! Based on your order history, here are your remaining unreviewed products: {product_list}. "
                           f"Please specify which product you’d like to review (e.g., 'Product 1'), or say 'cancel' to exit.")

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": [{
            "name": f"projects/{session_id}/agent/sessions/{session_id}/contexts/submit_review_active",
            "lifespanCount": 5,
            "parameters": {"unreviewed_products": [p[0] for p in unreviewed_products]}
        }]
    })

def submit_review_end(parameters: dict, output_contexts: list, session_id: str):
    fulfillment_text = ("You’re welcome, John! Thanks for taking the time to share your review. "
                       "If you need help with anything else, like tracking orders or finding new products, "
                       "just let me know, or say 'cancel' to exit.")
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": []
    })

def submit_review_cancel(parameters: dict, output_contexts: list, session_id: str):
    fulfillment_text = ("No problem, John! I’ve canceled the review process. "
                       "If you need help with something else, like tracking orders or finding new products, "
                       "just let me know. Have a great day!")
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
        "outputContexts": []
    })

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