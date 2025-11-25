import os
import re

# 定义匹配模式
PATTERN = r'© 2025 Mafengwo\.cn 京ICP备.*'

def clean_file(file_path):
    """
    清理文件中匹配的文本及之后的所有内容
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找匹配的位置
        match = re.search(PATTERN, content)
        if match:
            # 只保留匹配前的内容
            cleaned_content = content[:match.start()].strip()
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"已处理文件: {file_path}")
            return True
        else:
            print(f"文件中未找到匹配内容: {file_path}")
            return False
            
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {str(e)}")
        return False

def main():
    """
    遍历当前目录下所有.txt文件并处理
    """
    current_dir = os.getcwd()
    txt_files = [f for f in os.listdir(current_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print("当前目录下没有找到.txt文件")
        return
    
    print(f"找到 {len(txt_files)} 个.txt文件")
    
    processed_count = 0
    for txt_file in txt_files:
        file_path = os.path.join(current_dir, txt_file)
        if clean_file(file_path):
            processed_count += 1
    
    print(f"处理完成，共处理了 {processed_count} 个文件")

if __name__ == "__main__":
    main()