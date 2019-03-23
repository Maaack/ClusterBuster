from django import forms


class LeaderHintsForm(forms.Form):
    hint_1 = forms.CharField(max_length=100)
    hint_2 = forms.CharField(max_length=100)
    hint_3 = forms.CharField(max_length=100)
