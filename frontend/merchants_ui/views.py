import requests
from django.contrib import messages
from django.shortcuts import redirect, render

from . import services
from .forms import MerchantForm, ReasonForm
from .services import ApiUnavailableError

STATUS_CHOICES = [
    ("", "Todos"),
    ("draft", "Draft"),
    ("pending_analysis", "Pending analysis"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("blocked", "Blocked"),
]


def _api_unavailable(request):
    messages.error(
        request,
        "Não foi possível conectar à API de Merchants. Verifique se o container "
        "da API está em execução.",
    )


def _apply_api_errors_to_form(form, data):
    if isinstance(data, dict) and "detail" not in data:
        for field, errors in data.items():
            errors = errors if isinstance(errors, list) else [errors]
            if field in form.fields:
                for error in errors:
                    form.add_error(field, error)
            else:
                for error in errors:
                    form.add_error(None, f"{field}: {error}")
        return True
    return False


def merchant_list(request):
    status = request.GET.get("status", "")
    merchant_id = request.GET.get("id", "").strip()
    try:
        merchants = services.list_merchants(status or None, merchant_id or None)
    except ApiUnavailableError:
        _api_unavailable(request)
        merchants = []
    except requests.exceptions.HTTPError:
        messages.error(request, "Erro ao consultar a API de Merchants.")
        merchants = []

    return render(
        request,
        "merchants_ui/list.html",
        {
            "merchants": merchants,
            "status_choices": STATUS_CHOICES,
            "selected_status": status,
            "merchant_id": merchant_id,
        },
    )


def merchant_detail(request, pk):
    try:
        merchant = services.get_merchant(pk)
    except ApiUnavailableError:
        _api_unavailable(request)
        return redirect("merchant_list")
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            messages.error(request, "Merchant não encontrado.")
        else:
            messages.error(request, "Erro ao consultar a API de Merchants.")
        return redirect("merchant_list")

    return render(
        request,
        "merchants_ui/detail.html",
        {
            "merchant": merchant,
            "reject_form": ReasonForm(),
            "block_form": ReasonForm(),
        },
    )


def merchant_create(request):
    if request.method == "POST":
        form = MerchantForm(request.POST)
        if form.is_valid():
            try:
                response = services.create_merchant(form.cleaned_data)
            except ApiUnavailableError:
                _api_unavailable(request)
                return render(request, "merchants_ui/form.html", {"form": form, "title": "Novo Merchant"})

            if response.status_code == 201:
                merchant = response.json()
                messages.success(request, "Merchant cadastrado com sucesso.")
                return redirect("merchant_detail", pk=merchant["id"])

            data = response.json()
            if not _apply_api_errors_to_form(form, data):
                for msg in services.format_errors(data):
                    messages.error(request, msg)
    else:
        form = MerchantForm()

    return render(request, "merchants_ui/form.html", {"form": form, "title": "Novo Merchant"})


def merchant_edit(request, pk):
    try:
        merchant = services.get_merchant(pk)
    except ApiUnavailableError:
        _api_unavailable(request)
        return redirect("merchant_list")
    except requests.exceptions.HTTPError:
        messages.error(request, "Merchant não encontrado.")
        return redirect("merchant_list")

    if merchant["status"] != "draft":
        messages.error(
            request,
            "Só é possível editar os dados cadastrais enquanto o merchant "
            "estiver em draft.",
        )
        return redirect("merchant_detail", pk=pk)

    if request.method == "POST":
        form = MerchantForm(request.POST)
        if form.is_valid():
            try:
                response = services.update_merchant(pk, form.cleaned_data)
            except ApiUnavailableError:
                _api_unavailable(request)
                return render(
                    request,
                    "merchants_ui/form.html",
                    {"form": form, "title": "Editar Merchant"},
                )

            if response.status_code == 200:
                messages.success(request, "Merchant atualizado com sucesso.")
                return redirect("merchant_detail", pk=pk)

            data = response.json()
            if not _apply_api_errors_to_form(form, data):
                for msg in services.format_errors(data):
                    messages.error(request, msg)
    else:
        initial = {**merchant, "cnpj": services.format_cnpj(merchant["cnpj"])}
        form = MerchantForm(initial=initial)

    return render(request, "merchants_ui/form.html", {"form": form, "title": "Editar Merchant"})


def _run_transition(request, pk, service_func, *args):
    if request.method != "POST":
        return redirect("merchant_detail", pk=pk)

    try:
        response = service_func(pk, *args)
    except ApiUnavailableError:
        _api_unavailable(request)
        return redirect("merchant_detail", pk=pk)

    if response.status_code == 200:
        messages.success(request, "Operação realizada com sucesso.")
    else:
        data = response.json()
        for msg in services.format_errors(data):
            messages.error(request, msg)

    return redirect("merchant_detail", pk=pk)


def merchant_submit_for_analysis(request, pk):
    return _run_transition(request, pk, lambda merchant_id: services.submit_for_analysis(merchant_id))


def merchant_approve(request, pk):
    return _run_transition(request, pk, lambda merchant_id: services.approve(merchant_id))


def merchant_reject(request, pk):
    if request.method != "POST":
        return redirect("merchant_detail", pk=pk)

    form = ReasonForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe um motivo para rejeitar.")
        return redirect("merchant_detail", pk=pk)

    return _run_transition(request, pk, services.reject, form.cleaned_data["reason"])


def merchant_block(request, pk):
    if request.method != "POST":
        return redirect("merchant_detail", pk=pk)

    form = ReasonForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Informe um motivo para bloquear.")
        return redirect("merchant_detail", pk=pk)

    return _run_transition(request, pk, services.block, form.cleaned_data["reason"])
