from fastapi import APIRouter, HTTPException
from app.config import settings
from app.schemas.predict import UserInput
from app.services.predict_service import ObesityPredictorComplete
from openai import OpenAI
from typing import Dict, Any

router = APIRouter(prefix="/predict", tags=["Prediction"])

# kiểm tra API key trước khi khởi client
if not settings.openrouter_api_key:
    raise RuntimeError("OpenRouter API key is not set in settings.openrouter_api_key")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key
)

predictor = ObesityPredictorComplete()

@router.post("/")
def predict_obesity(data: UserInput):
    try:
        result = predictor.predict_complete(data.dict())
        
        # Xử lý BMI - chuyển đổi sang float nếu cần và định dạng
        try:
            bmi_value = float(result['bmi'])
            bmi_formatted = f"{bmi_value:.1f}"
        except (ValueError, TypeError):
            bmi_formatted = str(result['bmi'])

        # Prompt cho phân tích tổng quát
        general_prompt = f"""
Bạn là một chuyên gia dinh dưỡng và sức khỏe giàu kinh nghiệm. Hãy phân tích tình trạng sức khỏe và đưa ra khuyến nghị chi tiết cho người dùng sau:

THÔNG TIN NGƯỜI DÙNG:
- Giới tính: {data.gender}
- Tuổi: {data.age}
- Chiều cao: {data.height} mét
- Cân nặng: {data.weight} kg
- Chỉ số BMI: {bmi_formatted} ({result['phân_loại_bmi']})
- Dự đoán tình trạng cân nặng: {result['dự_đoán']}

YÊU CẦU PHÂN TÍCH VÀ KHUYẾN NGHỊ:

1. PHÂN TÍCH TÌNH TRẠNG HIỆN TẠI:
   - Đánh giá mức độ BMI và ý nghĩa sức khỏe
   - Nhận định về tình trạng cân nặng hiện tại
   - Các nguy cơ sức khỏe tiềm ẩn (nếu có)

2. KHUYẾN NGHỊ DINH DƯỠNG (3-4 điểm cụ thể):
   - Loại thực phẩm nên tăng cường
   - Loại thực phẩm cần hạn chế
   - Khẩu phần ăn phù hợp
   - Thói quen ăn uống lành mạnh

3. KHUYẾN NGHỊ VẬN ĐỘNG (2-3 điểm cụ thể):
   - Loại hình tập luyện phù hợp
   - Tần suất và cường độ
   - Lưu ý khi tập luyện

4. LỜI KHUYÊN TỔNG QUÁT:
   - Mục tiêu sức khỏe ngắn hạn
   - Thay đổi lối sống cần thiết
   - Lời động viên tích cực

Hãy viết bằng giọng văn chuyên nghiệp nhưng gần gũi, dễ hiểu. Tập trung vào giải pháp thực tế và khả thi.
"""

        # Prompt chi tiết cho chế độ ăn uống
        diet_prompt = f"""
Dựa trên thông tin sau, hãy tạo một CHẾ ĐỘ ĂN UỐNG CHI TIẾT trong 1 tuần:
- Giới tính: {data.gender}
- Tuổi: {data.age}
- Chiều cao: {data.height} mét
- Cân nặng: {data.weight} kg
- BMI: {bmi_formatted} - Phân loại: {result['phân_loại_bmi']}
- Tình trạng: {result['dự_đoán']}

YÊU CẦU CHI TIẾT:
1. LƯỢNG CALO KHUYẾN NGHỊ hàng ngày
2. THỰC ĐƠN MẪU 7 NGÀY chi tiết:
   - Bữa sáng: món ăn cụ thể, khẩu phần
   - Bữa trưa: món ăn cụ thể, khẩu phần  
   - Bữa tối: món ăn cụ thể, khẩu phần
   - Bữa phụ (nếu có)
3. NGUYÊN TẮC DINH DƯỠNG:
   - Tỷ lệ protein/carb/fat
   - Loại thực phẩm ưu tiên
   - Thực phẩm cần tránh
4. LỜI KHUYÊN CHUYÊN BIỆT phù hợp với tình trạng {result['dự_đoán']}

Hãy cung cấp thông tin thực tế, dễ áp dụng với người Việt Nam.
"""

        # Prompt chi tiết cho chế độ tập luyện
        exercise_prompt = f"""
Dựa trên thông tin sau, hãy tạo một CHẾ ĐỘ TẬP LUYỆN CHI TIẾT trong 1 tuần:
- Giới tính: {data.gender}
- Tuổi: {data.age}
- Chiều cao: {data.height} mét
- Cân nặng: {data.weight} kg
- BMI: {bmi_formatted} - Phân loại: {result['phân_loại_bmi']}
- Tình trạng: {result['dự_đoán']}

YÊU CẦU CHI TIẾT:
1. LỊCH TẬP 7 NGÀY chi tiết:
   - Thứ 2: bài tập cụ thể, thời gian, cường độ
   - Thứ 3: bài tập cụ thể, thời gian, cường độ
   - ... (cho cả tuần)
2. HƯỚNG DẪN KỸ THUẬT cho các bài tập quan trọng
3. CHẾ ĐỘ NGHỈ NGƠI và phục hồi
4. LƯU Ý AN TOÀN đặc biệt cho người có tình trạng {result['dự_đoán']}
5. MỤC TIÊU THEO TUẦN/THÁNG

Hãy đề xuất các bài tập phù hợp với người Việt, có thể thực hiện tại nhà hoặc phòng gym.
"""

        def get_ai_suggestion(prompt_text: str) -> str:
            """Hàm helper để gọi API OpenAI"""
            try:
                response = client.chat.completions.create(
                    model=settings.openrouter_model,
                    messages=[{"role": "user", "content": prompt_text}],
                    temperature=settings.openrouter_temperature,
                    max_tokens=settings.openrouter_max_tokens,
                    timeout=settings.openrouter_timeout,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"Không thể tạo khuyến nghị: {str(e)}"

        # Gọi cả 3 API để lấy các loại khuyến nghị
        general_analysis = get_ai_suggestion(general_prompt)
        detailed_diet_plan = get_ai_suggestion(diet_prompt)
        detailed_exercise_plan = get_ai_suggestion(exercise_prompt)

        return {
            "prediction": result,
            "general_analysis": general_analysis,
            "detailed_diet_plan": detailed_diet_plan,
            "detailed_exercise_plan": detailed_exercise_plan
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))