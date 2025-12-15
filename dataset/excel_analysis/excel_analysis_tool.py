# -*- coding: utf-8 -*-
"""
Excel Analysis Tool - All-in-One
Comprehensive tool for analyzing telesales Excel data and training chatbot
"""

import pandas as pd
import numpy as np
import json
import sys
import io
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =============================================================================
# MODULE 1: EXCEL ANALYSIS
# =============================================================================

def load_excel_file(file_path):
    """Load Excel file and return all sheets"""
    try:
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"[OK] Loaded Excel file successfully")
        print(f"[OK] Number of sheets: {len(excel_file.sheet_names)}")
        print(f"[OK] Sheet names: {excel_file.sheet_names}\n")
        return excel_file
    except Exception as e:
        print(f"[ERROR] Error loading file: {e}")
        return None

def analyze_sheet(df, sheet_name):
    """Analyze a single sheet"""
    print(f"\n{'='*80}")
    print(f"ANALYZING SHEET: {sheet_name}")
    print(f"{'='*80}\n")
    
    print(f"[INFO] BASIC INFORMATION:")
    print(f"   - Rows: {len(df)}")
    print(f"   - Columns: {len(df.columns)}\n")
    
    # Data types
    print(f"[INFO] DATA TYPES:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        null_count = df[col].isna().sum()
        print(f"   - {col}: {df[col].dtype} (non-null: {non_null}, null: {null_count})")
    print()
    
    # Missing data
    missing = df.isna().sum()
    if missing.sum() > 0:
        print(f"[WARNING] MISSING DATA:")
        for col, count in missing.items():
            if count > 0:
                percentage = (count / len(df)) * 100
                print(f"   - {col}: {count} ({percentage:.2f}%)")
        print()
    
    return df

def export_to_csv(excel_file, file_path, output_dir="output"):
    """Export each sheet to CSV"""
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"[EXPORT] EXPORTING SHEETS TO CSV...")
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        clean_name = sheet_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_file = Path(output_dir) / f"{clean_name}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   [OK] Exported: {output_file}")
    print()

def run_excel_analysis():
    """Run basic Excel analysis"""
    file_path = r"thamkhao/Final - Kịch bản phân tích sâu KH.xlsx"
    
    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("EXCEL FILE ANALYSIS")
    print("="*80 + "\n")
    
    excel_file = load_excel_file(file_path)
    if not excel_file:
        return
    
    # Analyze each sheet
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        analyze_sheet(df, sheet_name)
    
    # Export to CSV
    export_to_csv(excel_file, file_path)
    print(f"\n[DONE] Analysis complete!\n")

# =============================================================================
# MODULE 2: DATA EXTRACTION
# =============================================================================

def extract_intent_data(df, sheet_name):
    """Extract intent training data from dataframe"""
    intents = []
    
    for idx, row in df.iterrows():
        intent_data = {}
        
        if 'Unnamed: 3' in df.columns and pd.notna(row.get('Unnamed: 3')):
            intent_name = str(row['Unnamed: 3']).strip()
            if intent_name and intent_name not in ['NaN', 'Khách phản hồi (Key)']:
                intent_data['intent'] = intent_name
        
        if 'Unnamed: 4' in df.columns and pd.notna(row.get('Unnamed: 4')):
            keywords_raw = str(row['Unnamed: 4'])
            if keywords_raw and keywords_raw not in ['Khách phản hồi (Key)', 'NaN']:
                keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]
                if keywords:
                    intent_data['keywords'] = keywords
        
        if 'Unnamed: 5' in df.columns and pd.notna(row.get('Unnamed: 5')):
            response = str(row['Unnamed: 5']).strip()
            if response and response not in ['ND tham khảo', 'NaN', 'KH trả lời']:
                intent_data['response'] = response
        
        if 'intent' in intent_data and ('keywords' in intent_data or 'response' in intent_data):
            intent_data['sheet'] = sheet_name
            intent_data['row'] = idx + 1
            intents.append(intent_data)
    
    return intents

def extract_conversation_flows(df, sheet_name):
    """Extract conversation flow patterns"""
    flows = []
    current_flow = None
    
    for idx, row in df.iterrows():
        if 'Kbm' in df.columns and pd.notna(row.get('Kbm')):
            kbm_value = str(row['Kbm']).strip()
            if kbm_value and kbm_value != 'Tình huống':
                if current_flow:
                    flows.append(current_flow)
                current_flow = {'scenario': kbm_value, 'steps': [], 'sheet': sheet_name}
        
        if current_flow and 'Unnamed: 5' in df.columns:
            response = row.get('Unnamed: 5')
            if pd.notna(response):
                response_str = str(response).strip()
                if response_str and response_str not in ['ND tham khảo', 'KH trả lời']:
                    step = {'response': response_str[:200], 'row': idx + 1}
                    if 'Unnamed: 3' in df.columns and pd.notna(row.get('Unnamed: 3')):
                        step['intent'] = str(row['Unnamed: 3']).strip()
                    current_flow['steps'].append(step)
    
    if current_flow:
        flows.append(current_flow)
    
    return flows

def run_data_extraction():
    """Run chatbot data extraction"""
    file_path = r"thamkhao/Final - Kịch bản phân tích sâu KH.xlsx"
    
    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return
    
    print("\n" + "="*80)
    print("CHATBOT DATA EXTRACTION")
    print("="*80 + "\n")
    
    excel_file = pd.ExcelFile(file_path, engine='openpyxl')
    all_intents = []
    all_flows = []
    
    for sheet_name in excel_file.sheet_names:
        print(f"[Processing] Sheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        intents = extract_intent_data(df, sheet_name)
        all_intents.extend(intents)
        print(f"  - Extracted {len(intents)} intents")
        
        flows = extract_conversation_flows(df, sheet_name)
        all_flows.extend(flows)
        print(f"  - Extracted {len(flows)} flows")
        print()
    
    # Generate JSON files
    training_data = {
        'version': '1.0',
        'description': 'Extracted from telesales scripts',
        'intents': all_intents,
        'conversation_flows': all_flows,
        'statistics': {
            'total_intents': len(all_intents),
            'total_flows': len(all_flows),
            'total_keywords': sum(len(i.get('keywords', [])) for i in all_intents)
        }
    }
    
    with open('chatbot_training_data.json', 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Training data saved: chatbot_training_data.json")
    
    # Generate keyword mapping
    keyword_map = {}
    for intent_data in all_intents:
        for keyword in intent_data.get('keywords', []):
            if keyword not in keyword_map:
                keyword_map[keyword] = []
            keyword_map[keyword].append({
                'intent': intent_data.get('intent', 'unknown'),
                'response': intent_data.get('response', '')[:100],
                'sheet': intent_data.get('sheet', '')
            })
    
    with open('keyword_intent_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(keyword_map, f, ensure_ascii=False, indent=2)
    print(f"[OK] Keyword mapping saved: keyword_intent_mapping.json")
    
    print(f"\n[DONE] Extracted {len(all_intents)} intents, {len(keyword_map)} keywords, {len(all_flows)} flows\n")

# =============================================================================
# MODULE 3: INSIGHTS ANALYSIS
# =============================================================================

def analyze_intent_distribution(training_data):
    """Analyze intent distribution"""
    print("\n" + "="*80)
    print("INTENT DISTRIBUTION")
    print("="*80 + "\n")
    
    intents = training_data.get('intents', [])
    sheet_counts = Counter(intent.get('sheet', 'Unknown') for intent in intents)
    
    for sheet, count in sheet_counts.most_common():
        percentage = (count / len(intents)) * 100 if intents else 0
        print(f"  {sheet:20s}: {count:3d} intents ({percentage:5.2f}%)")

def analyze_keyword_patterns(keyword_mapping):
    """Analyze keyword patterns"""
    print("\n" + "="*80)
    print("KEYWORD PATTERNS")
    print("="*80 + "\n")
    
    multi_intent_keywords = {k: v for k, v in keyword_mapping.items() if len(v) > 1}
    
    print(f"Total keywords: {len(keyword_mapping)}")
    print(f"Multi-intent keywords: {len(multi_intent_keywords)}")
    print(f"Single-intent keywords: {len(keyword_mapping) - len(multi_intent_keywords)}")

def run_insights_analysis():
    """Run advanced insights analysis"""
    try:
        with open('chatbot_training_data.json', 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        with open('keyword_intent_mapping.json', 'r', encoding='utf-8') as f:
            keyword_mapping = json.load(f)
    except:
        print("[ERROR] Data files not found. Run data extraction first.")
        return
    
    print("\n" + "="*80)
    print("INSIGHTS ANALYSIS")
    print("="*80)
    
    analyze_intent_distribution(training_data)
    analyze_keyword_patterns(keyword_mapping)
    
    # Export report
    with open('analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("CHATBOT DATA ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total Intents: {len(training_data['intents'])}\n")
        f.write(f"Total Keywords: {len(keyword_mapping)}\n")
        f.write(f"Total Flows: {len(training_data['conversation_flows'])}\n")
    
    print(f"\n[OK] Report saved: analysis_report.txt\n")

# =============================================================================
# MODULE 4: INTENT CLASSIFIER DEMO
# =============================================================================

class SimpleIntentClassifier:
    """Simple keyword-based intent classifier"""
    
    def __init__(self):
        try:
            with open('chatbot_training_data.json', 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
            with open('keyword_intent_mapping.json', 'r', encoding='utf-8') as f:
                self.keyword_mapping = json.load(f)
            self.intents = self.training_data.get('intents', [])
        except:
            print("[ERROR] Data files not found")
            self.training_data = {}
            self.keyword_mapping = {}
            self.intents = []
    
    def classify_intent(self, user_input: str) -> List[Tuple[str, float, str]]:
        """Classify user input to intents"""
        user_input_lower = user_input.lower()
        intent_scores = {}
        intent_responses = {}
        
        for keyword, intent_list in self.keyword_mapping.items():
            if keyword.lower() in user_input_lower:
                for intent_info in intent_list:
                    intent_name = intent_info.get('intent', 'Unknown')
                    response = intent_info.get('response', '')
                    
                    if intent_name not in intent_scores:
                        intent_scores[intent_name] = 0
                        intent_responses[intent_name] = response
                    intent_scores[intent_name] += 1
        
        if not intent_scores:
            return [("Unknown", 0.0, "Xin lỗi, tôi chưa hiểu câu hỏi của bạn.")]
        
        max_score = max(intent_scores.values())
        results = []
        
        for intent, score in intent_scores.items():
            confidence = score / max_score
            response = intent_responses.get(intent, '')
            results.append((intent, confidence, response))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_response(self, user_input: str) -> str:
        """Get best response for user input"""
        classifications = self.classify_intent(user_input)
        
        if classifications:
            intent, confidence, response = classifications[0]
            if confidence > 0.5:
                return response
        
        return "Xin lỗi, tôi chưa hiểu câu hỏi của bạn."

def run_classifier_demo():
    """Run intent classifier demo"""
    print("\n" + "="*80)
    print("INTENT CLASSIFIER DEMO")
    print("="*80 + "\n")
    
    classifier = SimpleIntentClassifier()
    
    if not classifier.intents:
        print("[ERROR] No training data. Run data extraction first.")
        return
    
    print(f"Loaded {len(classifier.intents)} intents, {len(classifier.keyword_mapping)} keywords\n")
    
    test_queries = [
        "Giá điện mặt trời bao nhiêu?",
        "Có thể trả góp không?",
        "Các bạn là công ty gì?",
        "Dự án ở đâu?",
        "Tôi không có nhu cầu"
    ]
    
    print("Testing queries:\n")
    for query in test_queries:
        response = classifier.get_response(query)
        print(f"Q: {query}")
        print(f"A: {response[:100]}...\n")
    
    print("[DONE] Demo complete\n")

# =============================================================================
# MODULE 5: RUN ALL
# =============================================================================

def run_all_analysis():
    """Run all analysis steps"""
    print("\n" + "="*80)
    print("RUNNING ALL ANALYSIS STEPS")
    print("="*80 + "\n")
    
    print("[Step 1/4] Excel Analysis...")
    run_excel_analysis()
    
    print("[Step 2/4] Data Extraction...")
    run_data_extraction()
    
    print("[Step 3/4] Insights Analysis...")
    run_insights_analysis()
    
    print("[Step 4/4] Classifier Demo...")
    run_classifier_demo()
    
    print("="*80)
    print("ALL STEPS COMPLETED!")
    print("="*80 + "\n")

# =============================================================================
# MAIN MENU
# =============================================================================

def print_menu():
    """Print main menu"""
    print("\n" + "="*80)
    print("EXCEL ANALYSIS TOOL - ALL-IN-ONE")
    print("="*80)
    print("\n1. Excel Analysis (analyze + export CSV)")
    print("2. Data Extraction (extract intents + keywords)")
    print("3. Insights Analysis (generate insights report)")
    print("4. Classifier Demo (test intent classification)")
    print("5. Run All (execute all steps)")
    print("6. Exit\n")

def main():
    """Main function"""
    while True:
        print_menu()
        
        try:
            choice = input("Select option (1-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting...")
            break
        
        if choice == '1':
            run_excel_analysis()
        elif choice == '2':
            run_data_extraction()
        elif choice == '3':
            run_insights_analysis()
        elif choice == '4':
            run_classifier_demo()
        elif choice == '5':
            run_all_analysis()
        elif choice == '6':
            print("\nGoodbye!")
            break
        else:
            print("\n[ERROR] Invalid option. Please choose 1-6.")

if __name__ == "__main__":
    main()

