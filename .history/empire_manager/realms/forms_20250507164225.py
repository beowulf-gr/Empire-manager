from django import forms
from django.forms import formset_factory, modelformset_factory
from .models import LandUnit, LandUnitType, PopulationUnit

class RealmInfoForm(forms.Form):
    name = forms.CharField(max_length=100)
    ruler = forms.CharField(max_length=100)

class TreasuryForm(forms.Form):
    treasury = forms.IntegerField(min_value=0)

class ResourcesForm(forms.Form):
    food = forms.IntegerField(min_value=0)
    wood = forms.IntegerField(min_value=0)
    stone = forms.IntegerField(min_value=0)  

class LandUnitForm(forms.ModelForm):
    class Meta:
        model = LandUnit
        fields = ['name', 'unit_type']  # Add other fields if desired

    unit_type = forms.ModelChoiceField(
        queryset=LandUnitType.objects.all(),
        empty_label="Select a Land Type"
    )

class PopulationUnitForm(forms.Form):
    class Meta:
        model = PopulatioUnit
        fields = ['name', 'unit_type']  # Add other fields if desired
    race = forms.ChoiceField(choices=[('Human', 'Human'), ('Dwarf', 'Dwarf')])  # Example choices

LandUnitFormSet = modelformset_factory(
    LandUnit,
    form=LandUnitForm,
    extra=0
)
PopulationUnitFormSet = formset_factory(PopulationUnitForm, extra=0)