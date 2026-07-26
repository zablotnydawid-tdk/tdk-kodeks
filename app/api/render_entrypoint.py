from __future__ import annotations

from datetime import datetime, timezone

from fastapi import BackgroundTasks, HTTPException, Request

from app.api import server as core


def _remove_post_route(path: str) -> None:
    core.app.router.routes = [
        route
        for route in core.app.router.routes
        if not (
            getattr(route, "path", None) == path
            and "POST" in (getattr(route, "methods", set()) or set())
        )
    ]


def _deliver_lead_notification(
    order_id: str,
    category: str,
    completeness: str,
    city: str,
    summary: str,
) -> None:
    try:
        order = core.order_store.get_order(order_id)

        core.send_lead_notification(
            client_email=order["email"],
            consumption_kwh=order["consumption_kwh"],
            price_per_kwh=order["price_per_kwh"],
            pv_power_kw=order["pv_power_kw"],
            pv_monthly_production_kwh=order["pv_monthly_production_kwh"],
            pdf_url=f"Zgloszenie asystenta: {order_id}",
            client_name=order["name"],
            client_phone=order["phone"],
            client_message=(
                f"Kategoria: {category}\n"
                f"Kompletnosc: {completeness}\n"
                f"Miasto: {city or 'brak'}\n\n"
                f"Podsumowanie:\n{core._clip_text(summary, 1100)}"
            ),
        )

        core.update_order_mail_status(
            order_id,
            "lead_mail",
            "MAIL_SENT",
            "Powiadomienie operatora zostalo wyslane.",
        )

    except Exception as exc:
        core.log_mail_failure(core.LEAD_NOTIFY_EMAIL, exc)

        try:
            core.update_order_mail_status(
                order_id,
                "lead_mail",
                "MAIL_NOT_CONFIRMED",
                "Powiadomienie e-mail nie zostalo potwierdzone. Sprawa jest zapisana w panelu.",
                exc,
            )
        except Exception:
            pass


_remove_post_route("/api/v1/assistant/intake")


@core.app.post(
    "/api/v1/assistant/intake",
    response_model=core.AssistantIntakeResponse,
)
def assistant_intake_nonblocking(
    payload: core.AssistantIntakeRequest,
    request_obj: Request,
    background_tasks: BackgroundTasks,
) -> core.AssistantIntakeResponse:

    core.enforce_anchorgrid_rate_limit(
        request_obj,
        "assistant_intake",
        core.ASSISTANT_RATE_LIMIT,
    )

    if not payload.consent_contact or not payload.consent_data:
        raise HTTPException(
            status_code=400,
            detail="Zgoda na kontakt i przetwarzanie danych jest wymagana.",
        )

    if len(payload.conversation) < 2:
        raise HTTPException(
            status_code=400,
            detail="Rozmowa jest zbyt krotka.",
        )

    if len(payload.conversation) > core.ASSISTANT_MAX_MESSAGES:
        raise HTTPException(
            status_code=400,
            detail="Rozmowa przekroczyla limit dlugosci.",
        )

    order_id = core.create_order_id()
    now = datetime.now(timezone.utc).isoformat()

    conversation = core._sanitize_assistant_messages(
        payload.conversation
    )
    description = core._assistant_order_description(payload)

    numeric = (
        payload.collected_data
        if isinstance(payload.collected_data, dict)
        else {}
    )

    order = {
        "order_id": order_id,
        "case_id": order_id,
        "source": "tdk_assistant_widget",
        "status": "waiting_for_operator_review",
        "operator_stage": "NEW",
        "created_at": now,
        "updated_at": now,
        "name": payload.name.strip(),
        "email": payload.email.strip(),
        "phone": payload.phone.strip(),
        "city": (payload.city or "").strip(),
        "message": core._clip_text(payload.summary, 1800),
        "description": description,
        "assistant_category": payload.category,
        "assistant_completeness": payload.completeness,
        "assistant_missing_data": payload.missing_data[:20],
        "assistant_safety_flags": payload.safety_flags[:20],
        "assistant_collected_data": numeric,
        "assistant_conversation": conversation,
        "consent_contact": payload.consent_contact,
        "consent_data": payload.consent_data,
        "amount": "operator review",
        "pdf_url": None,
        "pdf_path": None,
        "base_url": str(request_obj.base_url).rstrip("/"),
        "lead_mail_status": "MAIL_PENDING",
        "client_mail_status": "NOT_APPLICABLE",
        "consumption_kwh": float(
            numeric.get("monthly_consumption_kwh") or 0
        ),
        "price_per_kwh": float(
            numeric.get("price_per_kwh") or 0
        ),
        "pv_power_kw": float(
            numeric.get("pv_power_kwp") or 0
        ),
        "pv_monthly_production_kwh": float(
            numeric.get("monthly_production_kwh") or 0
        ),
    }

    core.order_store.create_order(order)

    background_tasks.add_task(
        _deliver_lead_notification,
        order_id,
        payload.category,
        payload.completeness,
        payload.city or "",
        payload.summary,
    )

    return core.AssistantIntakeResponse(
        case_id=order_id,
        status="waiting_for_operator_review",
        public_label="Zgloszenie przyjete",
        message=(
            "Sprawa zostala zapisana i czeka na "
            "weryfikacje operatora TDK&ProService."
        ),
        next_action=(
            "Zapisz numer sprawy i sprawdzaj status na /status."
        ),
        mail_status="MAIL_PENDING",
        mail_error_type=None,
        public_status_url=(
            f"https://tdkproservice.pl/status?case_id={order_id}"
        ),
    )


app = core.app