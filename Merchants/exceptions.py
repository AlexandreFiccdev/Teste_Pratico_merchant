from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessRuleError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Regra de negócio violada."
    default_code = "business_rule_error"
