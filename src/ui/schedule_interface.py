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
        # Allow all logged-in users to access (Admin sees all, Sale/User see only their own)
        if not current_user:
            st.error("Bạn cần đăng nhập để xem lịch hẹn.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_schedule_management = False
                st.rerun()
            return
        
        # Title
        st.title("📅 Quản Lý Lịch Hẹn")

        # Get events based on user role
        if current_user.role == UserRole.ADMIN:
            # Admin sees all events
            events = self.schedule_service.list_all()
        else:
            # Sale and User see only their own events
            events = self.schedule_service.list_for_user(current_user.user_id)
        
        # Show status metrics if there are events
        if events:
            status_counts: Dict[str, int] = {key: 0 for key in STATUS_LABELS.keys()}
            for event in events:
                status = event.get("status", "pending")
                status_counts[status] = status_counts.get(status, 0) + 1

            metric_cols = st.columns(len(status_counts))
            for idx, (status, count) in enumerate(status_counts.items()):
                with metric_cols[idx]:
                    st.metric(label=STATUS_LABELS.get(status, status), value=count)
        else:
            st.info("📭 Chưa có lịch hẹn nào. Calendar sẽ hiển thị khi có dữ liệu.")

        calendar_events = self._build_calendar_events(events) if events else []
        
        st.subheader("🗓 Calendar")
        # Enhanced calendar options to look more like Google Calendar
        calendar_options = {
            "initialView": "dayGridMonth",
            "locale": "vi",
            "height": 700,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
            },
            "views": {
                "dayGridMonth": {
                    "dayMaxEvents": 3,
                    "moreLinkClick": "popover"
                },
                "timeGridWeek": {
                    "slotMinTime": "06:00:00",
                    "slotMaxTime": "22:00:00"
                },
                "timeGridDay": {
                    "slotMinTime": "06:00:00",
                    "slotMaxTime": "22:00:00"
                },
                "listWeek": {
                    "listDayFormat": {"weekday": "long", "day": "numeric", "month": "long"}
                }
            },
            "eventDisplay": "block",
            "eventTimeFormat": {
                "hour": "2-digit",
                "minute": "2-digit",
                "hour12": False
            },
            "dayHeaderFormat": {"weekday": "long"},
            "firstDay": 1,  # Monday
            "weekNumbers": True,
            "navLinks": True,
            "editable": False,
            "selectable": True,
            "dayMaxEvents": True,
            "moreLinkClick": "popover",
        }

        calendar_state = calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css="""
            .fc {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .fc .fc-toolbar-title {
                font-size: 24px;
                font-weight: 500;
                color: #1a73e8;
            }
            .fc-button {
                background-color: #1a73e8;
                border-color: #1a73e8;
                color: white;
                font-weight: 500;
            }
            .fc-button:hover {
                background-color: #1557b0;
                border-color: #1557b0;
            }
            .fc-button-active {
                background-color: #1557b0;
                border-color: #1557b0;
            }
            .fc-daygrid-day-number {
                font-weight: 500;
            }
            .fc-event {
                border-radius: 4px;
                border: none;
                padding: 2px 4px;
                font-size: 13px;
                cursor: pointer;
            }
            .fc-event:hover {
                opacity: 0.9;
            }
            .fc-day-today {
                background-color: #e8f0fe !important;
            }
            .fc-col-header-cell {
                background-color: #f8f9fa;
                font-weight: 600;
                padding: 8px 0;
            }
            """
        )

        # Handle calendar interactions
        if calendar_state.get("eventClick"):
            st.session_state.selected_schedule_id = calendar_state["eventClick"]["event"]["id"]
            st.rerun()
        
        if calendar_state.get("dateClick"):
            # Optional: handle date click to create new event
            pass

        # Auto-select first event if available and none selected
        if "selected_schedule_id" not in st.session_state and events:
            st.session_state.selected_schedule_id = events[0]["id"]

        selected_event = self._get_selected_event(st.session_state.get("selected_schedule_id"))

        st.subheader("📋 Chi tiết lịch hẹn")
        if not selected_event:
            if events:
                st.info("👆 Click vào một sự kiện trên calendar để xem chi tiết.")
            else:
                st.info("📅 Calendar đang trống. Lịch hẹn sẽ xuất hiện ở đây khi có dữ liệu.")
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

            # Only Admin and Sale can edit status and notes
            if current_user.role in [UserRole.ADMIN, UserRole.SALE]:
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
            else:
                # User can only view
                current_status = selected_event.get("status", "pending")
                st.markdown(f"**Trạng thái:** {STATUS_LABELS.get(current_status, current_status)}")
                if selected_event.get("admin_note"):
                    st.markdown(f"**Ghi chú từ nhân viên:** {selected_event.get('admin_note')}")
                # Set defaults for update button (won't be shown anyway)
                new_status = current_status
                admin_note = selected_event.get("admin_note", "")

            col_actions = st.columns(2)
            with col_actions[0]:
                # Admin and Sale can update, User can only view
                if current_user.role in [UserRole.ADMIN, UserRole.SALE]:
                    if st.button("💾 Cập nhật", key=f"update_schedule_{selected_event['id']}"):
                        self.schedule_service.update_status(selected_event["id"], new_status, admin_note)
                        st.success("Đã cập nhật lịch hẹn!")
                        st.rerun()
                else:
                    # User can only view, show read-only message
                    st.info("ℹ️ Bạn chỉ có thể xem thông tin lịch hẹn. Liên hệ nhân viên để thay đổi.")
            with col_actions[1]:
                # Only Admin can delete schedules
                if current_user.role == UserRole.ADMIN:
                    if st.button("🗑️ Xóa lịch", key=f"delete_schedule_{selected_event['id']}", type="secondary"):
                        try:
                            if self.schedule_service.delete(selected_event["id"], current_user):
                                st.success("Đã xóa lịch hẹn.")
                                st.session_state.pop("selected_schedule_id", None)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {str(e)}")

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

