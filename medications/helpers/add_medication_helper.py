# medications/helpers/add_medication_helper.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from medications.models import MedicationItem, TakeMedicationEvent
from events.models import BaseEvent
import users


DEFAULT_WINDOW_MINUTES = 90  # dose completion window (from -> until)


@dataclass
class AddMedicationHelper:
    """
    Orchestrates creation/update/removal of MedicationItems and their
    related TakeMedicationEvents.

    Notes:
    - We preserve COMPLETED events on updates/deletes (audit).
    - We only regenerate/remove events that are NOT completed.
    - `created_by_user` should be the patient user in patient-scoped flows.
    """
    created_by_user: "users.User"  # AUTH_USER_MODEL instance

    # --------- public API ---------

    @transaction.atomic
    def create_item_with_events(
        self,
        *,
        item: MedicationItem,
        first_dose_at: Optional[str | timezone.datetime] = None,
        window_minutes: int = DEFAULT_WINDOW_MINUTES,
    ) -> MedicationItem:
        """
        Call this after you have a saved MedicationItem. It generates events.
        """
        self._generate_events_for_item(
            item=item,
            first_at=_coerce_dt_or_now(first_dose_at),
            window_minutes=window_minutes,
        )
        return item

    @transaction.atomic
    def update_item_and_events(
        self,
        *,
        item: MedicationItem,
        schedule_changed: bool = False,
        first_dose_at: Optional[str | timezone.datetime] = None,
        window_minutes: int = DEFAULT_WINDOW_MINUTES,
    ) -> MedicationItem:
        """
        If schedule_changed=True (e.g., frequency_hours or total_unit_amount changed)
        or a new first_dose_at is provided, we regenerate all **non-completed** events
        from the new baseline (preserving any completed ones).
        """
        if schedule_changed or first_dose_at is not None:
            self._regen_events_for_item(
                item=item,
                first_at=_coerce_dt_or_now(first_dose_at),
                window_minutes=window_minutes,
            )
        return item

    @transaction.atomic
    def remove_item_and_events(
        self,
        *,
        item: MedicationItem,
        delete_completed: bool = False,
    ) -> None:
        """
        Removes the MedicationItem and (by default) only non-completed events.
        Set delete_completed=True to hard-delete everything (generally not recommended).
        """
        qs = item.medication_events.all()
        if not delete_completed:
            qs = qs.exclude(status=BaseEvent.Status.COMPLETED)
        # Hard delete remaining events
        qs.delete()
        # Finally remove the item
        item.delete()

    # --------- internals ---------

    def _generate_events_for_item(
        self,
        *,
        item: MedicationItem,
        first_at: timezone.datetime,
        window_minutes: int,
    ) -> None:
        total = int(item.total_unit_amount or 0)
        freq_h = int(item.frequency_hours or 0)
        if total <= 0 or freq_h <= 0:
            return

        cursor = first_at
        window_delta = timedelta(minutes=window_minutes)

        unit_code = getattr(item.dosage_unit, "code", "")
        med_name = getattr(item.medication, "name", "Medication")
        desc_base = f"Take {med_name} {item.dosage_amount} {unit_code}".strip()

        created_by = self.created_by_user

        # Create one by one (multi-table inheritance safe)
        with transaction.atomic():
            for _ in range(total):
                start = cursor
                until = cursor + window_delta
                TakeMedicationEvent.objects.create(
                    created_by=created_by,
                    description=desc_base,
                    scheduled_to_complete_from=start,
                    scheduled_to_complete_until=until,
                    medication_item=item,
                )
                cursor = cursor + timedelta(hours=freq_h)

    def _regen_events_for_item(
        self,
        *,
        item: MedicationItem,
        first_at: timezone.datetime,
        window_minutes: int,
    ) -> None:
        """
        Delete all non-completed events for this item, then regenerate them.
        """
        item.medication_events.exclude(status=BaseEvent.Status.COMPLETED).delete()
        self._generate_events_for_item(item=item, first_at=first_at, window_minutes=window_minutes)


def _coerce_dt_or_now(dt_like: Optional[str | timezone.datetime]) -> timezone.datetime:
    """
    Accepts:
      - None -> returns timezone.now()
      - aware/naive datetime -> returns as aware (converted to timezone-aware)
      - ISO8601 string -> parses to aware datetime; fallback to now() on parse failure
    """
    if dt_like is None:
        return timezone.now()
    if isinstance(dt_like, timezone.datetime):
        return dt_like if timezone.is_aware(dt_like) else timezone.make_aware(dt_like)
    parsed = parse_datetime(str(dt_like))
    if parsed is None:
        return timezone.now()
    return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)
