import json
import uuid
from datetime import datetime
from pathlib import Path


def create_order_id() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"KODEKS-{date_part}-{unique_part}"


class FileSystemOrderStore:
    def __init__(self, orders_dir: Path | str = Path("data") / "orders") -> None:
        self.orders_dir = Path(orders_dir)
        self.orders_dir.mkdir(parents=True, exist_ok=True)

    def _order_path(self, order_id: str) -> Path:
        safe_order_id = order_id.replace("/", "").replace("\\", "")
        return self.orders_dir / f"{safe_order_id}.json"

    def create_order(self, data: dict) -> dict:
        order = dict(data)
        order.setdefault("order_id", create_order_id())
        self.update_order(order["order_id"], order)
        return order

    def list_orders(self) -> list[dict]:
        orders = []
        for path in sorted(self.orders_dir.glob("*.json"), reverse=True):
            try:
                orders.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return orders

    def get_order(self, order_id: str) -> dict:
        path = self._order_path(order_id)
        if not path.exists():
            raise RuntimeError(f"Nie znaleziono zgłoszenia: {order_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def update_order(self, order_id: str, data: dict) -> None:
        path = self._order_path(order_id)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def mark_generated(self, order_id: str, pdf_url: str, pdf_path: str | None = None) -> dict:
        order = self.get_order(order_id)
        order["status"] = "paid_generated"
        order["generated_at"] = datetime.now().isoformat(timespec="seconds")
        order["pdf_url"] = pdf_url
        if pdf_path is not None:
            order["pdf_path"] = pdf_path
        self.update_order(order_id, order)
        return order
