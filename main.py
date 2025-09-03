from fastapi import FastAPI, HTTPException
from models import AddItemRequest, AddItemResponse
from db import get_db_connection

app = FastAPI(title="Add Item to Order")

@app.post("/add-item")
async def add_item_to_order(request: AddItemRequest) -> AddItemResponse:
    """
    Adds a product to an order. If the item already exists, increases quantity.
    Updates the order's total amount.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Start transaction
        cursor.execute("BEGIN")

        # 1. Check if order exists and is open
        cursor.execute(
            "SELECT id FROM orders WHERE id = %s FOR UPDATE",
            (request.order_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")

        # 2. Check item availability with row locking
        cursor.execute(
            """SELECT quantity, price FROM nomenclature 
               WHERE id = %s AND quantity >= %s FOR UPDATE""",
            (request.nomenclature_id, request.quantity)
        )
        stock_item = cursor.fetchone()
        if not stock_item:
            raise HTTPException(status_code=400, detail="Not enough stock or item not found")
        
        available_quantity, unit_price = stock_item

        # 3. Check for existing item in order
        cursor.execute(
            """SELECT id, quantity, unit_price FROM order_items 
               WHERE order_id = %s AND nomenclature_id = %s FOR UPDATE""",
            (request.order_id, request.nomenclature_id)
        )
        existing = cursor.fetchone()

        total_price_adjustment = 0

        if existing:
            item_id, existing_quantity, existing_unit_price = existing
            
            # Verify unit price consistency
            if existing_unit_price != unit_price:
                raise HTTPException(status_code=409, detail="Item price has changed")
            
            new_quantity = existing_quantity + request.quantity
            additional_cost = request.quantity * unit_price
            
            # Update existing item
            cursor.execute(
                """UPDATE order_items 
                   SET quantity = %s, total_price = quantity * unit_price 
                   WHERE id = %s""",
                (new_quantity, item_id)
            )
            
            total_price_adjustment = additional_cost
            
        else:
            # Insert new item
            total_price = request.quantity * unit_price
            cursor.execute(
                """INSERT INTO order_items 
                   (order_id, nomenclature_id, quantity, unit_price, total_price) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (request.order_id, request.nomenclature_id, request.quantity, unit_price, total_price)
            )
            
            total_price_adjustment = total_price

        # 4. Update stock quantity
        cursor.execute(
            "UPDATE nomenclature SET quantity = quantity - %s WHERE id = %s",
            (request.quantity, request.nomenclature_id)
        )

        # 5. Update order total
        cursor.execute(
            "UPDATE orders SET total_amount = total_amount + %s WHERE id = %s",
            (total_price_adjustment, request.order_id)
        )

        conn.commit()
        return AddItemResponse(success=True, message="Item added to order")

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if conn:
            conn.close()