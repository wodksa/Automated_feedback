import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                            QComboBox, QTabWidget, QProgressBar, QMessageBox, QGroupBox,
                            QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QDesktopServices
from PyQt5.QtCore import QUrl
import csv
from openai import OpenAI
import json
import time

class DeepseekAnalyzer:
    def __init__(self, api_key, model="deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    def set_model(self, model):
        self.model = model
    
    def analyze_chat(self, chat_data, system_prompt=None):
        if not system_prompt:
            system_prompt = "你是一个专业的聊天记录分析助手。请分析以下聊天记录，提取关键信息，并生成简洁的摘要。"
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析以下聊天记录并提取关键信息：\n\n{chat_data}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"分析失败: {str(e)}"
    
    def improve_analysis(self, original_analysis, feedback):
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的聊天记录分析助手。请根据用户的反馈改进你的分析。"},
                {"role": "user", "content": f"原始分析：\n\n{original_analysis}\n\n用户反馈：\n\n{feedback}\n\n请根据反馈改进分析结果。"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"改进分析失败: {str(e)}"

class AnalysisWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, analyzer, chat_data, system_prompt=None):
        super().__init__()
        self.analyzer = analyzer
        self.chat_data = chat_data
        self.system_prompt = system_prompt
    
    def run(self):
        result = self.analyzer.analyze_chat(self.chat_data, self.system_prompt)
        self.finished.emit(result)

class AnalysisImproveWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, analyzer, original_analysis, feedback):
        super().__init__()
        self.analyzer = analyzer
        self.original_analysis = original_analysis
        self.feedback = feedback
    
    def run(self):
        result = self.analyzer.improve_analysis(self.original_analysis, self.feedback)
        self.finished.emit(result)

class ChatAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("聊天记录分析工具")
        self.setGeometry(100, 100, 1200, 800)
        self.analyzer = None
        self.chat_data = []
        self.analysis_result = ""
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
        self.analysis_history = []
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        # 创建主窗口部件
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 设置标签页
        settings_tab = self.create_settings_tab()
        analysis_tab = self.create_analysis_tab()
        results_tab = self.create_results_tab()
        
        self.tabs.addTab(settings_tab, "设置")
        self.tabs.addTab(analysis_tab, "分析")
        self.tabs.addTab(results_tab, "结果")
        
        # 添加Deepseek友情链接
        link_layout = QHBoxLayout()
        link_label = QLabel("Powered by:")
        deepseek_link = QPushButton("DeepSeek AI")
        deepseek_link.setStyleSheet("color: blue; text-decoration: underline;")
        deepseek_link.setCursor(Qt.PointingHandCursor)
        deepseek_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://deepseek.com/")))
        
        link_layout.addWidget(link_label)
        link_layout.addWidget(deepseek_link)
        link_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(link_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # API设置组
        api_group = QGroupBox("API 设置")
        api_layout = QVBoxLayout()
        
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Deepseek API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        
        model_layout = QHBoxLayout()
        model_label = QLabel("选择模型:")
        self.model_selector = QComboBox()
        self.model_selector.addItem("DeepSeek-V3", "deepseek-chat")
        self.model_selector.addItem("DeepSeek-R1", "deepseek-reasoner")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_selector)
        
        save_api_btn = QPushButton("保存API设置")
        save_api_btn.clicked.connect(self.save_api_settings)
        
        api_layout.addLayout(api_key_layout)
        api_layout.addLayout(model_layout)
        api_layout.addWidget(save_api_btn)
        api_group.setLayout(api_layout)
        
        # 系统提示词设置
        prompt_group = QGroupBox("系统提示词设置")
        prompt_layout = QVBoxLayout()
        
        prompt_label = QLabel("自定义系统提示词 (可选):")
        self.system_prompt = QTextEdit()
        self.system_prompt.setPlaceholderText("输入自定义的系统提示词，如不填写将使用默认提示词")
        
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.system_prompt)
        prompt_group.setLayout(prompt_layout)
        
        layout.addWidget(api_group)
        layout.addWidget(prompt_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_analysis_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 导入聊天记录部分
        import_group = QGroupBox("导入聊天记录")
        import_layout = QVBoxLayout()
        
        import_btn = QPushButton("导入CSV文件")
        import_btn.clicked.connect(self.import_csv)
        
        self.file_label = QLabel("未选择文件")
        
        import_layout.addWidget(import_btn)
        import_layout.addWidget(self.file_label)
        import_group.setLayout(import_layout)
        
        # 手动输入聊天记录部分
        manual_group = QGroupBox("手动输入聊天记录")
        manual_layout = QVBoxLayout()
        
        format_label = QLabel("请按照以下格式输入聊天记录：\n[时间] 作者: 消息\n例如：[2023-01-01 12:00:00] 张三: 你好！")
        
        self.manual_input = QTextEdit()
        self.manual_input.setPlaceholderText("在此输入聊天记录...")
        
        parse_btn = QPushButton("解析输入内容")
        parse_btn.clicked.connect(self.parse_manual_input)
        
        manual_layout.addWidget(format_label)
        manual_layout.addWidget(self.manual_input)
        manual_layout.addWidget(parse_btn)
        manual_group.setLayout(manual_layout)
        
        # 聊天记录预览
        preview_group = QGroupBox("聊天记录预览")
        preview_layout = QVBoxLayout()
        
        self.chat_preview = QTextEdit()
        self.chat_preview.setReadOnly(True)
        
        preview_layout.addWidget(self.chat_preview)
        preview_group.setLayout(preview_layout)
        
        # 分析控制
        control_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        control_layout.addWidget(self.analyze_btn)
        control_layout.addWidget(self.progress_bar)
        
        layout.addWidget(import_group)
        layout.addWidget(manual_group)
        layout.addWidget(preview_group)
        layout.addLayout(control_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 历史记录
        history_group = QGroupBox("历史分析记录")
        history_layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.show_history_item)
        
        history_layout.addWidget(self.history_list)
        history_group.setLayout(history_layout)
        
        # 分析结果
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        
        # 用户反馈
        feedback_group = QGroupBox("提供反馈")
        feedback_layout = QVBoxLayout()
        
        feedback_label = QLabel("请提供反馈以改进分析结果:")
        self.feedback_text = QTextEdit()
        
        improve_btn = QPushButton("提交反馈并改进")
        improve_btn.clicked.connect(self.improve_analysis)
        
        feedback_layout.addWidget(feedback_label)
        feedback_layout.addWidget(self.feedback_text)
        feedback_layout.addWidget(improve_btn)
        feedback_group.setLayout(feedback_layout)
        
        # 导出结果
        export_btn = QPushButton("导出分析结果到CSV")
        export_btn.clicked.connect(self.export_results)
        
        layout.addWidget(history_group)
        layout.addWidget(results_group)
        layout.addWidget(feedback_group)
        layout.addWidget(export_btn)
        
        tab.setLayout(layout)
        return tab

    def show_history_item(self, item):
        index = self.history_list.row(item)
        history_item = self.analysis_history[index]
        self.results_text.setText(history_item["result"])
        self.feedback_text.clear()

    def update_history_list(self):
        self.history_list.clear()
        for item in self.analysis_history:
            timestamp = item["timestamp"]
            type_text = "分析" if item["type"] == "analysis" else "改进"
            list_item = QListWidgetItem(f"{timestamp} - {type_text}结果")
            self.history_list.addItem(list_item)
        # 选中最新的记录
        if self.history_list.count() > 0:
            self.history_list.setCurrentRow(self.history_list.count() - 1)

    def analysis_completed(self, result):
        self.progress_bar.setValue(100)
        self.analyze_btn.setEnabled(True)
        self.analysis_result = result
        self.results_text.setText(result)
        
        # 保存分析结果到历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.analysis_history.append({
            "timestamp": timestamp,
            "result": result,
            "type": "analysis"
        })
        
        # 保存到文件
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_history, f, ensure_ascii=False, indent=4)
        
        # 更新历史记录列表
        self.update_history_list()
        
        # 自动切换到结果标签页
        self.tabs.setCurrentIndex(2)  # 结果标签页的索引是2

    def improve_analysis(self):
        feedback = self.feedback_text.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "提示", "请先输入反馈内容")
            return
        
        # 获取当前选中的历史记录
        current_row = self.history_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条历史记录")
            return
        
        current_item = self.analysis_history[current_row]
        
        # 调用分析器进行改进
        if self.analyzer:
            self.progress_bar.setValue(0)
            self.analyze_btn.setEnabled(False)
            self.analyzer.improve_analysis(current_item["result"], feedback, self.improvement_completed)

    def improvement_completed(self, result):
        self.progress_bar.setValue(100)
        self.analyze_btn.setEnabled(True)
        self.analysis_result = result
        self.results_text.setText(result)
        
        # 保存改进结果到历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.analysis_history.append({
            "timestamp": timestamp,
            "result": result,
            "type": "improvement"
        })
        
        # 保存到文件
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_history, f, ensure_ascii=False, indent=4)
        
        # 更新历史记录列表
        self.update_history_list()
        self.feedback_text.clear()

    def save_api_settings(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入有效的API Key")
            return
        
        model = self.model_selector.currentData()
        system_prompt = self.system_prompt.toPlainText().strip()
        
        try:
            self.analyzer = DeepseekAnalyzer(api_key, model)
            
            # 保存配置到文件
            config = {
                "api_key": api_key,
                "model": model,
                "system_prompt": system_prompt
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            QMessageBox.information(self, "成功", "API设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"API设置失败: {str(e)}")
    
    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            self.chat_data = []
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)  # 读取标题行
                
                for row in csv_reader:
                    if len(row) >= 3:  # 确保至少有时间、作者和消息
                        self.chat_data.append({
                            'time': row[0],
                            'author': row[1],
                            'message': row[2]
                        })
            
            self.file_label.setText(f"已导入: {os.path.basename(file_path)}")
            
            # 使用公共方法更新预览
            self.update_chat_preview()
            self.analyze_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入CSV文件失败: {str(e)}")
    
    def start_analysis(self):
        if not self.analyzer:
            QMessageBox.warning(self, "警告", "请先设置API Key")
            return
        
        if not self.chat_data:
            QMessageBox.warning(self, "警告", "请先导入聊天记录")
            return
        
        # 准备聊天数据
        chat_text = ""
        for item in self.chat_data:
            chat_text += f"[{item['time']}] {item['author']}: {item['message']}\n"
        
        system_prompt = self.system_prompt.toPlainText().strip()
        if not system_prompt:
            system_prompt = None
        
        # 创建并启动工作线程
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        
        self.worker = AnalysisWorker(self.analyzer, chat_text, system_prompt)
        self.worker.finished.connect(self.analysis_completed)
        self.worker.progress.connect(self.update_progress)
        self.worker.start()
        
        # 模拟进度条
        self.progress_timer = self.startTimer(100)
    
    def timerEvent(self, event):
        current = self.progress_bar.value()
        if current < 95:  # 保留最后5%给实际完成
            self.progress_bar.setValue(current + 1)
        else:
            self.killTimer(self.progress_timer)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def analysis_completed(self, result):
        self.progress_bar.setValue(100)
        self.analyze_btn.setEnabled(True)
        self.analysis_result = result
        self.results_text.setText(result)
        
        # 保存分析结果到历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.analysis_history.append({
            "timestamp": timestamp,
            "result": result,
            "type": "analysis"
        })
        
        # 保存到文件
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_history, f, ensure_ascii=False, indent=4)
        
        # 自动切换到结果标签页
        self.tabs.setCurrentIndex(2)  # 结果标签页的索引是2
    
    def improve_analysis(self):
        if not self.analyzer or not self.analysis_result:
            QMessageBox.warning(self, "警告", "请先完成分析")
            return
        
        feedback = self.feedback_text.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "警告", "请输入反馈内容")
            return
        
        # 创建并启动工作线程
        self.progress_bar.setValue(0)
        
        # 禁用提交按钮，防止重复提交
        sender = self.sender()
        if sender:
            sender.setEnabled(False)
        
        self.improve_worker = AnalysisImproveWorker(self.analyzer, self.analysis_result, feedback)
        self.improve_worker.finished.connect(self.improve_analysis_completed)
        self.improve_worker.progress.connect(self.update_progress)
        self.improve_worker.start()
        
        # 模拟进度条
        self.progress_timer = self.startTimer(100)
    
    def improve_analysis_completed(self, result):
        self.progress_bar.setValue(100)
        
        # 停止定时器
        if hasattr(self, 'progress_timer'):
            try:
                self.killTimer(self.progress_timer)
            except:
                pass
        
        # 重新启用提交按钮
        for widget in self.findChildren(QPushButton):
            if widget.text() == "提交反馈并改进":
                widget.setEnabled(True)
        
        self.analysis_result = result
        self.results_text.setText(result)
        self.feedback_text.clear()
        
        # 保存改进后的分析结果到历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.analysis_history.append({
            "timestamp": timestamp,
            "result": result,
            "type": "improvement"
        })
        
        # 保存到文件
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_history, f, ensure_ascii=False, indent=4)
        
        # 自动切换到结果标签页
        self.tabs.setCurrentIndex(2)  # 结果标签页的索引是2
        QMessageBox.information(self, "成功", "分析已根据反馈进行改进")
    
    def export_results(self):
        if not self.analysis_result:
            QMessageBox.warning(self, "警告", "没有可导出的分析结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存分析结果", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["分析结果"])
                writer.writerow([self.analysis_result])
            
            QMessageBox.information(self, "成功", f"分析结果已导出到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出结果失败: {str(e)}")
    
    def parse_manual_input(self):
        """解析用户手动输入的聊天记录"""
        text = self.manual_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入聊天记录")
            return
        
        self.chat_data = []
        lines = text.split('\n')
        
        # 解析每一行
        for line in lines:
            line = line.strip()
            if not line:  # 跳过空行
                continue
                
            # 尝试解析标准格式: [时间] 作者: 消息
            standard_format = False
            if line.startswith('[') and ']' in line:
                try:
                    time_part = line[1:line.index(']')]
                    rest_part = line[line.index(']')+1:].strip()
                    
                    if ':' in rest_part:
                        author = rest_part[:rest_part.index(':')].strip()
                        message = rest_part[rest_part.index(':')+1:].strip()
                        
                        self.chat_data.append({
                            'time': time_part,
                            'author': author,
                            'message': message
                        })
                        standard_format = True
                except:
                    standard_format = False
            
            # 如果不是标准格式，尝试简化格式: 作者: 消息
            if not standard_format:
                if ':' in line:
                    author = line[:line.index(':')].strip()
                    message = line[line.index(':')+1:].strip()
                    
                    # 使用当前时间作为时间戳
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    self.chat_data.append({
                        'time': current_time,
                        'author': author,
                        'message': message
                    })
                else:
                    # 如果连简化格式都不是，将整行作为消息，作者为"未知"
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.chat_data.append({
                        'time': current_time,
                        'author': "未知",
                        'message': line
                    })
        
        if not self.chat_data:
            QMessageBox.warning(self, "警告", "无法解析聊天记录，请检查格式")
            return
        
        # 更新预览
        self.update_chat_preview()
        self.analyze_btn.setEnabled(True)
        QMessageBox.information(self, "成功", f"已解析 {len(self.chat_data)} 条聊天记录")
    
    def update_chat_preview(self):
        """更新聊天记录预览"""
        preview_text = ""
        for i, item in enumerate(self.chat_data[:10]):  # 只显示前10条
            preview_text += f"[{item['time']}] {item['author']}: {item['message']}\n\n"
        
        if len(self.chat_data) > 10:
            preview_text += f"... 还有 {len(self.chat_data) - 10} 条消息 ..."
        
        self.chat_preview.setText(preview_text)
        
    def load_config(self):
        """从配置文件加载设置和历史记录"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 加载历史分析记录
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    self.analysis_history = json.load(f)
                # 更新历史记录列表
                self.update_history_list()
                
                # 设置API密钥
                if "api_key" in config and config["api_key"]:
                    self.api_key_input.setText(config["api_key"])
                
                # 设置模型
                if "model" in config and config["model"]:
                    index = self.model_selector.findData(config["model"])
                    if index >= 0:
                        self.model_selector.setCurrentIndex(index)
                
                # 设置系统提示词
                if "system_prompt" in config and config["system_prompt"]:
                    self.system_prompt.setText(config["system_prompt"])
                
                # 如果有API密钥，自动初始化分析器
                if "api_key" in config and config["api_key"] and "model" in config and config["model"]:
                    try:
                        self.analyzer = DeepseekAnalyzer(config["api_key"], config["model"])
                    except Exception as e:
                        print(f"初始化分析器失败: {str(e)}")
        except Exception as e:
            print(f"加载配置失败: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格使界面更现代
    
    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #4a86e8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3a76d8;
        }
        QPushButton:disabled {
            background-color: #cccccc;
        }
        QTextEdit, QLineEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4a86e8;
            width: 10px;
        }
    """)
    
    window = ChatAnalyzerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()