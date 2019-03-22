from django import forms


class LeaderHintForm(forms.Form):
    hint = forms.CharField(max_length=100)
    position = forms.IntegerField(label='Position', disabled=True)

    def __init__(self, *args, **kwargs):
        super(LeaderHintForm, self).__init__(*args, **kwargs)
        self.fields['position'].initial = 9
        self.fields['hint'].initial = "Hint Here"
