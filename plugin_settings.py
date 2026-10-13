import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTALLED_APPS = ["plugins.polio"]
TEMPLATES_DIRS = [os.path.join(BASE_DIR, "templates")]
AUTHENTICATION_CLASSES = ["rest_framework.authentication.BasicAuthentication"]


def org_unit_extra_permissions(user):
    """Polio users can read org units. Core ORs this with its own permissions."""
    from plugins.polio.permissions import POLIO_PERMISSION

    return [user.has_perm(POLIO_PERMISSION.full_name())]


def has_log_access(user, obj):
    """Audit access for campaigns. None when obj is not a campaign."""
    from plugins.polio.models import Campaign
    from plugins.polio.permissions import POLIO_PERMISSION

    if not isinstance(obj, Campaign):
        return None
    return user.has_perm(POLIO_PERMISSION.full_name()) and (
        Campaign.objects.filter_for_user(user).filter(id=obj.id).exists()
    )
