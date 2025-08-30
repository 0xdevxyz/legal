"""
Additional Payment Demo Endpoints for Complyo
Diese Datei enthält zusätzliche Payment-Endpoints die zu groß für einen Edit waren
"""

additional_payment_endpoints = '''

@app.get("/api/payments/demo-checkout/{session_id}")
async def demo_checkout_page(session_id: str):
    """Demo checkout page - simulates Stripe checkout"""
    
    # In a real app, this would redirect to Stripe
    # For demo, we return a simple HTML page
    
    demo_checkout_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complyo - Demo Checkout</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-purple-50">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl p-8 max-w-md w-full">
                <div class="text-center mb-6">
                    <h1 class="text-2xl font-bold text-gray-900 mb-2">Demo Checkout</h1>
                    <p class="text-gray-600">Session ID: {session_id}</p>
                </div>
                
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <p class="text-yellow-800 text-sm">
                        <strong>Demo Mode:</strong> This is a simulated checkout. 
                        No real payment will be processed.
                    </p>
                </div>
                
                <div class="space-y-4">
                    <button onclick="simulateSuccess()" 
                            class="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700">
                        ✅ Simulate Successful Payment
                    </button>
                    
                    <button onclick="simulateCancel()" 
                            class="w-full bg-gray-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-gray-700">
                        ❌ Simulate Cancelled Payment
                    </button>
                </div>
                
                <div class="mt-6 text-center">
                    <p class="text-sm text-gray-500">
                        In production, this would be the actual Stripe checkout page.
                    </p>
                </div>
            </div>
        </div>
        
        <script>
        function simulateSuccess() {
            alert('✅ Payment simulation successful!\\nRedirecting to success page...');
            // In real app: redirect to success_url with session_id
            window.location.href = '/api/payments/demo-success/{session_id}';
        }
        
        function simulateCancel() {
            alert('❌ Payment cancelled by user.\\nRedirecting to cancel page...');
            // In real app: redirect to cancel_url
            window.location.href = '/api/payments/demo-cancel';
        }
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=demo_checkout_html)

@app.get("/api/payments/demo-success/{session_id}")
async def demo_payment_success(session_id: str):
    """Demo payment success page"""
    
    # Simulate successful payment processing
    subscription_id = f"sub_demo_{uuid.uuid4().hex[:16]}"
    customer_id = f"cus_demo_{uuid.uuid4().hex[:12]}"
    
    # Store mock subscription
    mock_subscriptions[subscription_id] = {
        "subscription_id": subscription_id,
        "customer_id": customer_id,
        "session_id": session_id,
        "status": "active",
        "created_at": datetime.now(),
        "current_period_start": datetime.now(),
        "current_period_end": datetime.now().replace(day=28),  # End of month
        "plan_name": "Complyo AI Automation",
        "amount": 3900
    }
    
    success_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful - Complyo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-green-50 to-blue-50">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl p-8 max-w-md w-full text-center">
                <div class="text-6xl mb-4">🎉</div>
                <h1 class="text-2xl font-bold text-green-600 mb-2">Payment Successful!</h1>
                <p class="text-gray-600 mb-6">Your Complyo subscription has been activated.</p>
                
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                    <p class="text-green-800 text-sm">
                        <strong>Subscription ID:</strong> {subscription_id}<br>
                        <strong>Status:</strong> Active<br>
                        <strong>Plan:</strong> AI Automation (39€/month)
                    </p>
                </div>
                
                <button onclick="window.location.href='https://3010-iqtxqhmde36ooi6emqnp2.e2b.dev/'" 
                        class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700">
                    🚀 Go to Dashboard
                </button>
                
                <div class="mt-4">
                    <a href="https://3005-iqtxqhmde36ooi6emqnp2.e2b.dev/" 
                       class="text-blue-600 hover:underline text-sm">
                        ← Back to Landing Page
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=success_html)

@app.get("/api/payments/demo-cancel")
async def demo_payment_cancel():
    """Demo payment cancel page"""
    
    cancel_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled - Complyo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-gray-50 to-red-50">
        <div class="min-h-screen flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl p-8 max-w-md w-full text-center">
                <div class="text-6xl mb-4">😔</div>
                <h1 class="text-2xl font-bold text-gray-700 mb-2">Payment Cancelled</h1>
                <p class="text-gray-600 mb-6">Your payment was cancelled. You can try again anytime.</p>
                
                <div class="space-y-3">
                    <button onclick="window.location.href='https://3005-iqtxqhmde36ooi6emqnp2.e2b.dev/'" 
                            class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700">
                        🔄 Try Again
                    </button>
                    
                    <button onclick="window.location.href='https://3010-iqtxqhmde36ooi6emqnp2.e2b.dev/'" 
                            class="w-full bg-gray-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-gray-700">
                        📊 View Dashboard
                    </button>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=cancel_html)

@app.get("/api/payments/subscription/{customer_id}")
async def get_subscription_info(customer_id: str):
    """Get active subscription information für einen Kunden"""
    
    # Find subscription by customer_id
    for sub in mock_subscriptions.values():
        if sub["customer_id"] == customer_id:
            return {
                "subscription_id": sub["subscription_id"],
                "customer_id": sub["customer_id"],
                "status": sub["status"],
                "current_period_start": sub["current_period_start"],
                "current_period_end": sub["current_period_end"],
                "plan_name": sub["plan_name"],
                "amount": sub["amount"]
            }
    
    raise HTTPException(status_code=404, detail="No active subscription found")

@app.post("/api/payments/cancel-subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str):
    """Cancel subscription at period end"""
    
    if subscription_id in mock_subscriptions:
        mock_subscriptions[subscription_id]["status"] = "cancel_at_period_end"
        return {
            "subscription_id": subscription_id,
            "status": "cancel_at_period_end",
            "message": "Subscription will be cancelled at the end of the current period"
        }
    
    raise HTTPException(status_code=404, detail="Subscription not found")

'''

# Diese Endpoints werden später in die main backend Datei eingefügt