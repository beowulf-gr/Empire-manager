from django import forms
from django.forms import formset_factory, modelformset_factory
from .models import LandUnit, LandUnitType, PopulationUnit, PopulationRace

class RealmInfoForm(forms.Form):
    name = forms.CharField(max_length=100)
    ruler = forms.CharField(max_length=100)

class TreasuryForm(forms.Form):
    treasury = forms.IntegerField(min_value=0)

# class ResourcesForm(forms.Form):
#     Food = forms.IntegerField(min_value=0)
#     Wood = forms.IntegerField(min_value=0)
#     Stone = forms.IntegerField(min_value=0)
#     Adamantine = forms.IntegerField(min_value=0)
#     Copper = forms.IntegerField(min_value=0)
#     Gold = forms.IntegerField(min_value=0)
#     Iron = forms.IntegerField(min_value=0)
#     Mithral = forms.IntegerField(min_value=0)
#     Silver = forms.IntegerField(min_value=0)

class LandUnitForm(forms.ModelForm):
    class Meta:
        model = LandUnit
        fields = ['name', 'unit_type']  # Add other fields if desired

    unit_type = forms.ModelChoiceField(
        queryset=LandUnitType.objects.all(),
        empty_label="Select a Land Type"
    )

class PopulationUnitForm(forms.ModelForm):
    class Meta:
        model = PopulationUnit
        fields = ['race']  # Add other fields if desired

    race = forms.ModelChoiceField(
        queryset=PopulationRace.objects.all(),
        empty_label="Select a Population Race"
    )

PopulationUnitFormSet = modelformset_factory(
    PopulationUnit,
    form=PopulationUnitForm,
    extra=0
)

LandUnitFormSet = modelformset_factory(
    LandUnit,
    form=LandUnitForm,
    extra=0
)