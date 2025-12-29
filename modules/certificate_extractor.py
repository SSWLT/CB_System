import requests
import base64
import json
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CertificateExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = "glm-4.6v"
        
        if not self.api_key:
            raise ValueError("API key is required. Please set ZHIPU_API_KEY environment variable.")
    
    def extract_certificate_info(self, base64_str: str) -> dict:
        """
        调用GLM-4.6V API提取证书信息
        :param base64_str: 证书图片的base64字符串（包含data:image/jpeg;base64,前缀）
        :return: 提取的证书信息字典
        """
        try:
            # 移除base64字符串的前缀，只保留纯base64数据
            if base64_str.startswith('data:image'):
                base64_data = base64_str.split(',')[1]
            else:
                base64_data = base64_str
            
            logger.info(f"开始调用GLM-4.6V API提取证书信息，base64数据长度: {len(base64_data)} 字符")
            
            # 构建请求消息，严格按照智谱AI文档格式
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的证书信息提取系统，请从提供的证书图片中提取以下字段信息：学生所在学院、竞赛项目、学号、学生姓名、获奖类别（国家级、省级）、获奖等级（一等奖、二等奖、三等奖、金奖、银奖、铜奖、优秀奖）、竞赛类型（A类、B类）、主办单位、获奖时间、指导教师。如果某些字段无法识别，请留空。返回JSON格式，键名必须与上述字段名完全一致，不添加其他额外信息。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "请提取上述证书中的指定字段信息，返回JSON格式。"
                        }
                    ]
                }
            ]
            
            # 构建请求体，严格按照智谱AI文档要求
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            logger.debug(f"API请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 发送请求，添加超时设置
            logger.info(f"发送API请求到: {self.api_url}")
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=payload, 
                timeout=60,  # 延长超时时间，确保处理大型图片
                verify=True  # 启用SSL验证
            )
            
            # 记录响应状态
            logger.info(f"API响应状态码: {response.status_code}")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            logger.debug(f"API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 处理API响应
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                logger.info(f"API返回内容: {content}")
                
                # 解析JSON内容
                try:
                    extracted_info = json.loads(content)
                    logger.info(f"成功解析提取结果，包含字段: {list(extracted_info.keys())}")
                    return extracted_info
                except json.JSONDecodeError as e:
                    logger.error(f"解析提取结果失败，返回内容不是有效的JSON: {content[:200]}...")
                    logger.error(f"JSON解析错误: {str(e)}")
                    return {}
            else:
                logger.error(f"API返回格式异常，缺少choices字段: {result}")
                return {}
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"API请求HTTP错误: {str(e)}")
            if response is not None:
                logger.error(f"错误响应内容: {response.text}")
            raise Exception(f"证书信息提取失败: API请求错误 - {str(e)}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API请求连接错误: {str(e)}")
            raise Exception(f"证书信息提取失败: 网络连接错误 - {str(e)}")
        except requests.exceptions.Timeout as e:
            logger.error(f"API请求超时: {str(e)}")
            raise Exception(f"证书信息提取失败: 请求超时 - {str(e)}")
        except Exception as e:
            logger.error(f"提取证书信息失败: {str(e)}", exc_info=True)
            raise Exception(f"证书信息提取失败: {str(e)}")
    
    def validate_extracted_data(self, extracted_data: dict) -> dict:
        """
        验证提取的数据，确保字段完整性和格式正确性
        :param extracted_data: 提取的证书信息
        :return: 验证后的证书信息
        """
        required_fields = [
            "学生所在学院", "竞赛项目", "学号", "学生姓名", 
            "获奖类别", "获奖等级", "竞赛类型", "主办单位",
            "获奖时间", "指导教师"
        ]
        
        validated_data = {}
        
        for field in required_fields:
            validated_data[field] = extracted_data.get(field, "")
        
        return validated_data
