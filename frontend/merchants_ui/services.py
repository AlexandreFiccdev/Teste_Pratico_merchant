import re

import requests
from django.conf import settings

TIMEOUT = 5

class ApiUnavailableError(Exception):
    pass


def _url(path):
    return f"{settings.API_BASE_URL}{path}"


def _request(method, path, **kwargs):
    try:
        return requests.request(method, _url(path), timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise ApiUnavailableError(str(exc)) from exc


def list_merchants(status=None, merchant_id=None):
    params = {}
    if status:
        params["status"] = status
    if merchant_id:
        params["id"] = merchant_id
    response = _request("GET", "/merchants/", params=params)
    response.raise_for_status()
    return response.json()


def get_merchant(merchant_id):
    response = _request("GET", f"/merchants/{merchant_id}/")
    response.raise_for_status()
    return response.json()


def create_merchant(data):
    return _request("POST", "/merchants/", json=data)


def update_merchant(merchant_id, data):
    return _request("PATCH", f"/merchants/{merchant_id}/", json=data)


def submit_for_analysis(merchant_id):
    return _request("POST", f"/merchants/{merchant_id}/submit-for-analysis/")


def approve(merchant_id):
    return _request("POST", f"/merchants/{merchant_id}/approve/")


def reject(merchant_id, reason):
    return _request("POST", f"/merchants/{merchant_id}/reject/", json={"reason": reason})


def block(merchant_id, reason):
    return _request("POST", f"/merchants/{merchant_id}/block/", json={"reason": reason})


def format_cnpj(value):
    digits = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
    if len(digits) != 14:
        return value
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def format_errors(data):
    if isinstance(data, dict):
        if "detail" in data:
            return [str(data["detail"])]
        messages = []
        for field, errors in data.items():
            errors = errors if isinstance(errors, list) else [errors]
            for error in errors:
                messages.append(f"{field}: {error}")
        return messages
    return [str(data)]
