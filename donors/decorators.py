"""
RBAC decorator for the donors app.

Re-exports the project-wide staff_required check from authentication, so
there is exactly one implementation of "what counts as staff" shared by
inventory, requests and donors rather than three copies that could drift
apart. See authentication/decorators.py for the role model and rationale.
"""
from authentication.decorators import staff_required

__all__ = ["staff_required"]
