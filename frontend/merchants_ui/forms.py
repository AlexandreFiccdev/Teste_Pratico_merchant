from django import forms


class MerchantForm(forms.Form):
    cnpj = forms.CharField(label="CNPJ", max_length=18)
    razao_social = forms.CharField(label="Razão social", max_length=255)
    nome_fantasia = forms.CharField(label="Nome fantasia", max_length=255, required=False)
    email = forms.EmailField(label="E-mail")
    telefone = forms.CharField(label="Telefone", max_length=20, required=False)


class ReasonForm(forms.Form):
    reason = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 3}))
