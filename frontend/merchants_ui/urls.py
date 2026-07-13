from django.urls import path

from . import views

urlpatterns = [
    path("", views.merchant_list, name="merchant_list"),
    path("novo/", views.merchant_create, name="merchant_create"),
    path("<int:pk>/", views.merchant_detail, name="merchant_detail"),
    path("<int:pk>/editar/", views.merchant_edit, name="merchant_edit"),
    path(
        "<int:pk>/enviar-para-analise/",
        views.merchant_submit_for_analysis,
        name="merchant_submit_for_analysis",
    ),
    path("<int:pk>/aprovar/", views.merchant_approve, name="merchant_approve"),
    path("<int:pk>/rejeitar/", views.merchant_reject, name="merchant_reject"),
    path("<int:pk>/bloquear/", views.merchant_block, name="merchant_block"),
]
