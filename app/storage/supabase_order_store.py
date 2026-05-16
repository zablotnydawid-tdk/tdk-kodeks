"""
Draft storage adapter for a future Supabase/PostgreSQL migration.

This module is intentionally not wired into the application yet. It contains
only the target method surface compatible with FileSystemOrderStore, so the
production JSON flow can stay unchanged until a controlled migration window.
"""

from datetime import datetime

from app.storage.order_store import create_order_id


class SupabaseOrderStore:
    """Future order store skeleton.

    TODO:
    - Add a Supabase/PostgreSQL client after storage migration is approved.
    - Keep method return values compatible with FileSystemOrderStore.
    - Preserve current order dict shape at the server boundary.
    - Add explicit migration tests before wiring this into app/api/server.py.
    """

    def __init__(self, client=None) -> None:
        # TODO: Accept an injected client after dependencies and ENV are approved.
        # No active connection is created here by design.
        self.client = client

    def create_order(self, data: dict) -> dict:
        """Create an order row and return the order dict used by server.py.

        TODO:
        - Generate order_id with create_order_id() when missing.
        - Map scalar fields to columns.
        - Store original technical input fields in input_data JSONB.
        - Set payment_status to "waiting_for_payment" by default.
        - Return a dict compatible with the current JSON order shape.
        """
        order = dict(data)
        order.setdefault("order_id", create_order_id())
        raise NotImplementedError("SupabaseOrderStore is a migration draft only.")

    def list_orders(self) -> list[dict]:
        """Return orders in the same order as FileSystemOrderStore.

        TODO:
        - Query orders ordered by id DESC or created_at DESC after validating
          which ordering matches current filename-based sorting most closely.
        - Convert database rows back to current order dicts for admin HTML.
        """
        raise NotImplementedError("SupabaseOrderStore is a migration draft only.")

    def get_order(self, order_id: str) -> dict:
        """Return one order dict by public KODEKS order id.

        TODO:
        - Query by id.
        - Raise RuntimeError(f"Nie znaleziono zgłoszenia: {order_id}") when empty,
          matching FileSystemOrderStore behavior.
        """
        raise NotImplementedError("SupabaseOrderStore is a migration draft only.")

    def update_order(self, order_id: str, data: dict) -> None:
        """Replace/update one order.

        TODO:
        - Update scalar columns and input_data JSONB without changing the public
          method contract.
        - Refresh updated_at server-side or in SQL.
        """
        raise NotImplementedError("SupabaseOrderStore is a migration draft only.")

    def mark_generated(self, order_id: str, pdf_url: str, pdf_path: str | None = None) -> dict:
        """Mark an order as generated after manual admin approval.

        TODO:
        - Preserve current status value: "paid_generated".
        - Set generated_at with seconds precision or database timestamp.
        - Store report_url from pdf_url.
        - Store report_path from pdf_path when present.
        - Return the updated order dict.
        """
        _generated_at = datetime.now().isoformat(timespec="seconds")
        raise NotImplementedError("SupabaseOrderStore is a migration draft only.")
