"""
Calendar UI for visit schedules.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st
from streamlit_calendar import calendar

from ..services.schedule_service import schedule_service
from ..schemas.user import UserSession, UserRole


STATUS_LABELS = {
    "pending": "🟡 Chờ xác nhận",
    "confirmed": "🟢 Đã xác nhận",
    "cancelled": "🔴 Đã hủy",
}

STATUS_COLORS = {
    "pending": "#fbbf24",
    "confirmed": "#22c55e",
    "cancelled": "#ef4444",
}


class ScheduleInterface:
    """Render visit schedules for admins and users."""

    def __init__(self):
        self.schedule_service = schedule_service

    @staticmethod
    def _build_calendar_events(events: List[Dict]) -> List[Dict]:
        calendar_events = []
        for event in events:
            start = event.get("requested_time")
            if not start:
                continue
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = start_dt + timedelta(hours=1)
                end = end_dt.isoformat()
            except Exception:
                start_dt = None
                end = start

            calendar_events.append({
                "id": event["id"],
                "title": f"{event.get('user_name', 'Khách')} • {event.get('district', '')}",
                "start": start_dt.isoformat() if start_dt else start,
                "end": end,
                "color": STATUS_COLORS.get(event.get("status"), "#6366f1"),
                "extendedProps": {
                    "status": event.get("status"),
                    "user_name": event.get("user_name"),
                    "district": event.get("district"),
                    "property_type": event.get("property_type"),
                    "notes": event.get("notes"),
                },
            })
        return calendar_events

    def _get_selected_event(self, schedule_id: Optional[str]) -> Optional[Dict]:
        if not schedule_id:
            return None
        return self.schedule_service.get(schedule_id)

    def render_admin_calendar(self, current_user: UserSession):
        if not current_user or current_user.role != UserRole.ADMIN:
            st.error("Bạn không có quyền truy cập lịch hẹn.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_schedule_management = False
                st.rerun()
            return

        st.title("📅 Lịch Xem Nhà")

        events = self.schedule_service.list_all()
        if not events:
            st.info("Chưa có lịch hẹn nào.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_schedule_management = False
                st.rerun()
            return

        status_counts: Dict[str, int] = {key: 0 for key in STATUS_LABELS.keys()}
        for event in events:
            status = event.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1

        metric_cols = st.columns(len(status_counts))
        for idx, (status, count) in enumerate(status_counts.items()):
            with metric_cols[idx]:
                st.metric(label=STATUS_LABELS.get(status, status), value=count)

        calendar_events = self._build_calendar_events(events)
        st.subheader("🗓 Calendar")
        calendar_options = {
            "initialView": "dayGridMonth",
            "locale": "vi",
            "height": 650,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": ""
            },
            "dayMaxEvents": True,
        }

        calendar_state = calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css="""
            .fc .fc-toolbar-title { font-size: 20px; }
            .fc-daygrid-dot-event .fc-event-title { font-weight: 600; }
            """
        )

        if calendar_state.get("eventClick"):
            st.session_state.selected_schedule_id = calendar_state["eventClick"]["event"]["id"]

        if "selected_schedule_id" not in st.session_state and events:
            st.session_state.selected_schedule_id = events[0]["id"]

        selected_event = self._get_selected_event(st.session_state.get("selected_schedule_id"))

        st.subheader("📋 Chi tiết lịch hẹn")
        if not selected_event:
            st.info("Click vào một sự kiện trên calendar để xem chi tiết.")
        else:
            st.markdown(f"**Khách hàng:** {selected_event.get('user_name', 'Không rõ')}")
            st.markdown(f"**Khu vực:** {selected_event.get('district', 'Quận 7')} • **Loại:** {selected_event.get('property_type', 'bất động sản')}")
            raw_time = selected_event.get("requested_time")
            if raw_time:
                try:
                    dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                    time_display = dt.strftime("%H:%M, %d/%m/%Y")
                except Exception:
                    time_display = raw_time
            else:
                time_display = "Không xác định"
            st.markdown(f"**Thời gian:** {time_display}")
            if selected_event.get("notes"):
                st.markdown(f"**Ghi chú của khách:** {selected_event['notes']}")

            status_options = list(STATUS_LABELS.keys())
            current_status = selected_event.get("status", "pending")
            status_index = status_options.index(current_status) if current_status in status_options else 0
            new_status = st.selectbox(
                "Trạng thái",
                options=status_options,
                index=status_index,
                format_func=lambda s: STATUS_LABELS.get(s, s),
                key=f"detail_status_{selected_event['id']}"
            )
            admin_note = st.text_area(
                "Ghi chú gửi khách",
                value=selected_event.get("admin_note", ""),
                key=f"detail_note_{selected_event['id']}"
            )

            col_actions = st.columns(2)
            with col_actions[0]:
                if st.button("💾 Cập nhật", key=f"update_schedule_{selected_event['id']}"):
                    self.schedule_service.update_status(selected_event["id"], new_status, admin_note)
                    st.success("Đã cập nhật lịch hẹn!")
                    st.rerun()
            with col_actions[1]:
                if st.button("🗑️ Xóa lịch", key=f"delete_schedule_{selected_event['id']}", type="secondary"):
                    if self.schedule_service.delete(selected_event["id"]):
                        st.success("Đã xóa lịch hẹn.")
                        st.session_state.pop("selected_schedule_id", None)
                        st.rerun()

        st.divider()
        if st.button("⬅️ Quay lại chat", use_container_width=True):
            st.session_state.show_schedule_management = False
            st.rerun()


    def render_user_summary(self, user_session: Optional[UserSession], container):
        if not user_session:
            return

        events = self.schedule_service.list_for_user(user_session.user_id)
        if not events:
            container.caption("📅 Chưa có lịch xem nhà")
            return

        container.caption(f"📅 Bạn có {len(events)} lịch xem nhà")
        for event in events[:3]:
            container.markdown(
                f"- {event.get('requested_time')} • {STATUS_LABELS.get(event.get('status'), '')}"
            )


schedule_interface = ScheduleInterface()

