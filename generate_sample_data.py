import csv
import random
from datetime import datetime, timedelta

# 生成示例聊天数据
def generate_sample_chat_data(num_messages=1000):
    authors = ["张三", "李四", "王五", "赵六", "钱七"]
    topics = ["项目进度", "技术问题", "团队协作", "客户反馈", "产品设计"]
    
    messages = []
    start_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_messages):
        time_stamp = (start_time + timedelta(minutes=random.randint(1, 60*24*30))).strftime("%Y-%m-%d %H:%M:%S")
        author = random.choice(authors)
        topic = random.choice(topics)
        
        if topic == "项目进度":
            message = random.choice([
                "我们的项目进度如何？",
                f"模块{random.randint(1, 5)}已经完成了{random.randint(50, 100)}%",
                "我们需要加快进度，截止日期快到了",
                "今天的任务已经完成",
                "我们可能需要延期交付"
            ])
        elif topic == "技术问题":
            message = random.choice([
                f"我在实现{random.choice(['登录', '注册', '支付', '数据分析', '报表'])}功能时遇到了问题",
                "这个bug很难修复，我需要帮助",
                "我找到了一个更好的解决方案",
                "我们应该使用哪个框架？",
                "代码质量需要提高"
            ])
        elif topic == "团队协作":
            message = random.choice([
                "我们需要更好的沟通",
                "下周二开会讨论项目进展",
                "请大家及时更新任务状态",
                "我需要前端团队的支持",
                "谁能帮我review一下代码？"
            ])
        elif topic == "客户反馈":
            message = random.choice([
                "客户对新功能很满意",
                "客户报告了一个严重的bug",
                "客户希望增加一个新特性",
                "我们需要改进用户体验",
                "客户投诉系统响应太慢"
            ])
        else:  # 产品设计
            message = random.choice([
                "新的UI设计稿已经完成",
                "我们需要重新考虑产品定位",
                "用户调研结果显示我们需要简化流程",
                "竞品分析报告已经发到邮箱",
                "产品路线图需要更新"
            ])
        
        messages.append([time_stamp, author, message])
    
    return messages

# 将数据保存为CSV文件
def save_to_csv(data, filename="sample_chat_data.csv"):
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["时间", "作者", "消息"])
        writer.writerows(data)
    
    print(f"已生成示例数据并保存到 {filename}")

if __name__ == "__main__":
    data = generate_sample_chat_data(1000)
    save_to_csv(data, "d:/AI/project/Automated_feedback/sample_chat_data.csv")