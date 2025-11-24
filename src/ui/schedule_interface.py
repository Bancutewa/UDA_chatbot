"""
Calendar UI for visit schedules.
"""
from typing import Optional

import streamlit as st

from ..services.schedule_service import schedule_service
from ..schemas.user import UserSession, UserRole


STATUS_LABELS = {
    "pending": "🟡 Chờ xác nhận",
    "confirmed": "🟢 Đã xác nhận",
    "cancelled": "🔴 Đã hủy",
}


class ScheduleInterface:
    """Render visit schedules for admins and users."""

    def __init__(self):
        self.schedule_service = schedule_service

    def render_admin_calendar(self, current_user: UserSession):
        if not current_user or current_user.role != UserRole.ADMIN:
            st.error("Bạn không có quyền truy cập lịch hẹn.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_schedule_management = False
                st.rerun()
            return

        st.title("📅 Lịch Xem Nhà")
        st.caption("Toàn bộ lịch hẹn sẽ đồng bộ với calendar của admin.")

        events = self.schedule_service.list_all()
        if not events:
            st.info("Chưa có lịch hẹn nào.")
        else:
            for event in events:
                with st.container():
                    st.subheader(f"{event.get('user_name', 'Khách')} • {event.get('district', 'Quận 7')}")
                    st.caption(f"Loại: {event.get('property_type', 'bất động sản')}")

                    st.markdown(f"**Thời gian:** {event.get('requested_time')}")
                    if event.get("notes"):
                        st.markdown(f"**Ghi chú của khách:** {event['notes']}")

                    st.markdown(f"**Trạng thái:** {STATUS_LABELS.get(event.get('status'), event.get('status'))}")

                    col1, col2 = st.columns([3, 2])
                    with col1:
                        status_options = ["pending", "confirmed", "cancelled"]
                        current_status = event.get("status", "pending")
                        current_index = status_options.index(current_status) if current_status in status_options else 0

                        new_status = st.selectbox(
                            "Cập nhật trạng thái",
                            options=status_options,
                            index=current_index,
                            key=f"status_{event['id']}",
                        )
                        admin_note = st.text_input(
                            "Ghi chú cho khách",
                            value=event.get("admin_note", ""),
                            key=f"note_{event['id']}",
                        )
                    with col2:
                        if st.button("💾 Lưu", key=f"save_{event['id']}"):
                            self.schedule_service.update_status(event["id"], new_status, admin_note)
                            st.success("Đã cập nhật lịch hẹn!")
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

