# auth_app/admin.py
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
from auth_app.jwt_utils import create_access_token, create_refresh_token  # NEW: JWT helpers for debug preview
from auth_app.models import BlacklistedToken  # NEW: model that stores hashed blacklisted refresh tokens


class BlacklistedTokenInline(admin.TabularInline):
    """
    Read-only inline to show blacklisted refresh tokens for this user.
    """
    model = BlacklistedToken  # The related model
    extra = 0  # No extra empty rows
    can_delete = False  # Prevent deletes from inline
    fields = ('token_hash', 'created_at')  # Show hash and timestamp
    readonly_fields = ('token_hash', 'created_at')  # Make inline fields read-only
    verbose_name_plural = 'Blacklisted refresh tokens'  # Section title


class UserAdmin(BaseUserAdmin):
    """
    Custom admin with:
    - colored activation badge
    - activation token/link (read-only)
    - JWT debug tokens (read-only; superusers only)
    - inline list of blacklisted refresh tokens
    """
    list_display = (
        'id', 'username', 'email', 'activation_badge', 'is_staff', 'is_superuser',
        'last_login', 'date_joined',
    )  # Columns in user list

    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')  # Sidebar filters
    search_fields = ('username', 'email')  # Quick search
    ordering = ('-date_joined',)  # Newest first

    # Base read-only fields (always visible)
    readonly_fields = (
        'date_joined',        # Built-in readonly
        'last_login',         # Built-in readonly
        'activation_badge',   # Colored badge
        'activation_token',   # Activation token (for inactive users)
        'activation_link',    # Activation link (for inactive users)
        'password_reset_token',
        'password_reset_link',
    )

    # Inline: show blacklisted refresh tokens for this user
    inlines = [BlacklistedTokenInline]

    # Base fieldsets (without debug tokens); we’ll inject the debug section conditionally for superusers
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Activation', {
            'classes': ('collapse',),
            'fields': ('activation_badge', 'activation_token', 'activation_link'),
        }),
        ('Password reset', {
        'classes': ('collapse',),
        'fields': ('password_reset_token', 'password_reset_link'),
        }),
    )

    # ---------- Activation helpers (you already had these) ----------

    def activation_badge(self, obj):
        """Render a colored pill showing activation state."""
        if obj.is_active:  # Active -> green pill
            label, bg, fg, br = 'Active', '#e8f5e9', '#166534', '#bbf7d0'
        else:              # Pending -> slate pill
            label, bg, fg, br = 'Pending', '#f1f5f9', '#475569', '#e2e8f0'
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-weight:600;font-size:12px;letter-spacing:.2px;'
            'background:{};color:{};border:1px solid {};">{}</span>',
            bg, fg, br, label
        )
    activation_badge.short_description = 'Activation'
    activation_badge.admin_order_field = 'is_active'

    def _activation_parts(self, obj):
        """Helper: build uidb64 and a fresh token for this user."""
        uidb64 = urlsafe_base64_encode(force_bytes(obj.pk))  # Encode PK to uidb64
        token = default_token_generator.make_token(obj)      # Compute current token
        return uidb64, token

    def activation_token(self, obj):
        """Readonly field: show the current activation token or a hint."""
        if obj.is_active:
            return 'Already active'  # No token needed for active users
        _, token = self._activation_parts(obj)
        return token
    activation_token.short_description = 'Activation token'

    def activation_link(self, obj):
        """Readonly field: show a clickable activation URL + copy box."""
        if obj.is_active:
            return 'Already active'
        base = getattr(settings, 'BACKEND_BASE_URL', '')  # e.g. 'http://127.0.0.1:8000'
        uidb64, token = self._activation_parts(obj)
        url = f'{base}/api/activate/{uidb64}/{token}/' if base else f'/api/activate/{uidb64}/{token}/'
        return format_html(
            '<div style="max-width:100%;">'
            '<input type="text" readonly value="{}" '
            'style="width:100%;padding:6px 8px;font-family:monospace;border:1px solid #e2e8f0;'
            'border-radius:8px;background:#f8fafc;margin-bottom:8px;" />'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:6px 10px;border-radius:8px;'
            'background:#3b82f6;color:#fff;text-decoration:none;font-weight:600;">Open activation link</a>'
            '</div>',
            url, url
        )
    activation_link.short_description = 'Activation link'

    # ---------- NEW: JWT debug tokens (only visible to superusers) ----------

    def get_readonly_fields(self, request, obj=None):
        """
        Add debug token fields for superusers only.
        """
        base = list(super().get_readonly_fields(request, obj)) + list(self.readonly_fields)
        if request.user.is_superuser:
            # Expose debug-only fields to superusers
            base += ['debug_access_token', 'debug_refresh_token']
        # Remove duplicates while preserving order
        seen, out = set(), []
        for f in base:
            if f not in seen:
                out.append(f); seen.add(f)
        return tuple(out)

    def get_fieldsets(self, request, obj=None):
        """
        Inject a collapsed 'Tokens (debug)' section for superusers.
        """
        base = list(super().get_fieldsets(request, obj)) or list(self.fieldsets)
        if request.user.is_superuser:
            base.append((
                'Tokens (debug)', {
                    'classes': ('collapse',),
                    'fields': ('debug_access_token', 'debug_refresh_token'),
                }
            ))
        return tuple(base)

    def debug_access_token(self, obj):
        """
        Readonly: show a freshly generated access token for demonstration only.
        """
        if not obj.is_active:
            return 'Activate the account first'
        token = create_access_token(obj)  # New token (not related to any cookie)
        return format_html(
            '<textarea readonly style="width:100%;height:80px;'
            'font-family:monospace;border:1px solid #e2e8f0;border-radius:8px;'
            'background:#f8fafc;padding:6px 8px;">{}</textarea>', token
        )
    debug_access_token.short_description = 'Access token (debug)'

    def debug_refresh_token(self, obj):
        """
        Readonly: show a freshly generated refresh token for demonstration only.
        """
        if not obj.is_active:
            return 'Activate the account first'
        token = create_refresh_token(obj)  # New token (not related to any cookie)
        return format_html(
            '<textarea readonly style="width:100%;height:80px;'
            'font-family:monospace;border:1px solid #e2e8f0;border-radius:8px;'
            'background:#f8fafc;padding:6px 8px;">{}</textarea>', token
        )
    debug_refresh_token.short_description = 'Refresh token (debug)'

    # ---------- Action: resend activation email ----------

    def resend_activation_email(self, request, queryset):
        """Admin action: resend activation email to selected inactive users."""
        inactive_users = queryset.filter(is_active=False)
        sent = 0
        for user in inactive_users:
            uidb64, token = self._activation_parts(user)
            try:
                send_activation_email(user, uidb64, token)
                sent += 1
            except Exception as exc:
                self.message_user(request, f'Failed to send activation to {user.email}: {exc}', level=messages.ERROR)
        if sent:
            self.message_user(request, f'Sent {sent} activation email(s).', level=messages.SUCCESS)
            

    def password_reset_token(self, obj):
        '''Show a fresh password reset token (debug/support).'''
        if not obj.is_active:
            return 'Activate the account first'
        # Build a fresh token (matches default_token_generator used in email)
        return default_token_generator.make_token(obj)
    password_reset_token.short_description = 'Password reset token'

    def password_reset_link(self, obj):
        '''Clickable backend link to /api/password_confirm/<uidb64>/<token>/.'''
        if not obj.is_active:
            return 'Activate the account first'
        uidb64 = urlsafe_base64_encode(force_bytes(obj.pk))
        token = default_token_generator.make_token(obj)

        # Build an absolute or root-absolute backend URL
        base = getattr(settings, 'BACKEND_BASE_URL', '')
        url = f'{base}/api/password_confirm/{uidb64}/{token}/' if base else f'/api/password_confirm/{uidb64}/{token}/'

        # Render copy-friendly input + CTA
        return format_html(
            '<div style="max-width:100%;">'
            '<input type="text" readonly value="{}" '
            'style="width:100%;padding:6px 8px;font-family:monospace;border:1px solid #e2e8f0;'
            'border-radius:8px;background:#f8fafc;margin-bottom:8px;" />'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:6px 10px;border-radius:8px;'
            'background:#3b82f6;color:#fff;text-decoration:none;font-weight:600;">Open reset link</a>'
            '</div>',
            url, url
        )
    password_reset_link.short_description = 'Password reset link'    


# Swap in our customized admin for the built-in User model
try:
    admin.site.unregister(User)  # Unregister default user admin if present
except admin.sites.NotRegistered:
    pass

admin.site.register(User, UserAdmin)  # Register our customized admin


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    """
    Simple admin to browse blacklisted refresh tokens (stored as SHA-256 hashes).
    """
    list_display = ('id', 'user', 'token_hash_short', 'created_at')  # Main columns
    readonly_fields = ('user', 'token_hash', 'created_at')  # All read-only (audit view)
    search_fields = ('user__username', 'user__email', 'token_hash')  # Quick search
    list_filter = ('created_at',)  # Filter by date

    def token_hash_short(self, obj):
        """Shorten the hash for cleaner list display."""
        return obj.token_hash[:12] + '…'
    token_hash_short.short_description = 'token hash'
