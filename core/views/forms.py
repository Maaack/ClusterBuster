from django import forms

from core.constants import TEAM_WORD_LIMIT


class GuessForm(forms.Form):
    position = forms.IntegerField(label="Position", widget=forms.RadioSelect(choices=(range(1, TEAM_WORD_LIMIT))))

