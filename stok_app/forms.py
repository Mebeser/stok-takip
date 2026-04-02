from django import forms
from django.contrib.auth.models import User
from .models import Urun,Satis,Musteri,UserProfile
from django.contrib.auth.forms import UserCreationForm

class UrunForm(forms.ModelForm):
    class Meta:
        model = Urun
        fields = ['ad', 'kategori', 'stok_miktari', 'birim', 'fiyat', 'kritik_stok', 'barkod']
        widgets = {
            'barkod': forms.TextInput(attrs={'placeholder': 'Barkod girin veya boş bırakın (otomatik atanır)'})
        }

class KayitFormu(forms.ModelForm):
    password1 = forms.CharField(label="Şifre", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Şifreyi Onayla", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Şifreler eşleşmiyor!")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Şifreyi hashle
        user.is_active = False  # Kullanıcı admin onayını beklesin
        if commit:
            user.save()
        return user

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Kullanıcının e-posta girmesini zorunlu yapalım

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]  # Kullanıcının gireceği alanlar


class SatisForm(forms.ModelForm):
    musteri = forms.ModelChoiceField(
        queryset=Musteri.objects.none(),  # Başlangıçta boş olacak, init içinde doldurulacak
        required=True,
        label="Müşteri",
        empty_label="Müşteri Seçin"
    )

    class Meta:
        model = Satis
        fields = ['musteri', 'satis_adedi', 'satis_fiyati']
        labels = {
            "satis_adedi": "Satış Adedi",
            "satis_fiyati": "Satış Fiyatı (₺)",
        }
        widgets = {
            "satis_adedi": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "satis_fiyati": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        kullanici = kwargs.pop('kullanici', None)  # Kullanıcıyı parametre olarak al
        super(SatisForm, self).__init__(*args, **kwargs)
        
        if kullanici:
            try:
                firma = kullanici.userprofile.firma  # Kullanıcının firması
                self.fields['musteri'].queryset = Musteri.objects.filter(firma=firma)  # Sadece kendi firması
            except UserProfile.DoesNotExist:
                self.fields['musteri'].queryset = Musteri.objects.none()  # Kullanıcı profili yoksa boş liste döndür



#müşteri formu


class MusteriForm(forms.ModelForm):
    class Meta:
        model = Musteri
        fields = ['ad_soyad', 'telefon', 'email', 'adres']