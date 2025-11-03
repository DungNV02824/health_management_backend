# app/services/predict_service.py
import joblib
import pandas as pd

class ObesityPredictorComplete:
    def __init__(
        self,
        model_path=r"C:\Machine_learning\Source\be\health_management_backend\models_obesity\obesity_classifier_final.pkl",
        encoder_path=r"C:\Machine_learning\Source\be\health_management_backend\models_obesity\label_encoder.pkl"
    ):
        self.model = joblib.load(model_path)
        self.le = joblib.load(encoder_path)
        self.features = [
            'Gender', 'Age', 'Height', 'Weight', 'BMI', 'BMI_Category_Detailed',
            'family_history_with_overweight', 'FAVC', 'FCVC', 'NCP', 'CAEC',
            'CH2O', 'FAF', 'TUE', 'CALC', 'MTRANS_Calorie',
            'Metabolic_Age', 'Family_Risk_Score', 'Lifestyle_Score', 'Diet_Quality'
        ]
    
    def predict_complete(self, user_inputs: dict):
        # --- DỮ LIỆU NGƯỜI DÙNG NHẬP ---
        age = user_inputs["age"]
        height = user_inputs["height"]
        weight = user_inputs["weight"]
        gender = user_inputs["gender"]
        family_history = user_inputs["family_history"]

        # --- TÍNH TOÁN PHỤ TRỢ ---
        bmi = weight / (height ** 2)
        bmi_cat = self._bmi_category_index(bmi)
        metabolic_age = age * bmi / 10
        family_risk_score = (1 if family_history else 0) * bmi_cat

        # --- DỮ LIỆU BỔ SUNG ---
        faf = user_inputs.get("FAF", 1.0)
        tue = user_inputs.get("TUE", 1.0)
        ncp = user_inputs.get("NCP", 3)
        fcvc = user_inputs.get("FCVC", 2.0)
        ch2o = user_inputs.get("CH2O", 2.0)
        favc = user_inputs.get("FAVC", 0)
        calc = user_inputs.get("CALC", 0)
        caec = user_inputs.get("CAEC", 2)
        mtrans = user_inputs.get("MTRANS_Calorie", 1)

        lifestyle_score = (faf + tue) * ncp
        diet_quality = fcvc + ch2o - (1 if favc else 0)

        input_data = {
            'Gender': 1 if gender.lower() in ['nam', 'male', '1'] else 0,
            'Age': age,
            'Height': height,
            'Weight': weight,
            'BMI': bmi,
            'BMI_Category_Detailed': bmi_cat,
            'family_history_with_overweight': 1 if family_history else 0,
            'FAVC': favc,
            'FCVC': fcvc,
            'NCP': ncp,
            'CAEC': caec,
            'CH2O': ch2o,
            'FAF': faf,
            'TUE': tue,
            'CALC': calc,
            'MTRANS_Calorie': mtrans,
            'Metabolic_Age': metabolic_age,
            'Family_Risk_Score': family_risk_score,
            'Lifestyle_Score': lifestyle_score,
            'Diet_Quality': diet_quality
        }

        df = pd.DataFrame([input_data])
        prediction = self.model.predict(df[self.features])[0]
        confidence = max(self.model.predict_proba(df[self.features])[0])

        return {
            "dự_đoán": self.le.inverse_transform([prediction])[0],
            "độ_tin_cậy": f"{confidence:.1%}",
            "bmi": f"{bmi:.1f}",
            "phân_loại_bmi": self._get_bmi_category(bmi)
        }

    def _bmi_category_index(self, bmi):
        if bmi < 16: return 0
        elif bmi < 17: return 1
        elif bmi < 18.5: return 2
        elif bmi < 25: return 3
        elif bmi < 30: return 4
        elif bmi < 35: return 5
        elif bmi < 40: return 6
        else: return 7

    def _get_bmi_category(self, bmi):
        if bmi < 18.5: return "Thiếu cân"
        elif bmi < 25: return "Bình thường"
        elif bmi < 30: return "Thừa cân"
        elif bmi < 35: return "Béo phì cấp I"
        elif bmi < 40: return "Béo phì cấp II"
        else: return "Béo phì cấp III"
