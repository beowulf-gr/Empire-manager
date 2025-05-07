from django import forms
from django.forms import formset_factory
from .models import LandUnit, LandUnitType

class RealmInfoForm(forms.Form):
    name = forms.CharField(max_length=100)
    ruler = forms.CharField(max_length=100)

class TreasuryForm(forms.Form):
    treasury = forms.IntegerField(min_value=0)

class ResourcesForm(forms.Form):
    food = forms.IntegerField(min_value=0)
    wood = forms.IntegerField(min_value=0)
    stone = forms.IntegerField(min_value=0)  

# class LandUnitForm(forms.ModelForm):
#     class Meta:
#         model = LandUnit
#         fields = ['name', 'unit_type']  # Add other fields if desired

#     unit_type = forms.ModelChoiceField(
#         queryset=LandUnitType.objects.all(),
#         empty_label="Select a Land Type"
#     )

from django import forms
from .models import LandUnit, LandUnitType
import ast

class LandUnitForm(forms.ModelForm):
    unit_type = forms.ModelChoiceField(
        queryset=LandUnitType.objects.all(),
        empty_label="Select a Land Type",
        widget=forms.Select(attrs={'id': 'id_unit_type'})  # Add id for JS targeting
    )
    production_choice = forms.ChoiceField(
        choices=[],
        required=False,
        label="Production Option",
        widget=forms.Select(attrs={'id': 'id_production_choice'})  # Add id for JS targeting
    )

    class Meta:
        model = LandUnit
        fields = ['name', 'unit_type', 'production_choice']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        unit_type = None

        # Populate choices if POST data exists
        if 'unit_type' in self.data:
            try:
                unit_type_id = int(self.data.get('unit_type'))
                unit_type = LandUnitType.objects.get(pk=unit_type_id)
            except (ValueError, LandUnitType.DoesNotExist):
                pass
        elif self.instance.pk:
            unit_type = self.instance.unit_type

        if unit_type and unit_type.choices:
            choices = unit_type.choices
            self.fields['production_choice'].choices = [
                (str(choice), f"{list(choice.keys())[0]}: {list(choice.values())[0]}")
                for choice in choices
            ]
            self.fields['production_choice'].required = True
        else:
            # Do not hide the field, we'll handle visibility with JS
            pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        prod_choice = self.cleaned_data.get('production_choice')
        if prod_choice:
            instance.production = ast.literal_eval(prod_choice)
        else:
            instance.production = self.cleaned_data['unit_type'].production or {}
        if commit:
            instance.save()
        return instance


class PopulationUnitForm(forms.Form):
    race = forms.ChoiceField(choices=[('Human', 'Human'), ('Dwarf', 'Dwarf')])  # Example choices

LandUnitFormSet = formset_factory(LandUnitForm, extra=0)
PopulationUnitFormSet = formset_factory(PopulationUnitForm, extra=0)