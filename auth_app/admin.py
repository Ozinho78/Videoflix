from django.contrib import admin  # Admin site APIs
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # Default User admin
from django.contrib.auth.models import User  # Built-in User model
from django.contrib import messages  # Flash messages
from django.utils.http import urlsafe_base64_encode  # Encode uid for activation link
from django.utils.encoding import force_bytes  # Convert pk to bytes
from django.contrib.auth.tokens import default_token_generator  # Build/validate activation tokens
from django.utils.html import format_html  # Safe HTML rendering in admin
from django.conf import settings  # Read settings like DEBUG / base URLs
from auth_app.emails import send_activation_email  # Your HTML email helper


class UserAdmin(BaseUserAdmin):
    '''Custom admin with colored activation badge + readonly token & link.'''

    # List columns (unchanged, plus badge)
    list_display = (
        'id',
        'username',
        'email',
        'activation_badge',
        'is_staff',
        'is_superuser',
        'last_login',
        'date_joined',
    )

    # Filters/search/ordering (unchanged)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

    # Make additional computed fields visible/read-only on the detail page
    readonly_fields = (
        'date_joined',        # Built-in readonly
        'last_login',         # Built-in readonly
        'activation_badge',   # Show the same colored pill in the form
        'activation_token',   # NEW: show current activation token
        'activation_link',    # NEW: show clickable activation link + copy box
    )

    # Add a small "Activation" section to the form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        # New collapsed section with our computed fields
        ('Activation', {
            'classes': ('collapse',),  # Start collapsed to save space
            'fields': ('activation_badge', 'activation_token', 'activation_link'),
        }),
    )

    actions = ['resend_activation_email']  # Keep your bulk action

    def activation_badge(self, obj):
        '''Render a colored pill showing activation state.'''
        if obj.is_active:  # Active -> green pill
            label, bg, fg, br = 'Active', '#e8f5e9', '#166534', '#bbf7d0'
        else:              # Pending -> slate pill
            label, bg, fg, br = 'Pending', '#f1f5f9', '#475569', '#e2e8f0'
        # Return a rounded pill (inline styles work without extra CSS)
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-weight:600;font-size:12px;letter-spacing:.2px;'
            'background:{};color:{};border:1px solid {};">{}</span>',
            bg, fg, br, label
        )
    activation_badge.short_description = 'Activation'   # Column/field label
    activation_badge.admin_order_field = 'is_active'    # Allow sorting

    def _activation_parts(self, obj):
        '''Helper: build uidb64 and a fresh token for this user.'''
        uidb64 = urlsafe_base64_encode(force_bytes(obj.pk))  # Encode PK to uidb64
        token = default_token_generator.make_token(obj)      # Compute current token
        return uidb64, token  # Return tuple for reuse

    def activation_token(self, obj):
        '''Readonly field: show the current activation token or a hint.'''
        if obj.is_active:  # No need for a token once active
            return 'Already active'  # Friendly hint
        _, token = self._activation_parts(obj)  # Compute token
        # Note: token is time/ state sensitive and may change (password/last_login etc.)
        return token  # Plain string rendered by admin
    activation_token.short_description = 'Activation token'  # Field label

    def activation_link(self, obj):
        '''Readonly field: show a clickable activation URL + copy box.'''
        # Decide the base: use absolute backend URL if provided; else use absolute path
        base = getattr(settings, 'BACKEND_BASE_URL', '')  # Optional setting (e.g. 'http://127.0.0.1:8000')
        uidb64, token = self._activation_parts(obj)  # Compute parts
        # Build an absolute or root-absolute URL to the backend activate endpoint
        url = f'{base}/api/activate/{uidb64}/{token}/' if base else f'/api/activate/{uidb64}/{token}/'
        if obj.is_active:  # Don’t offer link if already active
            return 'Already active'  # Friendly hint
        # Render a copy-friendly readonly input + clickable anchor (opens new tab)
        return format_html(
            '<div style="max-width:100%;">'
            '<input type="text" readonly value="{}" '
            'style="width:100%;padding:6px 8px;font-family:monospace;border:1px solid #e2e8f0;'
            'border-radius:8px;background:#f8fafc;margin-bottom:8px;" />'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:6px 10px;border-radius:8px;'
            'background:#3b82f6;color:#fff;text-decoration:none;font-weight:600;">Open activation link</a>'
            '</div>',
            url, url  # First {} fills the input value, second {} fills the anchor href
        )
    activation_link.short_description = 'Activation link'  # Field label

    def resend_activation_email(self, request, queryset):
        '''Admin action: resend activation email to selected inactive users.'''
        inactive_users = queryset.filter(is_active=False)  # Only pending accounts
        sent = 0  # Counter
        for user in inactive_users:
            uidb64, token = self._activation_parts(user)  # Build parts
            try:
                send_activation_email(user, uidb64, token)  # Send HTML email
                sent += 1  # Count success
            except Exception as exc:
                self.message_user(request, f'Failed to send activation to {user.email}: {exc}', level=messages.ERROR)
        if sent:
            self.message_user(request, f'Sent {sent} activation email(s).', level=messages.SUCCESS)


# Swap in our customized admin for the built-in User model
try:
    admin.site.unregister(User)  # Unregister default user admin if present
except admin.sites.NotRegistered:
    pass  # Safe if already unregistered

admin.site.register(User, UserAdmin)  # Register our customized admin
