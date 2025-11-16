# 🤖 AI Chatbot Assistant

Chatbot AI đa năng với kiến trúc 7-layer, hỗ trợ authentication, trò chuyện, tạo ảnh và tạo audio.

## 🏗️ Kiến trúc 7 Layer

```
chatbot/
├── app.py                    # Entry point
├── src/
│   ├── core/                # ⚙️  Dependencies, config, logger, utils
│   │   ├── config.py         # Configuration management
│   │   ├── settings.py       # Constants & prompts
│   │   ├── logger.py         # Logging setup
│   │   └── exceptions.py     # Custom exceptions
│   │
│   ├── agents/              # 🤖 Model agents (LLM / Image / Audio / Intent analyzer)
│   │   ├── llm_agent.py      # Gemini API wrapper
│   │   ├── intent_agent.py   # Intent analysis agent
│   │   ├── image_agent.py    # Pollinations agent
│   │   └── audio_agent.py    # ElevenLabs agent
│   │
│   ├── intents/             # 🎯 Intent handlers
│   │   ├── base_intent.py    # Abstract base class
│   │   ├── intent_registry.py # Intent registry
│   │   ├── general_chat_intent.py
│   │   ├── generate_image_intent.py
│   │   └── generate_audio_intent.py
│   │
│   ├── services/            # 🔧 Business logic
│   │   ├── chat_service.py   # Chat operations
│   │   ├── image_service.py  # Image generation
│   │   └── audio_service.py  # Audio generation
│   │
│   ├── repositories/        # 💾 Database layer
│   │   ├── chat_history_repo.py  # JSON chat storage
│   │   └── user_repository.py    # User data storage
│   │
│   ├── schemas/             # 📋 Pydantic schemas
│   │   ├── chat.py          # Chat schemas
│   │   └── user.py          # User & auth schemas
│   │
│   ├── ui/                  # 🎨 User interface
│   │   ├── chat_interface.py # Chat UI
│   │   └── auth_interface.py # 🔐 Authentication UI
│   │
│   └── utils/               # 🛠️  Common helpers
│   └── main_chatbot.py      # 🎼 Orchestrator
│
└── data/
    └── audio_generations/   # Audio files
```

## 🚀 Cài đặt và Chạy

### 1. Cài đặt Dependencies

```bash
cd chatbot
pip install -r requirements.txt
```

### 2. Cấu hình API Key

**Cách 1: Environment variable**

```bash
export GEMINI_API_KEY=your_gemini_api_key_here
```

**Cách 2: File .env**

```bash
# Tạo file .env trong thư mục gốc
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
```

**Lấy API Key:**

- **Gemini API Key**: Đăng ký tại [Google AI Studio](https://aistudio.google.com/)
- Hoàn toàn miễn phí với 1,500 requests/ngày

### 3. Chạy Chatbot

**Tùy chọn A: Chạy trực tiếp**

```bash
streamlit run app.py
```

**Tùy chọn B: Chạy với Docker**

_Yêu cầu: Docker và Docker Compose đã được cài đặt_

```bash
# 1. Sao chép file env
cp env.example .env

# 2. Chỉnh sửa .env với API keys của bạn
nano .env

# 3. Build và chạy
docker-compose up --build

# Hoặc chạy background
docker-compose up -d --build
```

**Truy cập:** http://localhost:8501

### Docker Configuration

**Database:** Sử dụng MongoDB Atlas (cloud) - không cần MongoDB local

**Ports:**

- Chatbot: `8501`

**Volumes:**

- `./data`: Audio files và user data
- `./logs`: Application logs

**Lưu ý:** Dự án sử dụng MongoDB Atlas (cloud database), không cần MongoDB local.

## 🔐 Authentication System

### Đăng ký & Đăng nhập

- **User Registration**: Tạo tài khoản mới với email, username, password (tự động có role `user`)
- **User Login**: Đăng nhập với username/password
- **JWT Authentication**: Token-based authentication
- **Role-based Access**: Hỗ trợ 2 role `admin` và `user`
- **User-specific Sessions**: Mỗi user chỉ thấy chat sessions của mình trong sidebar
- **Session Management**: Hiển thị thời gian tạo, số tin nhắn, với UI thân thiện

### Quản lý người dùng (Admin only)

- **User Management**: Xem, chỉnh sửa, xóa user
- **Role Assignment**: Thay đổi role của user
- **Account Status**: Kích hoạt/vô hiệu hóa tài khoản

### Cấu hình Authentication

```bash
# Thêm vào .env
JWT_SECRET_KEY=your_secret_key_here
```

**Lưu ý**: Tất cả user mới đăng ký sẽ tự động có role `user`. Admin accounts chỉ có thể được tạo bởi script `create_admin.py` hoặc được cấp bởi admin hiện tại.

## 🎯 Tính năng

### 💬 Trò chuyện thông thường

- Intent: `general_chat`
- Hỗ trợ context từ lịch sử chat
- **Streaming Response**: Trả lời theo kiểu streaming (tương tự ChatGPT)
- Trả lời bằng tiếng Việt

### 🖼️ Tạo ảnh

- Intent: `generate_image`
- Sử dụng Pollinations AI
- Tự động tạo prompt chi tiết từ mô tả đơn giản

### 🎵 Tạo audio

- Intent: `generate_audio`
- Sử dụng ElevenLabs TTS
- Hỗ trợ Firecrawl cho URL scraping
- Voice: Nguyễn Ngân (Female, Vietnamese)

### 🏠 Tư vấn bất động sản (BĐS)

- Intent: `estate_query`
- RAG pipeline với Qdrant vector DB
- Tư vấn dựa trên dữ liệu thực tế

## 🧩 Intent System

Hệ thống intent thông minh tự động phân loại:

| Intent           | Keywords               | Handler             |
| ---------------- | ---------------------- | ------------------- |
| `general_chat`   | chào, hỏi, trò chuyện  | GeneralChatIntent   |
| `generate_image` | vẽ, tạo ảnh, hình ảnh  | GenerateImageIntent |
| `generate_audio` | đọc, phát, audio       | GenerateAudioIntent |
| `estate_query`   | nhà, đất, bất động sản | BDSIntent           |

## 🏛️ Kiến trúc Clean Architecture

### Dependency Direction:

```
UI → Services → Agents/Repositories → Core
```

### Benefits:

- **Separation of Concerns**: Mỗi layer có trách nhiệm riêng
- **Testability**: Dễ mock và test từng layer
- **Maintainability**: Dễ mở rộng và sửa đổi
- **Scalability**: Có thể thay thế implementation mà không ảnh hưởng layer khác

## 🛠️ Development

### Thêm Intent mới:

1. Tạo class kế thừa `BaseIntent` trong `src/intents/`
2. Register trong `IntentRegistry`
3. Thêm system prompt trong `settings.py`

### Thêm Service mới:

1. Tạo service class trong `src/services/`
2. Inject dependencies qua constructor
3. Implement business logic

### Database Migration:

- Chat history: JSON-based (dễ migrate)
- BDS data: Qdrant vectors
- Metadata: MongoDB (tương lai)

## 📊 Monitoring & Logging

- **Logs**: Tự động ghi vào `logs/chatbot.log`
- **Error Handling**: Custom exceptions cho từng module
- **API Status**: Real-time monitoring trong sidebar

## 🗄️ Database Support

### MongoDB Atlas Integration

- ✅ **Auto-detection**: Tự động detect MongoDB nếu có `MONGODB_URL`
- ✅ **Fallback**: Dùng JSON file nếu không có MongoDB
- ✅ **Migration**: Chuyển dữ liệu từ JSON sang MongoDB
- ✅ **Production Ready**: Scalable cho multi-user

📖 **Xem [MONGODB_SETUP.md](MONGODB_SETUP.md) để setup MongoDB Atlas**

### Database Architecture

```javascript
// MongoDB Collections
chat_sessions: {
  _id: "session_uuid",
  user_id: "default",
  title: "Chat Title",
  messages: [
    {role: "user", content: "...", timestamp: "..."},
    {role: "assistant", content: "..."}
  ],
  created_at: ISODate(),
  updated_at: ISODate()
}

// Future: BDS data
bds_properties: {...}
```

## 🔮 Tương lai

### Phase 2:

- [x] MongoDB integration cho chat history
- [ ] Qdrant production setup
- [ ] Real BDS data scraping
- [ ] Multi-user support
- [ ] API rate limiting

### Phase 3:

- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Plugin system
- [ ] Webhook integrations

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Implement theo clean architecture
4. Add tests
5. Submit PR

## 📝 License

MIT License - sử dụng tự do cho mục đích học tập và thương mại.

---

**Built with ❤️ using Streamlit, Agno, and modern AI APIs**
