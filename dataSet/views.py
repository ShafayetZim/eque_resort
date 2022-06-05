from email import message
from unicodedata import category
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, CreateView, ListView
from django.urls import reverse_lazy
from eque_resort.settings import MEDIA_ROOT, MEDIA_URL
import json
from django.db.models import Sum, F, Avg
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from dataSet import models, forms
from dataSet.forms import *
from dataSet.models import *
from django.conf import settings
import base64
from dataSet.utils import render_to_pdf
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import datetime, timedelta

context = {
    'page_title' : 'Eque Resort Management System',
}


# login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')


# Logout
def logoutuser(request):
    logout(request)
    return redirect('/')


# registration
def registerUser(request):
    user = request.user
    if user.is_authenticated:
        return redirect('home-page')
    context['page_title'] = "Register User"
    if request.method == 'POST':
        data = request.POST
        form = UserRegistration(data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            loginUser = authenticate(username= username, password = pwd)
            login(request, loginUser)
            return redirect('home-page')
        else:
            context['reg_form'] = form

    return render(request,'register.html',context)


# profile
@login_required
def profile(request):
    context['page_title'] = 'Profile'
    return render(request, 'profile.html',context)


@login_required
def update_profile(request):
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id=request.user.id)
    if not request.method == 'POST':
        form = UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile")
        else:
            context['form'] = form

    return render(request, 'update_profile.html', context)


@login_required
def update_password(request):
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)


# product
@login_required
def product_mgt(request):
    context['page_title'] = "Product List"
    products = Product.objects.all()
    category = Category.objects.all()
    context['products'] = products
    context['category'] = category

    return render(request, 'product.html', context)


@login_required
def save_product(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            product = Product.objects.get(pk=request.POST['id'])
        else:
            product = None
        if product is None:
            form = SaveProduct(request.POST)
        else:
            form = SaveProduct(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def manage_product(request, pk=None):
    context['page_title'] = "Manage Product"
    if not pk is None:
        product = Product.objects.get(id=pk)
        context['product'] = product
    else:
        context['product'] = {}

    return render(request, 'manage_product.html', context)


@login_required
def delete_product(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        try:
            product = Product.objects.get(id=request.POST['id'])
            product.delete()
            messages.success(request, 'Product has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Product has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Product has failed to delete'

    return HttpResponse(json.dumps(resp), content_type="application/json")


# home
def home(request):
    context['page_title'] = 'Home'
    context['categories'] = Category.objects.count()
    context['products'] = Product.objects.count()
    context['sales'] = Invoice.objects.count()
    # context['low'] = Product.objects.filter(count_inventory__lte=5).count()
    context['net'] = Invoice.objects.all().aggregate(Sum('total'))['total__sum']
    context['today'] = Invoice.objects.filter(date_created=timezone.now()).aggregate(Sum('total'))
    context['td'] = Invoice.objects.filter().values('date_created__date').order_by('date_created__date').annotate(sum=Sum('total')).last()
    context['collection'] = Invoice.objects.filter().values('date_created__date').order_by('date_created__date').annotate(sum=Sum('paid')).last()
    stocks = Product.objects.all()
    count = 0
    x = Product().count_inventory()
    print(x)
    for i in range(x):
        if i < 5:
            count = count + 1
            return count

    context['count'] = count
    context['stocks'] = stocks

    return render(request, 'home.html',context)


# Category
@login_required
def category_mgt(request):
    context['page_title'] = "Product Categories"
    categories = Category.objects.all()
    context['categories'] = categories

    return render(request, 'category.html', context)


@login_required
def save_category(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            category = Category.objects.get(pk=request.POST['id'])
        else:
            category = None
        if category is None:
            form = SaveCategory(request.POST)
        else:
            form = SaveCategory(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def manage_category(request, pk=None):
    context['page_title'] = "Manage Category"
    if not pk is None:
        category = Category.objects.get(id=pk)
        context['category'] = category
    else:
        context['category'] = {}

    return render(request, 'manage_category.html', context)


@login_required
def delete_category(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        try:
            category = Category.objects.get(id=request.POST['id'])
            category.delete()
            messages.success(request, 'Category has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Category has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Category has failed to delete'

    return HttpResponse(json.dumps(resp), content_type="application/json")


# low stock
@login_required
def low_stock(request):
    context['page_title'] = 'Low Stocks'

    products = Product.objects.all()
    context['products'] = products

    return render(request, 'low_stock.html', context)


# Inventory
@login_required
def inventory(request):
    context['page_title'] = 'Inventory'

    products = Product.objects.all()
    context['products'] = products

    return render(request, 'stock.html', context)


# Inventory History
@login_required
def inv_history(request, pk=None):
    context['page_title'] = 'Inventory History'
    if pk is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    else:
        product = Product.objects.get(id=pk)
        stocks = Stock.objects.filter(product=product).all()
        context['product'] = product
        context['stocks'] = stocks

        return render(request, 'stock_history.html', context)


# Stock Form
@login_required
def manage_stock(request, pid=None, pk=None):
    if pid is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    context['pid'] = pid
    if pk is None:
        context['page_title'] = "Add New Stock"
        context['stock'] = {}
    else:
        context['page_title'] = "Manage New Stock"
        stock = Stock.objects.get(id=pk)
        context['stock'] = stock

    return render(request, 'manage_stock.html', context)


@login_required
def save_stock(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            stock = Stock.objects.get(pk=request.POST['id'])
        else:
            stock = None
        if stock is None:
            form = SaveStock(request.POST)
        else:
            form = SaveStock(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def delete_stock(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        try:
            stock = Stock.objects.get(id=request.POST['id'])
            stock.delete()
            messages.success(request, 'Stock has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Stock has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Stock has failed to delete'

    return HttpResponse(json.dumps(resp), content_type="application/json")


# sale
@login_required
def sales_mgt(request):
    context['page_title'] = 'Sales'
    products = Product.objects.filter(status=1).all()
    context['products'] = products
    return render(request, 'sales.html', context)


def get_product(request, pk=None):
    resp = {'status': 'failed', 'data': {}, 'msg': ''}
    if pk is None:
        resp['msg'] = 'Product ID is not recognized'
    else:
        product = Product.objects.get(id=pk)
        resp['data']['product'] = str(product.code + " - " + product.name)
        resp['data']['id'] = product.id
        resp['data']['price'] = product.price
        resp['status'] = 'success'

    return HttpResponse(json.dumps(resp), content_type="application/json")


def save_sales(request):
    resp = {'status': 'failed', 'msg': ''}
    id = 2
    if request.method == 'POST':
        pids = request.POST.getlist('pid[]')
        invoice_form = SaveInvoice(request.POST)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = Invoice.objects.last()
            for pid in pids:
                data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': request.POST['quantity[' + str(pid) + ']'],
                    'price': request.POST['price[' + str(pid) + ']'],
                }
                print(data)
                ii_form = SaveInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Sale Transaction has been saved.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")

    return HttpResponse(json.dumps(resp), content_type="application/json")


# sale invoice
@login_required
def invoices(request):
    invoice = Invoice.objects.all().order_by('-id')
    context['page_title'] = 'Invoices'
    context['invoices'] = invoice

    return render(request, 'invoice.html', context)


@login_required
def delete_invoice(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        try:
            invoice = Invoice.objects.get(id=request.POST['id'])
            invoice.delete()
            messages.success(request, 'Invoice has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Invoice has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Invoice has failed to delete'

    return HttpResponse(json.dumps(resp), content_type="application/json")


# update due
class DueUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'login'
    model = Invoice
    form_class = DueForm
    success_url = reverse_lazy('invoice-page')
    template_name = 'update_due.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context)
        context["page_title"] = "Due Update"
        context["pageview"] = "Invoice"
        return context


# purchase
@login_required
def purchase_mgt(request):
    context['page_title'] = 'Purchase'
    products = Product.objects.filter(status=1).all()
    context['products'] = products
    return render(request, 'purchase.html', context)


def save_purchase(request):
    resp = {'status': 'failed', 'msg': ''}
    id = 2
    if request.method == 'POST':
        pids = request.POST.getlist('pid[]')
        invoice_form = SaveIncomingInvoice(request.POST)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = IncomingInvoice.objects.last()
            for pid in pids:
                data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': request.POST['quantity[' + str(pid) + ']'],
                    'price': request.POST['price[' + str(pid) + ']'],
                }
                print(data)
                ii_form = SaveIncomingInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Purchase Transaction has been saved.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")

    return HttpResponse(json.dumps(resp), content_type="application/json")


# purchase invoice
@login_required
def incoming_invoices(request):
    invoice = IncomingInvoice.objects.all().order_by('-id')
    context['page_title'] = 'Invoices'
    context['invoices'] = invoice

    return render(request, 'incoming_invoice.html', context)


@login_required
def delete_incoming_invoice(request):
    resp = {'status': 'failed', 'msg': ''}

    if request.method == 'POST':
        try:
            invoice = IncomingInvoice.objects.get(id=request.POST['id'])
            invoice.delete()
            messages.success(request, 'Invoice has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Invoice has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Invoice has failed to delete'

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def print_sales(request, id=None):
    print(id)
    invoice = get_object_or_404(Invoice, id=id)
    invoice_item = Invoice_Item.objects.filter(invoice=id)
    print(invoice_item)
    total_qty = invoice_item.aggregate(Sum('quantity'))
    total_qty = total_qty.get('quantity__sum')
    print(total_qty)

    context = {
        'page-title': "invoice print",
        'sales_item': invoice_item,
        'total_qty': total_qty,
        'invoice_info': invoice,
    }
    pdf = render_to_pdf('sales_print.html', context)
    return HttpResponse(pdf, content_type='application/pdf')


# view pdf
def view_PDF(request, id=None):
    invoice = get_object_or_404(Invoice, id=id)
    lineitem = Invoice_Item.objects.filter(invoice=id)

    context = {
        "company": {
            "name": "Something Limited",
            "address": "Bashundhara R/A",
            "phone": "01345-555982",
            "email": "xyz@gmail.com",
        },
        "invoice_id": invoice.id,
        "transaction": invoice.transaction,
        "invoice_total": invoice.total,
        "customer": invoice.customer,
        "customer_email": invoice.transaction,
        "date": invoice.date_created,
        "lineitem": lineitem,
    }
    return render(request, 'pdf_template.html', context)


# view purchase pdf
def view_purchase_PDF(request, id=None):
    invoice = get_object_or_404(IncomingInvoice, id=id)
    lineitem = IncomingInvoice_Item.objects.filter(invoice=id)

    context = {
        "company": {
            "name": "Something Limited",
            "address": "Bashundhara R/A",
            "phone": "01345-555982",
            "email": "xyz@gmail.com",
        },
        "invoice_id": invoice.id,
        "transaction": invoice.transaction,
        "invoice_total": invoice.total,
        "customer": invoice.customer,
        "customer_email": invoice.transaction,
        "date": invoice.date_created,
        "lineitem": lineitem,
    }
    return render(request, 'pdf_purchase_template.html', context)


# edit
def invoice_edit_sale(request, id=None):
    resp = {'status': 'failed', 'msg': ''}

    # context = {
    #     "company": {
    #         "name": "Something Limited",
    #         "address": "Bashundhara R/A",
    #         "phone": "01345-555982",
    #         "email": "xyz@gmail.com",
    #     },
    #     "invoice_id": invoice.id,
    #     "transaction": invoice.transaction,
    #     "invoice_total": invoice.total,
    #     "customer": invoice.customer,
    #     "customer_email": invoice.transaction,
    #     "date": invoice.date_created,
    #     "lineitem": lineitem,
    # }
    if request.method == 'GET':
        invoice = get_object_or_404(Invoice, id=id)
        lineitem = Invoice_Item.objects.filter(invoice=id)
        invoice_form = SaveInvoice(instance=invoice)
    if request.method == 'Post':
        invoice = get_object_or_404(Invoice, id=id)
        lineitem = Invoice_Item.objects.filter(invoice=id)
        pids = request.POST.getlist('pid[]')
        invoice_form = SaveInvoice(request.POST, instance=invoice)
        lineitem_form = SaveInvoiceItem(request.POST, instance=lineitem)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = Invoice.objects.last()
            for pid in pids:
                data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': request.POST['quantity[' + str(pid) + ']'],
                    'price': request.POST['price[' + str(pid) + ']'],
                }
                print(data)
                ii_form = SaveInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Purchase Transaction has been updated.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    return render(request, 'sales_edit.html', context)

#
# @login_required
# def new_sales_edit(request, id=None):
#     template_name = 'edit_sales.html'
#
#     if request.method == 'GET':
#         print("GET called")
#         parent = get_object_or_404(Invoice, id=id)
#         sales_form = SalesCreateForm(instance=parent)
#         queryset = Invoice_Item.objects.filter(invoice=id)
#
#         # Set Current Stock of Item
#         for query in queryset:
#             query.save()
#
#         sales_form_child = SalesChildFormset(queryset=Invoice_Item.objects.filter(invoice=id))
#
#     elif request.method == 'POST':
#         print("Post called")
#         parent = get_object_or_404(Invoice, id=id)
#         sales_form = SalesCreateForm(request.POST, instance=parent)
#         queryset = Invoice_Item.objects.filter(invoice=id)
#         sales_form_child = SalesChildFormset(request.POST, queryset=queryset)
#
#         if sales_form.is_valid() and sales_form_child.is_valid():
#             sales_parent = sales_form.save(commit=False)
#             sales_parent.author = request.user
#             sales_parent.is_active = True
#             sales_parent.save()
#
#             for form in sales_form_child:
#
#                 if form.is_valid():
#                     try:
#                         product_qty = form.cleaned_data.get('quantity')
#
#                         child = form.save(commit=False)
#                         child.invoice = Invoice.objects.get(id=sales_parent.id)
#                         child.author = sales_parent.author
#                         child.is_active = True
#                         child.save()
#                     except IntegrityError as e:
#                         print(e.args)
#                         messages.add_message(request, messages.WARNING, 'Sales Product must be Unique!')
#                         return redirect(request.path)
#
#                 else:
#                     print("Child Form Error")
#                     messages.add_message(request, messages.ERROR, form.errors)
#                     print(form.errors)
#
#             messages.add_message(request, messages.SUCCESS, 'Sales Update Successful')
#             return redirect('sales-list')
#
#         else:
#             print("Not Valid Create Form")
#             print(sales_form_child.errors)
#
#     return render(request, template_name, {
#         'sales_form': sales_form,
#         'formset': sales_form_child,
#         'title': 'New Sales',
#         'nav_bar': 'new_sales',
#     })


def edit_sale(request, id=None):
    resp = {'status': 'failed', 'msg': ''}
    id = 2
    if request.method == 'GET':
        invoice = get_object_or_404(Invoice, id=id)
        invoice_form = SaveInvoice(instance=invoice)
        lineitem = Invoice_Item.objects.filter(invoice=id)
        for query in lineitem:
            query.save()
        item_form = SaveInvoiceItem(instance=lineitem)
    elif request.method == 'POST':
        pids = request.POST.getlist('pid[]')
        invoice_form = SaveInvoice(request.POST)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = Invoice.objects.last()
            for pid in pids:
                data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': request.POST['quantity[' + str(pid) + ']'],
                    'price': request.POST['price[' + str(pid) + ']'],
                }
                print(data)
                ii_form = SaveInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Purchase Transaction has been saved.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")

    # return HttpResponse(json.dumps(resp), content_type="application/json")
    return render(request, 'sales_edit.html', {'invoice_form': invoice_form, 'item_form': item_form})


@login_required
def sales_update(request):
    context['page_title'] = 'Sales'
    products = Product.objects.filter(status=1).all()
    context['products'] = products
    return render(request, 'sales_edit.html', context)


@login_required
def new_sales_edit(request, id=None):
    resp = {'status': 'failed', 'msg': ''}
    template_name = 'sales_edit.html'

    if request.method == 'GET':
        print("GET called")
        invoice = get_object_or_404(Invoice, id=id)
        invoice_form = SaveInvoice(instance=invoice)
        lineitem = Invoice_Item.objects.filter(invoice=id)
        item_form = SaveInvoiceItem()

    elif request.method == 'POST':
        print("Post called")
        pids = request.POST.getlist('pid[]')
        invoice_form = SaveInvoice(request.POST)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = Invoice.objects.last()
            for pid in pids:
                data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': request.POST['quantity[' + str(pid) + ']'],
                    'price': request.POST['price[' + str(pid) + ']'],
                }
                print(data)
                ii_form = SaveInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Purchase Transaction has been saved.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def manage_laundry(request, pk=None):
    # context = context_data(request)
    context['page'] = 'manage_laundry'
    context['page_title'] = 'Manage laundry'
    context['products'] = Product.objects.filter(status=1).all()
    # context['prices'] = models.Prices.objects.filter(delete_flag=0, status=1).all()
    if pk is None:
        context['laundry'] = {}
        context['items'] = {}
        # context['pitems'] = {}
    else:
        context['laundry'] = Invoice.objects.get(id=pk)
        context['items'] = Invoice_Item.objects.filter(invoice__id=pk).all()
        # context['pitems'] = models.LaundryProducts.objects.filter(laundry__id=pk).all()

    return render(request, 'manage_sale.html', context)






