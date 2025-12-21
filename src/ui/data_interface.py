"""
Data Interface - Admin UI for data management
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from ..services.data_service import data_service
from ..services.qdrant_service import qdrant_service
from ..core.logger import logger
from ..schemas.user import UserSession, UserRole

class DataInterface:
    """Admin interface for data management"""

    def render(self, current_user: UserSession = None):
        """Render the data management interface (Admin only)"""
        # Check permission
        if not current_user or current_user.role != UserRole.ADMIN:
            st.error("❌ Chỉ quản trị viên mới có quyền truy cập quản lý dữ liệu.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_data_management = False
                st.rerun()
            return
        
        st.title("🗄️ Quản Lý Dữ Liệu Bất Động Sản")
        
        tab1, tab2 = st.tabs(["📤 Upload Dữ Liệu", "📊 Thống Kê"])
        
        with tab1:
            self.render_upload_tab()
        
        with tab2:
            self.render_stats_tab()

    def render_upload_tab(self):
        """Render upload tab"""
        st.subheader("Upload File Excel")
        
        uploaded_file = st.file_uploader("Chọn file Excel (.xlsx, .xls)", type=['xlsx', 'xls'])
        
        if uploaded_file:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            if st.button("🚀 Xử lý & Upload", key="process_btn"):
                with st.status("Đang xử lý dữ liệu...", expanded=True) as status:
                    try:
                        # Step 1: Process Excel
                        st.write("1️⃣ Đang đọc và chuẩn hóa dữ liệu Excel...")
                        file_content = uploaded_file.getvalue()
                        result = data_service.process_excel_upload(file_content, uploaded_file.name)
                        
                        if result.get("error"):
                            status.update(label="❌ Lỗi xử lý Excel", state="error")
                            st.error(result["error"])
                            return
                        
                        json_path = result["json_file"]
                        total_records = result["total_records"]
                        st.write(f"✅ Đã xử lý {total_records} bản ghi. File JSON: `{os.path.basename(json_path)}`")
                        
                        # Preview data
                        if result.get("preview"):
                            st.write("👀 Preview dữ liệu:")
                            st.dataframe(pd.DataFrame(result["preview"]))
                        
                        # Step 2: Upload to Qdrant
                        st.write("2️⃣ Đang tạo vector và upload lên Qdrant...")
                        upload_result = qdrant_service.upload_from_json(json_path)
                        
                        if upload_result["success"]:
                            status.update(label="✅ Hoàn tất!", state="complete")
                            st.success(f"🎉 Đã upload thành công {upload_result['uploaded']} bản ghi vào collection `{upload_result['collection']}`")
                        else:
                            status.update(label="❌ Lỗi upload Qdrant", state="error")
                            st.error(upload_result["error"])
                            
                    except Exception as e:
                        status.update(label="❌ Lỗi không xác định", state="error")
                        st.error(f"Error: {str(e)}")
                        logger.error(f"Upload flow failed: {e}")

    def render_stats_tab(self):
        """Render statistics tab"""
        st.subheader("Thống Kê Dữ Liệu")
        
        try:
            # Get collection info
            collection_name = qdrant_service.collection_name
            count = qdrant_service.client.count(collection_name).count
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Collection", collection_name)
            with col2:
                st.metric("Tổng số bản ghi", count)
                
            # Show recent uploads (from data service index)
            st.divider()
            st.subheader("Lịch sử Upload")
            
            if data_service.upload_index:
                history_data = []
                for filename, path in data_service.upload_index.items():
                    try:
                        mod_time = os.path.getmtime(path)
                        dt = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                        history_data.append({"File": filename, "Thời gian": dt, "Đường dẫn": path})
                    except:
                        pass
                
                if history_data:
                    st.dataframe(pd.DataFrame(history_data))
                else:
                    st.info("Chưa có lịch sử upload.")
            else:
                st.info("Chưa có lịch sử upload.")
                
        except Exception as e:
            st.error(f"Không thể kết nối Qdrant: {e}")

# Global instance
data_interface = DataInterface()
