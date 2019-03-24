from django import forms


class LeaderHintsForm(forms.Form):
    hint_1 = forms.CharField(max_length=100)
    hint_2 = forms.CharField(max_length=100)
    hint_3 = forms.CharField(max_length=100)


class PlayerGuessForm(forms.Form):
    NUMBER_CHOICES = ((1, "1"),(2, "2"),(3, "3"),(4, "4"))
    guess_1 = forms.ChoiceField(choices=NUMBER_CHOICES)
    guess_2 = forms.ChoiceField(choices=NUMBER_CHOICES)
    guess_3 = forms.ChoiceField(choices=NUMBER_CHOICES)