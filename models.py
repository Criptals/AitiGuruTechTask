from pydantic import BaseModel


class AddItemRequest(BaseModel):
    """
    Request model for adding an item to an order.
    """
    order_id: str
    nomenclature_id: str
    quantity: int


class AddItemResponse(BaseModel):
    """
    Response model after successfully adding an item.
    """
    success: bool
    message: str