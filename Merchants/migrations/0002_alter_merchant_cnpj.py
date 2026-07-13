import Merchants.validators.CNPJ_validator
from django.db import migrations, models


def normalize_existing_cnpjs(apps, schema_editor):
    Merchant = apps.get_model('Merchants', 'Merchant')
    for merchant in Merchant.objects.all():
        normalized = Merchants.validators.CNPJ_validator.normalize_cnpj(merchant.cnpj)
        if normalized != merchant.cnpj:
            merchant.cnpj = normalized
            merchant.save(update_fields=['cnpj'])


class Migration(migrations.Migration):

    dependencies = [
        ('Merchants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_existing_cnpjs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='merchant',
            name='cnpj',
            field=models.CharField(max_length=14, unique=True, validators=[Merchants.validators.CNPJ_validator.validate_cnpj]),
        ),
    ]
