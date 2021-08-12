from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import Society, Account, Union, User,Transaction



class MemberInline(admin.StackedInline):
    model = User
    extra = 1


class SocietyInline(admin.StackedInline):
    model = Society
    extra = 1
    filter_horizontal = ('members', 'secretaries',)

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = ('username', 'first_name', 'last_name', 'balances', 'bm_approval', 'hq_approval',)
    list_display_links = ('username',)
    list_filter = ('is_active', 'is_staff', 'date_joined',)
    search_fields = ('username', 'email')
    filter_horizontal = ('groups',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Info', {'fields': ('first_name', 'last_name', 'date_of_birth', 'picture', 'ref_num', 'qrcode_img', 'address', 'phone_number', 'groups', 'bm_approval', 'hq_approval',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'groups',)}
         ),
    )
    readonly_fields = ('ref_num', 'qrcode_img',)


class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', )
    filter_horizontal = ('unions', )



class UnionAdmin(admin.ModelAdmin):
    list_display = ('name', 'ref_number', 'slug','members')
    list_display_links = ('name',)
    # list_filter = ('')
    filter_horizontal = ('accounts', 'secretaries')
    inlines= (SocietyInline, )


class SocietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'ref_number', 'union', 'balances',)
    filter_horizontal = ('members', 'secretaries',)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('member', 'secretary', 'society', 'amount', 'account', 'action', 'bm_approval', 'hq_approval',)


admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Union, UnionAdmin)
admin.site.register(Society, SocietyAdmin)
admin.site.register(Transaction, TransactionAdmin)


admin.site.site_title = "Kobo Admin"
admin.site.site_header = "Kobo Administration"

