from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(Invoice)
admin.site.register(Invoice_Item)
admin.site.register(IncomingInvoice)
admin.site.register(IncomingInvoice_Item)
