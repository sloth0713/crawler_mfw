import time
import random
import re
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse

def save_article_to_file(title, content, images=None, filename="article.txt"):
    """将爬取的文章保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"标题: {title}\n\n")
        f.write("正文内容:\n\n")
        f.write(content)
        
        # 添加图片信息
        if images:
            f.write("\n\n图片信息:\n\n")
            for i, image_info in enumerate(images, 1):
                f.write(f"图片 {i}: {image_info['filename']} (原URL: {image_info['url']})\n")
    print(f"\n文章已保存到文件: {filename}")

def setup_selenium_driver(headless=True):
    """设置Selenium WebDriver"""
    print("正在初始化Selenium WebDriver...")
    
    # 创建ChromeOptions对象
    chrome_options = Options()
    
    # 根据参数决定是否使用无头模式
    if headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
    
    # 添加一些选项以模拟真实浏览器
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15')
    
    # 禁用自动化控制特征
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 创建一个字典来禁用自动化
    prefs = {}
    prefs["credentials_enable_service"] = False
    prefs["profile.password_manager_enabled"] = False
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 创建WebDriver对象
    driver = webdriver.Chrome(options=chrome_options)
    
    # 禁用webdriver的特征
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("WebDriver初始化完成")
    return driver

def random_delay(min_seconds=1, max_seconds=3):
    """随机延迟，模拟真实用户行为"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"随机延迟 {delay:.2f} 秒...")
    time.sleep(delay)

def download_image(image_url, save_dir, image_index):
    """下载单张图片并保存到指定目录"""
    try:
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名
        file_extension = os.path.splitext(urlparse(image_url).path)[1]
        if not file_extension or len(file_extension) > 5:
            file_extension = ".jpg"
        filename = f"image_{image_index}{file_extension}"
        save_path = os.path.join(save_dir, filename)
        
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
            'Referer': 'https://www.mafengwo.cn/'
        }
        
        # 下载图片
        print(f"下载图片: {image_url}")
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        
        if response.status_code == 200:
            # 保存图片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"图片保存成功: {save_path}")
            return {"url": image_url, "filename": filename, "path": save_path}
        else:
            print(f"图片下载失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"下载图片时出错: {type(e).__name__}: {e}")
        return None

def fetch_images(driver, max_images=10, images_dir="images"):
    """从页面中提取并下载图片"""
    print("开始提取页面中的图片...")
    
    # 创建图片保存目录
    os.makedirs(images_dir, exist_ok=True)
    
    # 尝试不同的图片选择器
    image_selectors = [
        "img[src]",  # 所有带src属性的img标签
        "div.article img",  # 文章中的图片
        "div.content img",  # 内容中的图片
        "div._2R0mF img",  # 特定类中的图片
        "div._2l0YI img",  # 特定类中的图片
        "article img",  # 文章标签中的图片
        "main img",  # 主内容中的图片
        "img.photo",  # 照片类图片
        "img.pic",  # 图片类图片
        "img.image"  # 图像类图片
    ]
    
    downloaded_images = []
    tried_images = set()  # 用于去重
    
    # 尝试所有选择器
    for selector in image_selectors:
        if len(downloaded_images) >= max_images:
            break
        
        try:
            print(f"使用选择器: {selector}")
            img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"找到 {len(img_elements)} 个图片元素")
            
            for img_element in img_elements:
                if len(downloaded_images) >= max_images:
                    break
                
                try:
                    # 获取图片URL
                    img_url = None
                    # 尝试获取各种图片URL属性
                    for attr in ['src', 'data-src', 'data-original', 'data-url']:
                        url = img_element.get_attribute(attr)
                        if url and url.startswith(('http://', 'https://')):
                            img_url = url
                            break
                    
                    # 处理可能的相对URL
                    if not img_url and img_element.get_attribute('src'):
                        base_url = "https://www.mafengwo.cn"
                        img_url = img_element.get_attribute('src')
                        if not img_url.startswith(('http://', 'https://')):
                            if img_url.startswith('/'):
                                img_url = base_url + img_url
                            else:
                                img_url = base_url + '/' + img_url
                    
                    # 如果找到有效的URL且未尝试过
                    if img_url and img_url not in tried_images:
                        tried_images.add(img_url)
                        
                        # 过滤掉图标和小图片
                        try:
                            width = img_element.get_attribute('width')
                            height = img_element.get_attribute('height')
                            if width and height:
                                w, h = int(width), int(height)
                                if w < 100 or h < 100:
                                    print(f"跳过小图片: {img_url} ({w}x{h})")
                                    continue
                        except:
                            pass
                        
                        print(f"准备下载图片: {img_url}")
                        # 下载图片
                        image_info = download_image(img_url, images_dir, len(downloaded_images) + 1)
                        if image_info:
                            downloaded_images.append(image_info)
                            # 随机延迟，避免过快下载
                            random_delay(0.5, 1.5)
                except Exception as e:
                    print(f"处理图片元素时出错: {type(e).__name__}: {e}")
                    continue
        except Exception as e:
            print(f"使用选择器 {selector} 时出错: {type(e).__name__}: {e}")
            continue
    
    # 如果没有找到足够的图片，尝试获取所有img标签
    if len(downloaded_images) < max_images:
        try:
            print("尝试获取所有img标签...")
            all_images = driver.find_elements(By.TAG_NAME, "img")
            print(f"找到 {len(all_images)} 个图片元素")
            
            for img_element in all_images:
                if len(downloaded_images) >= max_images:
                    break
                
                try:
                    img_url = img_element.get_attribute('src')
                    if img_url and img_url.startswith(('http://', 'https://')) and img_url not in tried_images:
                        tried_images.add(img_url)
                        print(f"尝试下载其他图片: {img_url}")
                        image_info = download_image(img_url, images_dir, len(downloaded_images) + 1)
                        if image_info:
                            downloaded_images.append(image_info)
                            random_delay(0.5, 1.5)
                except:
                    continue
        except Exception as e:
            print(f"获取所有图片时出错: {type(e).__name__}: {e}")
    
    print(f"成功下载 {len(downloaded_images)} 张图片")
    return downloaded_images

def fetch_with_selenium(url, headless=True, max_retries=3, output_filename="article.txt", images_dir="images"):
    """使用Selenium爬取马蜂窝文章"""
    print(f"开始使用Selenium爬取: {url}")
    print(f"输出文件: {output_filename}")
    print(f"图片保存目录: {images_dir}")
    
    retry_count = 0
    while retry_count < max_retries:
        driver = None
        try:
            # 设置WebDriver
            driver = setup_selenium_driver(headless)
            
            # 访问URL
            print(f"第 {retry_count + 1} 次尝试访问URL")
            driver.get(url)
            
            # 随机延迟，让页面有时间加载
            random_delay(3, 5)
            
            # 模拟页面滚动，加载更多内容
            print("模拟页面滚动...")
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                random_delay(1, 2)
            
            # 尝试不同的方法获取标题
            title = "未找到标题"
            title_selectors = [
                "h1.title",  # 标题类名
                "h1._3He9I",  # 另一种标题类名
                "h1.head-title",  # 头部标题
                "h1.article-title",  # 文章标题
                "h1",  # 通用h1标签
                "meta[property='og:title']",  # og标签
                "meta[name='twitter:title']"  # twitter标签
            ]
            
            for selector in title_selectors:
                try:
                    if selector.startswith("meta"):
                        # 处理meta标签
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        title = element.get_attribute("content")
                    else:
                        # 处理普通元素
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        title = element.text.strip()
                    
                    # 如果找到了标题且长度合理
                    if title and len(title) > 5:
                        print(f"找到标题: {title}")
                        break
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"获取标题时出错: {type(e).__name__}: {e}")
                    continue
            
            # 尝试不同的方法获取正文内容
            content = ""
            content_selectors = [
                "div.article",  # 文章类
                "div#article-content",  # 文章内容ID
                "div._2R0mF",  # 另一种文章类
                "div._2l0YI",  # 另一种文章类
                "div.content",  # 内容类
                "div.article-content",  # 文章内容类
                "article",  # 文章标签
                "main",  # 主内容标签
                "div.post-body",  # 帖子主体
                "div.article_body",  # 文章主体
                "div.detail-content"  # 详细内容
            ]
            
            content_found = False
            for selector in content_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    content_text = element.text.strip()
                    
                    # 检查内容是否有足够的长度
                    if len(content_text) > 100:
                        content = content_text
                        content_found = True
                        print(f"找到正文内容，长度: {len(content_text)} 字符")
                        break
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"获取内容时出错: {type(e).__name__}: {e}")
                    continue
            
            # 如果没有找到合适的内容元素，尝试获取所有段落
            if not content_found:
                try:
                    paragraphs = driver.find_elements(By.TAG_NAME, "p")
                    meaningful_paragraphs = []
                    
                    for p in paragraphs:
                        text = p.text.strip()
                        if text and len(text) > 20:  # 只取较长的段落
                            meaningful_paragraphs.append(text)
                    
                    if meaningful_paragraphs:
                        content = "\n\n".join(meaningful_paragraphs)
                        print(f"从段落标签中提取内容，找到 {len(meaningful_paragraphs)} 个有意义的段落")
                    else:
                        # 尝试获取页面所有可见文本
                        body = driver.find_element(By.TAG_NAME, "body")
                        all_text = body.text
                        # 分割成句子，只保留较长的句子
                        sentences = re.split(r'[。！？.!?]\s*', all_text)
                        meaningful_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 30]
                        if meaningful_sentences:
                            content = "\n\n".join(meaningful_sentences)
                            print(f"从页面中提取所有文本，找到 {len(meaningful_sentences)} 个有意义的句子")
                except Exception as e:
                    print(f"尝试其他方法获取内容时出错: {type(e).__name__}: {e}")
            
            # 如果内容太短，可能是遇到了反爬
            if len(content) < 200:
                print("警告：获取的内容过短，可能是遇到了反爬措施")
                print(f"获取到的内容预览: {content[:100]}...")
                
                # 尝试访问移动版URL
                parsed_url = urlparse(url)
                if "www." in url:
                    mobile_url = url.replace("www.mafengwo.cn", "m.mafengwo.cn")
                    print(f"尝试访问移动版URL: {mobile_url}")
                    driver.get(mobile_url)
                    random_delay(3, 5)
                    
                    # 再次尝试获取内容
                    try:
                        # 移动版页面可能有不同的选择器
                        mobile_content_selectors = [
                            "div.article",
                            "div.content",
                            "div.detail",
                            "article",
                            "main"
                        ]
                        
                        for selector in mobile_content_selectors:
                            try:
                                element = driver.find_element(By.CSS_SELECTOR, selector)
                                mobile_content = element.text.strip()
                                if len(mobile_content) > 100:
                                    content = mobile_content
                                    content_found = True
                                    print(f"从移动版页面找到内容，长度: {len(mobile_content)} 字符")
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"尝试移动版URL时出错: {type(e).__name__}: {e}")
            
            # 抓取图片
            images = fetch_images(driver, max_images=10, images_dir=images_dir)
            
            # 如果最终还是没有获取到内容，认为失败
            if not content or len(content) < 100:
                raise ValueError("无法获取到足够的内容，可能是反爬措施阻止")
            
            # 显示获取到的标题和部分内容
            print(f"\n标题: {title}\n")
            print("正文内容预览:")
            # 只显示前200个字符作为预览
            content_preview = content[:200].replace('\n', ' ')
            print(f"{content_preview}...\n")
            
            # 保存文章到文件
            save_article_to_file(title, content, images, filename=output_filename)
            
            print("爬取成功！")
            return True
            
        except TimeoutException:
            retry_count += 1
            print(f"超时错误：页面加载超时")
            if retry_count < max_retries:
                print(f"将在 {retry_count * 3} 秒后重试...")
                time.sleep(retry_count * 3)
        except ValueError as e:
            retry_count += 1
            print(f"值错误: {e}")
            if retry_count < max_retries:
                print(f"将在 {retry_count * 3} 秒后重试...")
                time.sleep(retry_count * 3)
        except Exception as e:
            retry_count += 1
            print(f"错误: {type(e).__name__}: {e}")
            if retry_count < max_retries:
                print(f"将在 {retry_count * 3} 秒后重试...")
                time.sleep(retry_count * 3)
        finally:
            # 关闭WebDriver
            if driver:
                print("关闭WebDriver")
                driver.quit()
    
    print(f"达到最大重试次数 {max_retries}，爬取失败")
    return False

def main():
    print("马蜂窝文章爬虫 (Selenium版) 开始运行...")
    
    # 需要爬取的URL列表
    urls = [
        "https://www.mafengwo.cn/i/24597822.html",
        "https://www.mafengwo.cn/i/24684234.html",
        "https://www.mafengwo.cn/i/24445490.html",
        "https://www.mafengwo.cn/i/24700579.html",
        "https://www.mafengwo.cn/i/24421722.html"
    ]
    
    # 设置是否使用无头模式
    # 开发调试时可以设置为False，以便查看浏览器操作
    headless = False
    
    # 为每个URL单独爬取并保存
    for i, url in enumerate(urls, 1):
        print(f"\n=== 开始爬取第 {i} 个URL ===")
        print(f"目标URL: {url}")
        
        # 生成唯一的输出文件名和图片目录
        output_filename = f"article_{i}.txt"
        images_dir = f"images_{i}"
        
        # 执行爬取
        success = fetch_with_selenium(url, headless=headless, max_retries=3, 
                                     output_filename=output_filename, 
                                     images_dir=images_dir)
        
        if success:
            print(f"\n第 {i} 个URL爬取成功完成！")
        else:
            print(f"\n第 {i} 个URL爬取失败，请检查网络或稍后重试。")
        
        # 在URL之间添加延迟
        if i < len(urls):
            print(f"\n准备爬取下一个URL，等待10秒...")
            time.sleep(10)
    
    print("\n所有URL处理完成！")
    # 等待一段时间后退出
    print("\n程序将在5秒后退出...")
    time.sleep(5)

# 执行主函数
if __name__ == "__main__":
    main()