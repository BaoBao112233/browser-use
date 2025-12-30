import asyncio
import os
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from browser_use import Agent
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.google.chat import ChatGoogle
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Browser-use API Wrapper")

class ContactInfo(BaseModel):
    ho_ten: Optional[str] = Field(None, description="Họ và tên")
    so_dien_thoai: Optional[str] = Field(None, description="Số điện thoại")
    dia_chi: Optional[str] = Field(None, description="Địa chỉ")
    link_contract: Optional[str] = Field(None, description="Link contract (URL gốc)")
    nghe_nghiep: Optional[str] = Field(None, description="Nghề nghiệp")
    noi_lam_viec: Optional[str] = Field(None, description="Nơi làm việc")
    hoc_van: Optional[str] = Field(None, description="Học vấn")
    kinh_nghiem: Optional[str] = Field(None, description="Kinh nghiệm làm việc")
    ki_nang: Optional[str] = Field(None, description="Kĩ năng")
    hoat_dong: Optional[str] = Field(None, description="Hoạt động")

class ExtractRequest(BaseModel):
    urls: List[str]
    format: str = "csv"  # "csv" hoặc "excel"
    model: str = "gpt-4o"
    storage_state: Optional[str] = Field(None, description="Đường dẫn đến file storage_state.json (cookies)")
    headless: bool = True

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run_task")
async def run_task(request: BaseModel): # Giữ lại endpoint cũ cho tương thích
    # ... logic cũ ...
    pass

@app.post("/extract_contacts")
async def extract_contacts(request: ExtractRequest):
    try:
        import random
        from browser_use import Browser, BrowserProfile
        
        # Sử dụng User-Agent cố định và thực tế để khớp với cookies tốt hơn
        selected_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Random viewport size
        width = random.randint(1280, 1920)
        height = random.randint(720, 1080)
        
        # Kiểm tra file storage_state
        if request.storage_state:
            full_storage_path = os.path.abspath(request.storage_state)
            if not os.path.exists(full_storage_path):
                logger.warning(f"⚠️ storage_state file not found at {full_storage_path}")
            else:
                # Kiểm tra định dạng file cookies
                try:
                    import json
                    with open(full_storage_path, 'r') as f:
                        content = json.load(f)
                        
                    # Nếu là mảng (raw cookies), wrap lại thành định dạng Playwright
                    if isinstance(content, list):
                        logger.info(f"🔄 Chuyển đổi mảng cookies sang định dạng Playwright cho {request.storage_state}")
                        content = {"cookies": content, "origins": []}
                        with open(full_storage_path, 'w') as f:
                            json.dump(content, f, indent=2)
                    elif isinstance(content, dict) and 'cookies' not in content:
                        # Nếu là định dạng backup của extension (như user đang gặp)
                        if 'data' in content and 'version' in content:
                            logger.error(f"❌ File {request.storage_state} đang ở định dạng Backup/Encrypted của extension. Vui lòng Export dạng JSON thường.")
                        else:
                            logger.error(f"❌ Định dạng file {request.storage_state} không hợp lệ.")
                except Exception as e:
                    logger.error(f"❌ Không thể đọc hoặc parse file JSON: {e}")

        # Cấu hình BrowserProfile với các biện pháp Anti-bot
        profile = BrowserProfile(
            headless=request.headless,
            disable_security=True,
            user_agent=selected_ua,
            viewport={"width": width, "height": height},
            wait_between_actions=random.uniform(1.5, 3.0), # Tăng delay hơn nữa
            storage_state=request.storage_state if request.storage_state else None,
            traces_dir="/data/traces", # Lưu trace để debug
            minimum_wait_page_load_time=2.0,
            wait_for_network_idle_page_load_time=3.0
        )
        
        # Khởi tạo Browser (BrowserSession) với profile
        browser = Browser(browser_profile=profile)
        
        if 'gemini' in request.model.lower():
            llm = ChatGoogle(
                model=request.model,
                vertexai=True,
                project=os.getenv('GOOGLE_CLOUD_PROJECT'),
                location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1'),
                service_account_json=os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account.json')
            )
        else:
            llm = ChatOpenAI(model=request.model)
            
        all_contacts = []
        
        for url in request.urls:
            # Random viewport size
            width = random.randint(1280, 1920)
            height = random.randint(720, 1080)
            
            task = f"CHỈ ĐƯỢC PHÉP TRUY CẬP URL NÀY: {url}. " \
                   f"TUYỆT ĐỐI KHÔNG ĐƯỢC search Google hay DuckDuckGo nếu gặp lỗi. " \
                   f"Nếu gặp trang đăng nhập hoặc CAPTCHA, hãy đợi tối đa 10 giây xem có redirect không. " \
                   f"Nếu vẫn bị chặn, hãy báo cáo thất bại và dừng lại, KHÔNG ĐƯỢC đi tìm link khác. " \
                   f"Nếu vào được profile, hãy trích xuất đầy đủ thông tin: Họ tên, Số điện thoại, Địa chỉ, Nghề nghiệp, Nơi làm việc, Học vấn, Kinh nghiệm, Kĩ năng, Hoạt động."
            
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                output_model_schema=ContactInfo
            )
            
            # Cấu hình thêm cho agent session nếu cần (ví dụ wait_between_actions)
            # Lưu ý: browser-use 0.10.1 có thể có cách cấu hình khác nhau tùy version
            
            history = await agent.run()
            # Lấy kết quả cuối cùng dưới dạng cấu trúc
            result = history.final_result()
            if result:
                import json
                data = {}
                # Nếu kết quả là instance của ContactInfo (do output_model_schema)
                if hasattr(result, 'model_dump'):
                    data = result.model_dump()
                # Nếu kết quả là chuỗi JSON (đôi khi Agent trả về chuỗi thay vì object)
                elif isinstance(result, str):
                    try:
                        # Thử parse JSON nếu chuỗi có định dạng JSON
                        parsed = json.loads(result)
                        if isinstance(parsed, dict):
                            data = parsed
                        else:
                            data = {"ho_ten": result}
                    except:
                        data = {"ho_ten": result}
                else:
                    data = {"ho_ten": str(result)}
                
                data["link_contract"] = url # Đảm bảo link contract luôn đúng
                all_contacts.append(data)

        await browser.kill()

        if not all_contacts:
            return {"status": "failed", "message": "Không trích xuất được thông tin nào."}

        # Lưu file
        df = pd.DataFrame(all_contacts)
        filename = f"contacts_{int(asyncio.get_event_loop().time())}.{request.format}"
        filepath = os.path.join("/data", filename)
        
        if request.format.lower() == "csv":
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        else:
            df.to_excel(filepath, index=False)

        return {
            "status": "completed",
            "file_path": filepath,
            "contacts_count": len(all_contacts),
            "data": all_contacts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
