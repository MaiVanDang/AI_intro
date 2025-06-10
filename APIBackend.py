from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from datetime import datetime
import logging
from main import handle_request as handle_chatbot_request
import db_helper


try:
    import db_helper
    import generic_helper
except ImportError:
    db_helper = None
    generic_helper = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Order Management API", 
    version="1.0.0",
    description="API for managing orders and customer information"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class OrderResponse(BaseModel):
    order_id: int
    product_names: str
    total_amount: float
    payment_method: str
    order_status: str
    order_date: datetime

class CustomerInfo(BaseModel):
    customer_id: int
    name: str
    email: str
    phone: str

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    stock: int
    rating: float

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("home", exist_ok=True)

# FIXED: Mount static files with proper configuration
@app.on_event("startup")
async def startup_event():
    """Initialize static file mounting on startup"""
    try:
        # Ensure directories exist and have some content
        if not os.path.exists("static"):
            os.makedirs("static")
            # Create a simple index.html if it doesn't exist
            if not os.path.exists("static/index.html"):
                with open("static/index.html", "w", encoding="utf-8") as f:
                    f.write("""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Static Files Test</title>
</head>
<body>
    <h1>Static Files Working!</h1>
    <p>This is served from /static/ directory</p>
</body>
</html>
                    """)
        
        if not os.path.exists("home"):
            os.makedirs("home")
            # Create a simple index.html if it doesn't exist
            if not os.path.exists("home/index.html"):
                with open("home/index.html", "w", encoding="utf-8") as f:
                    f.write("""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Directory Test</title>
</head>
<body>
    <h1>Home Directory Working!</h1>
    <p>This is served from /home/ directory</p>
</body>
</html>
                    """)
        
        logger.info("Startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

# FIXED: Proper static files mounting
# Mount static files BEFORE defining routes
try:
    # Mount home directory first (for main interface)
    if os.path.exists("home") or True:  # Create if doesn't exist
        app.mount("/home", StaticFiles(directory="home", html=True), name="home")
        logger.info("✅ Mounted /home directory successfully")
    
    # Mount static directory (for assets like CSS, JS, images)
    if os.path.exists("static") or True:  # Create if doesn't exist
        app.mount("/static", StaticFiles(directory="static", html=True), name="static")
        logger.info("✅ Mounted /static directory successfully")
        
except Exception as e:
    logger.error(f"❌ Error mounting static files: {e}")

# API Routes
@app.post("/")
async def chatbot_webhook(request: Request):
    try:
        # Chuyển tiếp request sang handle_request trong main.py
        return await handle_chatbot_request(request)
    except Exception as e:
        logger.error(f"Error in chatbot webhook: {e}")
        return JSONResponse(content={
            "fulfillmentText": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "source": "shopdb-webhook"
        }, status_code=500)

@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    price_range: Optional[str] = None
):
    try:
        # Gọi hàm từ db_helper để lấy sản phẩm
        products = db_helper.search_products(category=category, brand=None)
        
        # Xử lý filter thêm nếu cần
        filtered_products = []
        for product in products:
            filtered_products.append({
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "category": product["category"],
                "stock": product["stock"],
                "rating": product["rating"]
            })
        
        return filtered_products
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# FIXED: Main page route - moved after static mounting
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the main HTML interface"""
    try:
        # Try to read from home folder first
        if os.path.exists("home/index.html"):
            with open("home/index.html", "r", encoding="utf-8") as f:
                content = f.read()
                logger.info("✅ Serving from home/index.html")
                return HTMLResponse(content=content)
        # If not in home folder, try static directory
        elif os.path.exists("static/index.html"):
            with open("static/index.html", "r", encoding="utf-8") as f:
                content = f.read()
                logger.info("✅ Serving from static/index.html")
                return HTMLResponse(content=content)
        else:
            # Fallback HTML with better styling and diagnostics
            logger.warning("⚠️  No index.html found, serving fallback page")
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Order Management System</title>
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        max-width: 1000px; 
                        margin: 0 auto; 
                        padding: 20px; 
                        background: #f5f5f5;
                        line-height: 1.6;
                    }}
                    .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .status-box {{ padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid; }}
                    .error {{ background: #ffeaea; border-left-color: #e74c3c; color: #c0392b; }}
                    .info {{ background: #e8f4fd; border-left-color: #3498db; color: #2980b9; }}
                    .success {{ background: #eafaf1; border-left-color: #27ae60; color: #229954; }}
                    .warning {{ background: #fef9e7; border-left-color: #f39c12; color: #d68910; }}
                    .test-links {{ margin: 25px 0; }}
                    .test-links a {{ 
                        display: inline-block; 
                        margin: 8px 10px; 
                        padding: 12px 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 25px; 
                        transition: transform 0.2s;
                        font-weight: 500;
                    }}
                    .test-links a:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
                    ul {{ margin: 15px 0; padding-left: 25px; }}
                    li {{ margin: 8px 0; }}
                    code {{ background: #f8f9fa; padding: 2px 6px; border-radius: 4px; font-family: 'Courier New', monospace; }}
                    h1 {{ color: #2c3e50; margin-bottom: 10px; }}
                    h3 {{ color: #34495e; margin-top: 25px; margin-bottom: 15px; }}
                    .emoji {{ font-size: 1.2em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1><span class="emoji">🛍️</span> Order Management System</h1>
                    
                    <div class="status-box warning">
                        <h3><span class="emoji">⚠️</span> HTML Interface Not Found</h3>
                        <p><strong>Hệ thống đang chạy nhưng không tìm thấy giao diện HTML chính.</strong></p>
                        <p>Vui lòng tạo file HTML trong một trong các vị trí sau:</p>
                        <ul>
                            <li><code>home/index.html</code> (khuyến nghị)</li>
                            <li><code>static/index.html</code></li>
                        </ul>
                    </div>
                    
                    <div class="status-box success">
                        <h3><span class="emoji">✅</span> Trạng thái thư mục:</h3>
                        <ul>
                            <li>Thư mục <code>home/</code> tồn tại: <strong>{"Có" if os.path.exists("home") else "Không"}</strong></li>
                            <li>Thư mục <code>static/</code> tồn tại: <strong>{"Có" if os.path.exists("static") else "Không"}</strong></li>
                            <li>Working Directory: <code>{os.getcwd()}</code></li>
                        </ul>
                    </div>
                    
                    <div class="test-links">
                        <h3><span class="emoji">🔗</span> Kiểm tra liên kết:</h3>
                        <a href="/home/" target="_blank">Test /home/</a>
                        <a href="/static/" target="_blank">Test /static/</a>
                        <a href="/api/products" target="_blank">Test API</a>
                        <a href="/docs" target="_blank">API Docs</a>
                        <a href="/health" target="_blank">Health Check</a>
                        <a href="/debug/files" target="_blank">Debug Files</a>
                    </div>
                    
                    <div class="status-box info">
                        <h3><span class="emoji">📚</span> API Endpoints có sẵn:</h3>
                        <ul>
                            <li><strong>GET /api/orders?customer_id={{id}}</strong> - Lấy đơn hàng theo ID khách hàng</li>
                            <li><strong>GET /api/orders?customer_name={{name}}</strong> - Lấy đơn hàng theo tên khách hàng</li>
                            <li><strong>GET /api/customer/{{customer_id}}</strong> - Lấy thông tin khách hàng theo ID</li>
                            <li><strong>GET /api/customer/search?email={{email}}&phone={{phone}}</strong> - Tìm kiếm khách hàng</li>
                            <li><strong>POST /</strong> - Chatbot webhook endpoint</li>
                            <li><strong>POST /chatbot</strong> - Chatbot endpoint</li>
                            <li><strong>GET /docs</strong> - Interactive API Documentation</li>
                            <li><strong>GET /health</strong> - Health check</li>
                        </ul>
                    </div>
                    
                    <div class="status-box info">
                        <h3><span class="emoji">🤖</span> Tích hợp Chatbot:</h3>
                        <p>Chatbot webhook có sẵn tại <code>/chatbot</code> để tích hợp với Dialogflow.</p>
                    </div>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving homepage: {e}")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>❌ Error loading homepage</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Working Directory:</strong> {os.getcwd()}</p>
            <a href="/debug/files">🔍 Debug File Structure</a>
        </body>
        </html>
        """, status_code=500)

@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(customer_id: Optional[int] = None, customer_name: Optional[str] = None):
    if not db_helper or not hasattr(db_helper, "get_customer_orders"):
        raise HTTPException(status_code=503, detail="Database service unavailable")

    try:
        if not customer_id and not customer_name:
            raise HTTPException(status_code=400, detail="Either customer_id or customer_name must be provided")

        if customer_id:
            logger.info(f"Getting orders for customer_id: {customer_id}")
            orders = db_helper.get_customer_orders(customer_id=customer_id)
        else:
            logger.info(f"Getting orders for customer_name: {customer_name}")
            orders = db_helper.get_customer_orders(customer_name=customer_name)

        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for this customer")

        # Format the orders to match OrderResponse model
        formatted_orders = []
        for order in orders:
            if not isinstance(order, dict):
                    logger.error(f"Unexpected order format: {order}")
                    continue
            formatted_orders.append({
                "order_id": order.get("order_id") or order.get("Order_ID"),
                "product_names": order.get("product_names") or order.get("Product_Names"),
                "total_amount": order.get("total_amount") or order.get("Total_Amount"),
                "payment_method": order.get("payment_method") or order.get("Payment_Method"),
                "order_status": order.get("order_status") or order.get("Order_Status"),
                "order_date": order.get("order_date") or order.get("Order_Date")
            })
        return formatted_orders

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/api/customer/{customer_id}", response_model=CustomerInfo)
async def get_customer(customer_id: int):
    """Get customer information by ID"""
    try:
        if not db_helper or not hasattr(db_helper, "get_customer_info"):
            raise HTTPException(status_code=503, detail="Database service unavailable")
            
        logger.info(f"Getting customer info for ID: {customer_id}")
        customer_data = db_helper.get_customer_info(customer_id)
        
        if not customer_data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerInfo(
            customer_id=customer_id,
            name=customer_data[0],
            email=customer_data[1],
            phone=customer_data[2]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/customer/search")
async def search_customer(email: Optional[str] = None, phone: Optional[str] = None):
    """Search customer by email or phone"""
    try:
        if not email and not phone:
            raise HTTPException(status_code=400, detail="Either email or phone must be provided")
        
        if not db_helper or not hasattr(db_helper, "get_customer_by_email_or_phone"):
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        logger.info(f"Searching customer by email: {email}, phone: {phone}")
        customer_result = db_helper.get_customer_by_email_or_phone(email or "", phone or "")
        
        if not customer_result:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_id = customer_result[0]
        customer_info = db_helper.get_customer_info(customer_id)
        
        return CustomerInfo(
            customer_id=customer_id,
            name=customer_info[0],
            email=customer_info[1],
            phone=customer_info[2]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching customer: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Chatbot webhook endpoint
@app.post("/chatbot")
async def chatbot_webhook(request: Request):
    """Handle Dialogflow webhook requests"""
    try:
        payload = await request.json()
        logger.info(f"Received chatbot request: {payload}")
        
        # Extract intent and parameters
        intent = payload.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = payload.get('queryResult', {}).get('parameters', {})
        query_text = payload.get('queryResult', {}).get('queryText', '')
        
        # Simple response logic - you can expand this
        response_text = "Xin chào! Tôi là trợ lý ảo của ShopDB. Tôi có thể giúp bạn tra cứu thông tin đơn hàng."
        
        if 'đơn hàng' in query_text.lower() or 'order' in query_text.lower():
            response_text = "Để tra cứu đơn hàng, bạn có thể cung cấp ID khách hàng hoặc tên khách hàng. Ví dụ: 'Tôi muốn xem đơn hàng của khách hàng có ID 123'"
        
        elif 'khách hàng' in query_text.lower() or 'customer' in query_text.lower():
            response_text = "Tôi có thể giúp bạn tìm kiếm thông tin khách hàng theo email hoặc số điện thoại."
        
        return JSONResponse(content={
            "fulfillmentText": response_text,
            "source": "shopdb-webhook"
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot webhook: {e}")
        return JSONResponse(content={
            "fulfillmentText": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
            "source": "shopdb-webhook"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if database functions are available
        db_status = "available" if db_helper and hasattr(db_helper, "get_customer_orders") else "unavailable"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "database": db_status,
            "version": "1.0.0",
            "directories": {
                "home": os.path.exists("home"),
                "static": os.path.exists("static"),
                "home_files": os.listdir("home") if os.path.exists("home") else [],
                "static_files": os.listdir("static") if os.path.exists("static") else []
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(content={
            "status": "unhealthy",  
            "error": str(e),
            "timestamp": datetime.now()
        }, status_code=500)

# ENHANCED: Debug endpoints to check static files
@app.get("/debug/files")
async def debug_files():
    """Debug endpoint to check file structure"""
    try:
        current_dir = os.getcwd()
        files_info = {
            "current_directory": current_dir,
            "home_exists": os.path.exists("home"),
            "static_exists": os.path.exists("static"),
            "home_files": [],
            "static_files": [],
            "directory_contents": {}
        }
        
        # Get home directory contents
        if os.path.exists("home"):
            try:
                files_info["home_files"] = os.listdir("home")
                files_info["directory_contents"]["home"] = {}
                for file in files_info["home_files"]:
                    file_path = os.path.join("home", file)
                    if os.path.isfile(file_path):
                        try:
                            files_info["directory_contents"]["home"][file] = {
                                "size": os.path.getsize(file_path),
                                "is_file": True
                            }
                        except Exception as e:
                            files_info["directory_contents"]["home"][file] = {"error": str(e)}
            except Exception as e:
                files_info["home_error"] = str(e)
        
        # Get static directory contents  
        if os.path.exists("static"):
            try:
                files_info["static_files"] = os.listdir("static")
                files_info["directory_contents"]["static"] = {}
                for file in files_info["static_files"]:
                    file_path = os.path.join("static", file)
                    if os.path.isfile(file_path):
                        try:
                            files_info["directory_contents"]["static"][file] = {
                                "size": os.path.getsize(file_path),
                                "is_file": True
                            }
                        except Exception as e:
                            files_info["directory_contents"]["static"][file] = {"error": str(e)}
            except Exception as e:
                files_info["static_error"] = str(e)
            
        return files_info
        
    except Exception as e:
        return {"error": str(e), "current_directory": os.getcwd()}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "path": str(request.url),
            "timestamp": datetime.now().isoformat(),
            "suggestion": "Try /docs for API documentation or /debug/files to check file structure"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Order Management API Server...")
    print("📱 Access the interface at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🤖 Chatbot webhook at: http://localhost:8000/chatbot")
    print("❤️  Health check at: http://localhost:8000/health")
    print("🔍 Debug files at: http://localhost:8000/debug/files")
    print("🏠 Home static files: http://localhost:8000/home/")
    print("📁 Static files: http://localhost:8000/static/")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)