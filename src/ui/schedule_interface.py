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
    "assigned": "🔵 Đã phân công",
    "confirmed": "🟢 Đã xác nhận",
    "rejected": "🟠 Đã từ chối",
    "cancelled": "🔴 Đã hủy",
}

STATUS_COLORS = {
    "pending": "#fbbf24",
    "assigned": "#3b82f6",
    "confirmed": "#22c55e",
    "rejected": "#f97316",
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

            # Build title with status for better visibility
            status = event.get("status", "pending")
            status_label = STATUS_LABELS.get(status, "")
            user_name = event.get('user_name', 'Khách')
            district = event.get('district', '')
            
            # For calendar title, include status if pending or assigned
            if status in ["pending", "assigned"]:
                title = f"{status_label} • {user_name} • {district}"
            else:
                title = f"{user_name} • {district}"
            
            calendar_events.append({
                "id": event["id"],
                "title": title,
                "start": start_dt.isoformat() if start_dt else start,
                "end": end,
                "color": STATUS_COLORS.get(status, "#6366f1"),
                "extendedProps": {
                    "status": status,
                    "user_name": user_name,
                    "district": district,
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
        
        # Title with refresh button
        col_title, col_refresh = st.columns([4, 1])
        with col_title:
            st.title("📅 Quản Lý Lịch Hẹn")
        with col_refresh:
            if st.button("🔄 Làm mới", key="refresh_calendar", use_container_width=True):
                # Clear cached data to force reload
                if "calendar_logged" in st.session_state:
                    del st.session_state.calendar_logged
                st.rerun()

        # Get events based on user role
        if current_user.role == UserRole.ADMIN:
            # Admin sees all events
            events = self.schedule_service.list_all()
        else:
            # Sale and User see only their own events
            events = self.schedule_service.list_for_user(current_user.user_id)
        
        # Auto-detect changes: compare current events hash with stored hash
        # This will auto-refresh when Sale confirms/rejects via email
        import hashlib
        import json
        events_hash = hashlib.md5(
            json.dumps(
                [(e.get("id"), e.get("status"), e.get("updated_at", "")) for e in events],
                sort_keys=True
            ).encode()
        ).hexdigest()
        stored_hash_key = f"calendar_events_hash_{current_user.user_id}"
        refresh_flag_key = f"calendar_refresh_pending_{current_user.user_id}"
        
        if stored_hash_key in st.session_state:
            if st.session_state[stored_hash_key] != events_hash:
                # Events have changed, but only refresh once to avoid loop
                if not st.session_state.get(refresh_flag_key, False):
                    st.session_state[stored_hash_key] = events_hash
                    st.session_state[refresh_flag_key] = True
                    st.rerun()
                else:
                    # Already refreshed, update hash and clear flag
                    st.session_state[stored_hash_key] = events_hash
                    st.session_state[refresh_flag_key] = False
        else:
            # First load, store hash
            st.session_state[stored_hash_key] = events_hash
            st.session_state[refresh_flag_key] = False
        
        # Debug logging (only log once per session to avoid spam)
        if "calendar_logged" not in st.session_state:
            from ..core.logger import logger
            logger.info(f"Calendar rendering: user_role={current_user.role}, user_id={current_user.user_id}, events_count={len(events) if events else 0}")
            if events:
                logger.debug(f"Event IDs: {[e.get('id') for e in events[:5]]}")
                logger.debug(f"Event user_ids: {[e.get('user_id') for e in events[:5]]}")
            st.session_state.calendar_logged = True
        
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
        # Only rerun if user clicked on a different event
        if calendar_state.get("eventClick"):
            clicked_event_id = calendar_state["eventClick"]["event"]["id"]
            current_selected = st.session_state.get("selected_schedule_id")
            if current_selected != clicked_event_id:
                st.session_state.selected_schedule_id = clicked_event_id
                st.rerun()
        
        if calendar_state.get("dateClick"):
            # Optional: handle date click to create new event
            pass

        # Auto-select first event if available and none selected
        # Use a key-based approach to avoid triggering rerun
        selected_event = None
        selected_schedule_id = st.session_state.get("selected_schedule_id")
        
        if selected_schedule_id:
            selected_event = self._get_selected_event(selected_schedule_id)
            # If selected event doesn't exist anymore, select first available
            if not selected_event and events:
                # Only update if different to avoid rerun loop
                if st.session_state.get("selected_schedule_id") != events[0]["id"]:
                    st.session_state.selected_schedule_id = events[0]["id"]
                    selected_event = self._get_selected_event(events[0]["id"])
        elif events:
            # Auto-select first event only once per page load
            auto_select_key = f"calendar_auto_selected_{len(events)}"
            if auto_select_key not in st.session_state:
                st.session_state.selected_schedule_id = events[0]["id"]
                st.session_state[auto_select_key] = True
                selected_event = self._get_selected_event(events[0]["id"])

        st.subheader("📋 Chi tiết lịch hẹn")
        if not selected_event:
            if events:
                st.info("👆 Click vào một sự kiện trên calendar để xem chi tiết.")
            else:
                st.info("Chưa có dữ liệu.")
        else:
            # Show status prominently, with different messages for Admin vs User
            status = selected_event.get("status", "pending")
            status_label = STATUS_LABELS.get(status, "")
            
            # Different messages based on user role
            if current_user.role == UserRole.ADMIN:
                # Admin view - focus on action needed
                if status == "pending":
                    st.warning(f"**{status_label}** - Lịch hẹn đang chờ được phân công cho nhân viên tư vấn.")
                elif status == "assigned":
                    st.info(f"**{status_label}** - Lịch hẹn đã được phân công, đang chờ Sale phản hồi.")
                elif status == "confirmed":
                    st.success(f"**{status_label}** - Lịch hẹn đã được Sale xác nhận.")
                elif status == "rejected":
                    st.error(f"**{status_label}** - Sale đã từ chối lịch hẹn này.")
                elif status == "cancelled":
                    st.info(f"**{status_label}** - Lịch hẹn đã bị hủy.")
            else:
                # User/Sale view - focus on customer perspective
                if status == "pending":
                    st.warning(f"**{status_label}** - Lịch hẹn của bạn đang chờ được Admin xem xét và phân công nhân viên tư vấn.")
                elif status == "assigned":
                    st.info(f"**{status_label}** - Lịch hẹn đã được phân công cho nhân viên tư vấn, đang chờ xác nhận.")
                elif status == "confirmed":
                    st.success(f"**{status_label}** - Lịch hẹn đã được xác nhận! Vui lòng có mặt đúng giờ.")
                elif status == "rejected":
                    st.error(f"**{status_label}** - Lịch hẹn đã bị từ chối.")
                elif status == "cancelled":
                    st.info(f"**{status_label}** - Lịch hẹn đã bị hủy.")
            
            # Display customer info - different for Admin vs User
            if current_user.role == UserRole.ADMIN:
                # Admin sees detailed information
                st.markdown(f"**Khách hàng:** {selected_event.get('user_name', 'Không rõ')}")
                user_email = selected_event.get('user_email')
                if user_email:
                    st.markdown(f"**Email:** {user_email}")
                # Get phone from separate field (not from notes)
                user_phone = selected_event.get('user_phone')
                if user_phone:
                    st.markdown(f"**Số điện thoại:** {user_phone}")
                st.markdown(f"**Khu vực:** {selected_event.get('district', 'Quận 7')} • **Loại:** {selected_event.get('property_type', 'bất động sản')}")
                if selected_event.get('listing_id'):
                    st.markdown(f"**Mã căn:** {selected_event.get('listing_id')}")
            else:
                # User sees basic information
                st.markdown(f"**Khách hàng:** {selected_event.get('user_name', 'Không rõ')}")
                st.markdown(f"**Khu vực:** {selected_event.get('district', 'Quận 7')} • **Loại:** {selected_event.get('property_type', 'bất động sản')}")
                if selected_event.get('listing_id'):
                    st.markdown(f"**Mã căn:** {selected_event.get('listing_id')}")
            
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
            
            # Notes display - different format for Admin vs User
            if selected_event.get("notes"):
                if current_user.role == UserRole.ADMIN:
                    st.markdown(f"**Ghi chú/Thông tin liên hệ:** {selected_event['notes']}")
                else:
                    # For users, only show relevant notes (hide technical details)
                    notes = selected_event['notes']
                    # Remove technical details like "Phone:", "Email:", "Listing:" for user view
                    user_friendly_notes = notes
                    # Keep only meaningful notes if any
                    if not any(keyword in notes for keyword in ['Phone:', 'Email:', 'Listing:']):
                        st.markdown(f"**Ghi chú:** {notes}")
                    # If notes only contain technical info, don't show to user
            
            # Show assignment info if assigned
            if selected_event.get("assigned_to_sale_id"):
                assigned_sale_name = selected_event.get("assigned_to_sale_name", "Không rõ")
                sale_response = selected_event.get("sale_response")
                if sale_response == "confirmed":
                    st.success(f"✅ Đã được xác nhận bởi: {assigned_sale_name}")
                elif sale_response == "rejected":
                    st.warning(f"❌ Đã bị từ chối bởi: {assigned_sale_name}")
                    if selected_event.get("rejection_reason"):
                        st.info(f"Lý do: {selected_event['rejection_reason']}")
                else:
                    st.info(f"🔵 Đã phân công cho: {assigned_sale_name} (đang chờ phản hồi)")

            # Admin assignment section
            if current_user.role == UserRole.ADMIN:
                st.divider()
                st.subheader("👥 Phân Công Cho Sale")
                if selected_event.get("status") in ["pending", "rejected"]:
                    # Get all Sale users
                    from ..repositories.user_repository import UserRepository
                    user_repo = UserRepository()
                    sale_users = user_repo.get_users_by_role("sale")
                    
                    if sale_users:
                        sale_options = {f"{sale.full_name} ({sale.email})": sale.id for sale in sale_users}
                        current_assigned = selected_event.get("assigned_to_sale_id")
                        current_index = 0
                        if current_assigned:
                            for idx, (name, sale_id) in enumerate(sale_options.items()):
                                if sale_id == current_assigned:
                                    current_index = idx
                                    break
                        
                        selected_sale_display = st.selectbox(
                            "Chọn Sale để phân công:",
                            options=list(sale_options.keys()),
                            index=current_index,
                            key=f"assign_sale_{selected_event['id']}"
                        )
                        selected_sale_id = sale_options[selected_sale_display]
                        
                        if st.button("📤 Phân Công", key=f"assign_button_{selected_event['id']}", type="primary"):
                            try:
                                from ..services.assignment_service import assignment_service
                                assignment_service.assign_schedule_to_sale(
                                    selected_event["id"],
                                    selected_sale_id,
                                    current_user
                                )
                                st.success("✅ Đã phân công lịch hẹn cho Sale! Email đã được gửi.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Lỗi: {str(e)}")
                    else:
                        st.warning("⚠️ Chưa có Sale nào trong hệ thống.")
                elif selected_event.get("status") == "assigned":
                    st.info("ℹ️ Lịch hẹn đã được phân công và đang chờ Sale phản hồi.")
                elif selected_event.get("status") == "confirmed":
                    st.success("✅ Lịch hẹn đã được Sale xác nhận.")
                elif selected_event.get("status") == "cancelled":
                    st.info("ℹ️ Lịch hẹn đã bị hủy.")
            
            # User cancel section
            if current_user.role == UserRole.USER and selected_event.get("user_id") == current_user.user_id:
                st.divider()
                st.subheader("❌ Hủy Lịch Hẹn")
                if selected_event.get("status") not in ["cancelled", "confirmed"]:
                    cancel_reason = st.text_area(
                        "Lý do hủy (tùy chọn):",
                        placeholder="Nhập lý do hủy lịch hẹn...",
                        height=80,
                        key=f"cancel_reason_{selected_event['id']}"
                    )
                    if st.button("❌ Hủy Lịch Hẹn", key=f"cancel_button_{selected_event['id']}", type="secondary"):
                        try:
                            from ..services.assignment_service import assignment_service
                            assignment_service.user_cancel_schedule(
                                selected_event["id"],
                                current_user.user_id,
                                cancel_reason if cancel_reason else None
                            )
                            st.success("✅ Đã hủy lịch hẹn thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi: {str(e)}")
                elif selected_event.get("status") == "cancelled":
                    st.info("ℹ️ Lịch hẹn này đã được hủy.")
                elif selected_event.get("status") == "confirmed":
                    st.warning("⚠️ Lịch hẹn đã được xác nhận. Vui lòng liên hệ nhân viên để hủy.")

            # Status is read-only - it changes automatically through workflow actions
            current_status = selected_event.get("status", "pending")
            
            # Admin and Sale can add notes
            if current_user.role in [UserRole.ADMIN, UserRole.SALE]:
                admin_note = st.text_area(
                    "Ghi chú gửi khách",
                    value=selected_event.get("admin_note", ""),
                    key=f"detail_note_{selected_event['id']}",
                    help="Ghi chú này sẽ được hiển thị cho khách hàng."
                )
            else:
                # User can only view notes
                if selected_event.get("admin_note"):
                    st.markdown(f"**Ghi chú từ nhân viên:** {selected_event.get('admin_note')}")
                admin_note = selected_event.get("admin_note", "")

            col_actions = st.columns(2)
            with col_actions[0]:
                # Admin and Sale can update notes only (status changes automatically through workflow)
                if current_user.role in [UserRole.ADMIN, UserRole.SALE]:
                    # Only show update button if note has changed
                    current_note = selected_event.get("admin_note", "")
                    if admin_note != current_note:
                        if st.button("💾 Cập nhật Ghi Chú", key=f"update_note_{selected_event['id']}"):
                            # Update only the note, keep current status
                            self.schedule_service.update_status(
                                selected_event["id"], 
                                current_status,  # Keep current status
                                admin_note
                            )
                            st.success("Đã cập nhật ghi chú!")
                            st.rerun()
                    else:
                        st.info("ℹ️ Ghi chú chưa thay đổi.")
                # User can only view - no action needed, status message already shown above
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

