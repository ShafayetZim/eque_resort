from django import forms
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm, UserChangeForm
from django.db.models import Sum, F
from django.contrib.auth.models import User
from more_itertools import quantify
from .models import *
from datetime import datetime


# registration
class UserRegistration(UserCreationForm):
    email = forms.EmailField(max_length=250 ,help_text="The email field is required.")
    first_name = forms.CharField(max_length=250 ,help_text="The First Name field is required.")
    last_name = forms.CharField(max_length=250 ,help_text="The Last Name field is required.")

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'first_name', 'last_name')


    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail is already exists/taken")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} mail is already exists/taken")


# profile
class UpdateProfile(UserChangeForm):
    username = forms.CharField(max_length=250,help_text="The Username field is required.")
    email = forms.EmailField(max_length=250,help_text="The Email field is required.")
    first_name = forms.CharField(max_length=250,help_text="The First Name field is required.")
    last_name = forms.CharField(max_length=250,help_text="The Last Name field is required.")
    current_password = forms.CharField(max_length=250)

    class Meta:
        model = User
        fields = ('email', 'username','first_name', 'last_name')

    def clean_current_password(self):
        if not self.instance.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError(f"Password is Incorrect")

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail is already exists/taken")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} mail is already exists/taken")


class UpdatePasswords(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Old Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Confirm New Password")

    class Meta:
        model = User
        fields = ('old_password','new_password1', 'new_password2')


# category
class SaveCategory(forms.ModelForm):
    name = forms.CharField(max_length="250")

    class Meta:
        model = Category
        fields = ('name',)

    def clean_name(self):
        id = self.instance.id if self.instance.id else 0
        name = self.cleaned_data['name']
        # print(int(id) > 0)
        # raise forms.ValidationError(f"{name} Category Already Exists.")
        try:
            if int(id) > 0:
                category = Category.objects.exclude(id=id).get(name = name)
            else:
                category = Category.objects.get(name = name)
        except:
            return name
            # raise forms.ValidationError(f"{name} Category Already Exists.")
        raise forms.ValidationError(f"{name} Category Already Exists.")


# product
class SaveProduct(forms.ModelForm):
    name = forms.CharField(max_length="250")
    status = forms.ChoiceField(choices=[('1', 'Active'), ('2', 'Inactive')])

    class Meta:
        model = Product
        fields = ('code', 'name', 'brand', 'unit', 'status', 'rate', 'price')

    def clean_code(self):
        id = self.instance.id if self.instance.id else 0
        code = self.cleaned_data['code']
        try:
            if int(id) > 0:
                product = Product.objects.exclude(id=id).get(code = code)
            else:
                product = Product.objects.get(code = code)
        except:
            return code
        raise forms.ValidationError(f"{code} Category Already Exists.")


# stock
class SaveStock(forms.ModelForm):
    product = forms.CharField(max_length=30)
    quantity = forms.CharField(max_length=250)
    type = forms.ChoiceField(choices=[('1','Stock-in'),('2','Stock-Out')])

    class Meta:
        model = Stock
        fields = ('product', 'quantity', 'type')

    def clean_product(self):
        pid = self.cleaned_data['product']
        try:
            product = Product.objects.get(id=pid)
            print(product)
            return product
        except:
            raise forms.ValidationError("Product is not valid")


# sale invoice
class SaveInvoice(forms.ModelForm):
    transaction = forms.CharField(max_length=100)
    customer = forms.CharField(max_length=250)
    total = forms.FloatField()
    paid = forms.FloatField()
    due = forms.FloatField()

    class Meta:
        model = Invoice
        fields = ('transaction', 'customer', 'total', 'paid', 'due',)

    def clean_transaction(self):
        pref = datetime.today().strftime('%Y%m%d')
        transaction= ''
        code = str(1).zfill(4)
        while True:
            invoice = Invoice.objects.filter(transaction=str(pref + code)).count()
            if invoice > 0:
                code = str(int(code) + 1).zfill(4)
            else:
                transaction = str(pref + code)
                break
        return transaction


class SaveInvoiceItem(forms.ModelForm):
    invoice = forms.CharField(max_length=30)
    product = forms.CharField(max_length=30)
    quantity = forms.CharField(max_length=100)
    price = forms.CharField(max_length=100)

    class Meta:
        model = Invoice_Item
        fields = ('invoice','product','quantity','price')

    def clean_invoice(self):
        iid = self.cleaned_data['invoice']
        try:
            invoice = Invoice.objects.get(id=iid)
            return invoice
        except:
            raise forms.ValidationError("Invoice ID is not valid")

    def clean_product(self):
        pid = self.cleaned_data['product']
        try:
            product = Product.objects.get(id=pid)
            return product
        except:
            raise forms.ValidationError("Product is not valid")

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty.isnumeric():
            return int(qty)
        raise forms.ValidationError("Quantity is not valid")

    def clean(self):
        qty = self.cleaned_data['quantity']
        item = self.cleaned_data['product']
        product = get_object_or_404(Product, id=item.id)
        # stock = Stock.objects.get(product=item.id)

        if product.count_inventory() < qty:

            raise forms.ValidationError("Not enough stock")


# purchase invoice
class SaveIncomingInvoice(forms.ModelForm):
    transaction = forms.CharField(max_length=100)
    customer = forms.CharField(max_length=250)
    total = forms.FloatField()

    class Meta:
        model = IncomingInvoice
        fields = ('transaction', 'customer', 'total')

    def clean_transaction(self):
        pref = datetime.today().strftime('%Y%m%d')
        transaction= ''
        code = str(1).zfill(4)
        while True:
            invoice = IncomingInvoice.objects.filter(transaction=str(pref + code)).count()
            if invoice > 0:
                code = str(int(code) + 1).zfill(4)
            else:
                transaction = str(pref + code)
                break
        return transaction


class SaveIncomingInvoiceItem(forms.ModelForm):
    invoice = forms.CharField(max_length=30)
    product = forms.CharField(max_length=30)
    quantity = forms.CharField(max_length=100)
    price = forms.CharField(max_length=100)

    class Meta:
        model = IncomingInvoice_Item
        fields = ('invoice','product','quantity','price')

    def clean_invoice(self):
        iid = self.cleaned_data['invoice']
        try:
            invoice = IncomingInvoice.objects.get(id=iid)
            return invoice
        except:
            raise forms.ValidationError("Invoice ID is not valid")

    def clean_product(self):
        pid = self.cleaned_data['product']
        try:
            product = Product.objects.get(id=pid)
            return product
        except:
            raise forms.ValidationError("Product is not valid")

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty.isnumeric():
            return int(qty)
        raise forms.ValidationError("Quantity is not valid")


# formset
class SalesCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = (
            'transaction', 'customer', 'total', )
        widgets = {
            'customer': forms.Select(
                attrs={'required': True, 'class': 'form-control', 'value': '', 'id': 'id_customer'}),

            'total': forms.NumberInput(
                attrs={'class': 'form-control', 'readonly': 'readonly', 'value': '', 'id': 'sales_total_amount'}),

        }
        labels = {
            'customer': 'Customer Name',
            'total': 'Total Amount',
        }


class SalesChildFormCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter()
        self.fields['product'].widget.attrs.update(
            {'class': 'textinput form-control setprice product', 'min': '0', 'required': 'true'})

        self.fields['quantity'].widget.attrs.update(
            {'class': 'textinput form-control setprice quantity', 'min': '0', 'required': 'true'})
        self.fields['price'].widget.attrs.update(
            {'class': 'textinput form-control setprice price', 'min': '0', 'required': 'true'})
        # self.fields['total'].widget.attrs.update(
        #     {'class': 'textinput form-control setprice amount', 'min': '0', 'required': 'true',
        #      'readonly': 'readonly', })


    class Meta:
        model = Invoice_Item
        fields = (
            'product', 'quantity', 'price',)


SalesChildFormset = modelformset_factory(
    Invoice_Item,
    form=SalesChildFormCreateForm,
    extra=1,
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'price': forms.NumberInput(attrs={'class': 'form-control'}),
        # 'amount': forms.NumberInput(attrs={'class': 'form-control'}),

    },
)


class DueForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = (
            'transaction', 'customer', 'total', 'paid')
        widgets = {
            'transaction': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'customer': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'paid': forms.TextInput(attrs={'class': 'form-control'}),

        }
