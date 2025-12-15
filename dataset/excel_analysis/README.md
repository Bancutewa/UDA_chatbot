# Excel Analysis - Chatbot Training Data

Phân tích file Excel "Final - Kịch bản phân tích sâu KH.xlsx" để trích xuất dữ liệu training cho chatbot telesales.

## 📊 Kết Quả

```
✓ Intents:           48
✓ Keywords:          454
✓ Flows:             17
✓ Domains:           Solar Energy, Real Estate
✓ Response Templates: 28
```

## 📂 Files Chính

| File                          | Size  | Mô tả              |
| ----------------------------- | ----- | ------------------ |
| `chatbot_training_data.json`  | 49KB  | Intents + flows    |
| `keyword_intent_mapping.json` | 140KB | Keyword mappings   |
| `analysis_report.txt`         | 4KB   | Chi tiết phân tích |
| `output/*.csv`                | 48KB  | 3 CSV exports      |

## 🚀 Quick Start

```bash
cd chatbot/dataset/excel_analysis
pip install pandas openpyxl numpy
python excel_analysis_tool.py
```

## 💻 Sử Dụng

### Load Data

```python
import json
with open('chatbot_training_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

intents = data['intents']              # 48 intents
flows = data['conversation_flows']    # 17 flows
keywords = json.load(open('keyword_intent_mapping.json'))  # 454 keywords
```

### Intent Classifier Demo

```python
from demo_intent_classifier import SimpleIntentClassifier

classifier = SimpleIntentClassifier()
response = classifier.get_response("Giá bao nhiêu?")
print(response)
```

## 📁 Cấu Trúc Data

### Intent Structure

```json
{
  "intent": "KH hỏi Giá",
  "keywords": ["bao tiền", "giá", "chi phí"],
  "response": "Dạ, hiện nay giá...",
  "sheet": "KBM SG 2",
  "row": 3
}
```

### Flow Structure

```json
{
  "scenario": "Hỏi thông tin",
  "steps": [{ "intent": "KH hỏi Giá", "response": "...", "row": 3 }],
  "sheet": "KBM SG 2"
}
```

## 🔧 Script

| Script                   | Mô tả                                |
| ------------------------ | ------------------------------------ |
| `excel_analysis_tool.py` | All-in-one tool với menu interactive |
|                          | - Excel analysis + CSV export        |
|                          | - Intent/keyword extraction          |
|                          | - Insights analytics                 |
|                          | - Intent classifier demo             |
|                          | - Run all automation                 |

## 🎯 Use Cases

1. **Intent Classification** - Train PhoBERT với 48 intents
2. **Keyword Matching** - 454 keywords cho pattern matching
3. **Dialog Management** - 17 conversation flows
4. **Response Generation** - 28 template responses

## 📈 Conversation Scenarios

1. Chào KH (2 flows)
2. Hỏi thông tin - KH hỏi bot (2 flows, 13.5 steps avg)
3. KH không quan tâm (2 flows, 9.5 steps avg)
4. KH bận (2 flows)
5. Đồng ý (2 flows)

## 💡 Integration

### NLU Pipeline

```
Input → Preprocess → Keyword Extract → Intent Classify
                           ↓
                    Entity Extract
                           ↓
                  Dialog Management
                           ↓
                Response Generation
                           ↓
                       Output
```

### Recommended Models

- **Intent**: PhoBERT (Vietnamese BERT)
- **Entity**: CRF hoặc LSTM-CRF
- **Dialog**: Finite State Machine (9 states)
- **Response**: Template-based + slot filling

## 📚 Source

- **Input**: `../../../thamkhao/Final - Kịch bản phân tích sâu KH.xlsx`
- **Sheets**: 3 (KBM SG 2, KBM SG, Trang tính10)
- **Total Rows**: 94
- **Total Columns**: 33

## ⚙️ Troubleshooting

```bash
# Windows encoding
chcp 65001

# Update deps
pip install pandas openpyxl numpy --upgrade

# Verify data
python -c "import json; d=json.load(open('chatbot_training_data.json',encoding='utf-8')); print(f'Intents: {len(d[\"intents\"])}')"
```

## 🎯 Next Steps

**Week 1-2**: Review data → Test demo classifier → Validate keywords  
**Week 3-4**: Implement PhoBERT → Build state machine → Add entities  
**Month 2**: CRM integration → Analytics → A/B testing  
**Month 3+**: Multi-domain → Personalization → Voice

---

**Version**: 1.0 | **Status**: ✅ Ready | **Updated**: Dec 2025
