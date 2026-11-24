from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler


class BusinessError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "business_error"
    default_detail = "Business rule violated."

    def __init__(self, code=None, message=None, details=None):
        self.code = code or self.default_code
        self.message = message or self.default_detail
        self.details = details or []
        super().__init__(detail=self.message, code=self.code)


class InsufficientStock(BusinessError):
    def __init__(self, shortages):
        super().__init__(
            code="insufficient_stock",
            message="Not enough stock to confirm the order.",
            details=shortages,
        )


class InvalidTransition(BusinessError):
    def __init__(self, current, target):
        super().__init__(
            code="invalid_status_transition",
            message=f"Cannot change order status from {current} to {target}.",
            details=[{"from": str(current), "to": str(target)}],
        )


class OrderNotEditable(BusinessError):
    def __init__(self):
        super().__init__(
            code="order_not_editable",
            message="Only DRAFT orders can be modified.",
        )


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, BusinessError):
        body = {"code": exc.code, "message": exc.message, "details": exc.details}
    elif isinstance(exc, ValidationError):
        body = {
            "code": "validation_error",
            "message": "Invalid input.",
            "details": response.data,
        }
    else:
        message = response.data.get("detail", "Request failed.") if isinstance(response.data, dict) else "Request failed."
        body = {
            "code": getattr(exc, "default_code", "error"),
            "message": str(message),
            "details": [],
        }
    response.data = body
    return respons