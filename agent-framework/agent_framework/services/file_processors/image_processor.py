"""
图片处理器 - 支持 OCR 文字识别

处理图片文件，使用 OCR 提取文字内容
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from .base_processor import BaseFileProcessor


class ImageProcessor(BaseFileProcessor):
    """图片处理器 - 支持 OCR 文字识别"""
    
    def __init__(self, ocr_engine: str = "paddle"):
        """
        初始化图片处理器
        
        Args:
            ocr_engine: OCR 引擎选择 ('paddle', 'tesseract', 'easy')
        """
        self.ocr_engine = ocr_engine
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化 OCR 引擎"""
        
        if self.ocr_engine == "paddle":
            try:
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    show_log=False
                )
            except ImportError:
                self.ocr = None
        
        elif self.ocr_engine == "tesseract":
            try:
                import pytesseract
                self.ocr = pytesseract
            except ImportError:
                self.ocr = None
        
        elif self.ocr_engine == "easy":
            try:
                import easyocr
                self.ocr = easyocr.Reader(['ch_sim', 'en'])
            except ImportError:
                self.ocr = None
    
    async def to_text(self, file_path: Path) -> str:
        """图片转文本 - OCR 识别"""
        
        text_parts = [
            f"[图片文件: {file_path.name}]\n",
            f"格式: {file_path.suffix}\n\n"
        ]
        
        # 获取图片基本信息
        try:
            from PIL import Image
            img = Image.open(file_path)
            text_parts.append(f"尺寸: {img.size[0]} x {img.size[1]}\n")
            text_parts.append(f"模式: {img.mode}\n\n")
        except ImportError:
            pass
        except Exception:
            pass
        
        # OCR 文字识别
        text_parts.append("=== OCR 识别结果 ===\n")
        
        if self.ocr is None:
            text_parts.append("[警告] OCR 引擎未初始化，请安装相应的库\n")
            text_parts.append(f"  - PaddleOCR: pip install paddleocr paddlepaddle\n")
            text_parts.append(f"  - Tesseract: pip install pytesseract (需要安装 Tesseract)\n")
            text_parts.append(f"  - EasyOCR: pip install easyocr\n")
        else:
            try:
                if self.ocr_engine == "paddle":
                    ocr_result = self.ocr.ocr(str(file_path), cls=True)
                    text_content = self._format_paddle_result(ocr_result)
                elif self.ocr_engine == "tesseract":
                    text_content = self._tesseract_ocr(file_path)
                elif self.ocr_engine == "easy":
                    ocr_result = self.ocr.readtext(str(file_path))
                    text_content = self._format_easy_result(ocr_result)
                else:
                    text_content = "未识别到文字"
                
                text_parts.append(text_content)
            except Exception as e:
                text_parts.append(f"[错误] OCR 识别失败: {str(e)}\n")
        
        return "".join(text_parts)
    
    def _format_paddle_result(self, result: List) -> str:
        """格式化 PaddleOCR 结果"""
        
        lines = []
        
        if result and result[0]:
            for item in result[0]:
                if item:
                    # item = [[[x1,y1], [x2,y2], ...], (text, confidence)]
                    box = item[0]
                    text, confidence = item[1]
                    lines.append(f"{text} (置信度: {confidence:.2f})")
        
        return "\n".join(lines) if lines else "未识别到文字"
    
    def _tesseract_ocr(self, file_path: Path) -> str:
        """Tesseract OCR"""
        
        from PIL import Image
        
        img = Image.open(file_path)
        
        try:
            text = self.ocr.image_to_string(img, lang='chi_sim+eng')
        except:
            # 如果中文包不可用，尝试英文
            text = self.ocr.image_to_string(img)
        
        return text if text.strip() else "未识别到文字"
    
    def _format_easy_result(self, result: List) -> str:
        """格式化 EasyOCR 结果"""
        
        lines = []
        
        for item in result:
            # item = ([[x1,y1], ...], text, confidence)
            box, text, confidence = item
            lines.append(f"{text} (置信度: {confidence:.2f})")
        
        return "\n".join(lines) if lines else "未识别到文字"
    
    async def from_text(self, text: str, output_path: Path) -> bool:
        """从文本生成图片（不支持）"""
        # 图片生成需要专门的图像生成模型
        # 这里只保存文本描述
        return False
    
    def get_supported_extensions(self) -> list[str]:
        return ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    
    async def batch_ocr(self, file_paths: List[Path]) -> Dict[str, str]:
        """批量 OCR 处理"""
        
        results = {}
        
        for file_path in file_paths:
            try:
                text = await self.to_text(file_path)
                results[str(file_path)] = text
            except Exception as e:
                results[str(file_path)] = f"OCR 失败: {str(e)}"
        
        return results
    
    async def ocr_with_structure(self, file_path: Path) -> Dict[str, Any]:
        """带结构信息的 OCR 识别"""
        
        if self.ocr_engine != "paddle" or self.ocr is None:
            text = await self.to_text(file_path)
            return {"text": text, "structure": None, "text_blocks": []}
        
        # PaddleOCR 带位置信息
        try:
            ocr_result = self.ocr.ocr(str(file_path), cls=True)
        except Exception as e:
            return {"text": "", "structure": None, "text_blocks": [], "error": str(e)}
        
        structured_result = {
            "text_blocks": [],
            "full_text": "",
            "layout": []
        }
        
        if ocr_result and ocr_result[0]:
            for item in ocr_result[0]:
                if item:
                    box, (text, confidence) = item
                    
                    # 计算文本块位置
                    x_coords = [p[0] for p in box]
                    y_coords = [p[1] for p in box]
                    
                    text_block = {
                        "text": text,
                        "confidence": float(confidence),
                        "position": {
                            "x_min": min(x_coords),
                            "x_max": max(x_coords),
                            "y_min": min(y_coords),
                            "y_max": max(y_coords)
                        },
                        "box": box
                    }
                    
                    structured_result["text_blocks"].append(text_block)
                    structured_result["full_text"] += text + "\n"
        
        return structured_result
