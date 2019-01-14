from django import forms

from core import models


class HintForm(forms.ModelForm):
    class Meta:
        model = models.LeaderHint
        fields = ['hint']

    field_order = ['position', 'word', 'hint']

    word = forms.CharField(label='Word', disabled=True)
    position = forms.IntegerField(label='Position', disabled=True)

    def __init__(self, *args, **kwargs):
        super(HintForm, self).__init__(*args, **kwargs)
        self.fields['position'].initial = self.instance.target_word.party_word.position
        self.fields['word'].initial = self.instance.target_word.party_word.get_text()


class GuessForm(forms.ModelForm):
    class Meta:
        model = models.PlayerGuess
        fields = ['guess']

    field_order = ['order', 'hint', 'guess']

    order = forms.IntegerField(label='Order', disabled=True)
    hint = forms.CharField(label='Word', disabled=True)
    guess = forms.ModelChoiceField(label='Guess', queryset=None)

    def __init__(self, *args, **kwargs):
        super(GuessForm, self).__init__(*args, **kwargs)
        self.fields['order'].initial = self.instance.target_word.order+1
        self.fields['hint'].initial = self.instance.target_word.leader_hint.hint
        self.fields['guess'].queryset = models.PartyWord.objects.filter(
            party=self.instance.target_word.party_word.party
        )


class OpponentGuessForm(forms.ModelForm):
    class Meta:
        model = models.PlayerGuess
        fields = ['guess']

    field_order = ['order', 'hint', 'guess']

    order = forms.IntegerField(label='Order', disabled=True)
    hint = forms.CharField(label='Word', disabled=True)
    guess = forms.ModelChoiceField(label='Guess', queryset=None)

    def __init__(self, *args, **kwargs):
        super(OpponentGuessForm, self).__init__(*args, **kwargs)
        self.fields['order'].initial = self.instance.target_word.order+1
        self.fields['hint'].initial = self.instance.target_word.leader_hint.hint
        self.fields['guess'].queryset = models.PartyWord.objects.only('position').filter(
            party=self.instance.target_word.party_word.party
        )

