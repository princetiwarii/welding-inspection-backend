"""
AI Service — Google Gemini Integration
Sends panorama image to Gemini, parses defect response,
stores results in DB, uploads marked image to S3.
"""
import json
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import google.generativeai as genai
import httpx

from app.core.config import settings
from app.models.models import (
    Inspection, InspectionImage, AIResult, Defect,
    ImageType, InspectionStatus, OverallResult, DefectSeverity
)

genai.configure(api_key=settings.GEMINI_API_KEY)


WELD_INSPECTION_PROMPT = """
You are an expert welding quality inspector AI.
Analyze this panoramic weld image carefully and detect ALL visible welding defects.

Return your response ONLY as valid JSON with this exact structure:
{
  "overall_status": "Pass" or "Fail",
  "total_length_analyzed_mm": <number or null>,
  "defects": [
    {
      "type": "<defect type>",
      "severity": "Low" or "Medium" or "High",
      "description": "<description>",
      "accuracy": <number 0-100>,
      "length_mm": <number or null>,
      "depth_mm": <number or null>,
      "width_mm": <number or null>,
      "count": <number or null>,
      "position": "<position description or null>",
      "die": "<null or description>"
    }
  ]
}

Defect types to detect:
- Undercut, Underfill, Excess Reinforcement, Spatter,
  Blowhole, Lag Length, Porosity, Crack, Overlap, Burn Through

Rules:
- overall_status is "Fail" if ANY defect is High severity
- overall_status is "Pass" if all defects are Low or no defects found
- Return empty defects array [] if weld looks good
- accuracy is your confidence percentage (0-100)
- Be precise and conservative in your assessment
"""


class AIService:

    @staticmethod
    async def process_inspection(db: AsyncSession, inspection_id: str):
        """
        Main entry point — called after inspection is submitted.
        Fetches panorama, sends to Gemini, stores results.
        """
        # 1. Get inspection
        insp_result = await db.execute(
            select(Inspection).where(Inspection.inspection_id == inspection_id)
        )
        inspection = insp_result.scalar_one_or_none()
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # 2. Get panorama image URL
        img_result = await db.execute(
            select(InspectionImage).where(
                InspectionImage.inspection_id == inspection_id,
                InspectionImage.image_type == ImageType.PANORAMA,
            )
        )
        panorama = img_result.scalar_one_or_none()
        if not panorama:
            raise HTTPException(status_code=400, detail="No panorama image found")

        # 3. Create AI result record (status=Processing)
        ai_result = AIResult(
            inspection_id=inspection_id,
            status="Processing",
            processing_started_at=datetime.utcnow(),
            gemini_model_used=settings.GEMINI_MODEL,
        )
        db.add(ai_result)
        inspection.status = InspectionStatus.AI_PROCESSING
        await db.flush()

        try:
            # 4. Download image bytes from S3 URL
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(panorama.s3_url)
                image_bytes = resp.content
                image_mime = panorama.mime_type or "image/jpeg"

            # 5. Call Gemini API
            start_time = time.time()
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            gemini_response = model.generate_content([
                WELD_INSPECTION_PROMPT,
                {"mime_type": image_mime, "data": image_bytes}
            ])
            duration = time.time() - start_time

            # 6. Parse response
            raw_text = gemini_response.text.strip()
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            parsed = json.loads(raw_text)

            # 7. Store results
            defects_data = parsed.get("defects", [])
            overall = parsed.get("overall_status", "Fail")
            total_length = parsed.get("total_length_analyzed_mm")

            ai_result.raw_gemini_response = parsed
            ai_result.status = "Completed"
            ai_result.overall_status = OverallResult.PASS if overall == "Pass" else OverallResult.FAIL
            ai_result.total_defects_found = len(defects_data)
            ai_result.total_length_analyzed_mm = total_length
            ai_result.processing_completed_at = datetime.utcnow()
            ai_result.processing_duration_seconds = round(duration, 2)

            # 8. Store each defect
            for d in defects_data:
                severity_map = {"Low": DefectSeverity.LOW, "Medium": DefectSeverity.MEDIUM, "High": DefectSeverity.HIGH}
                defect = Defect(
                    ai_result_id=ai_result.id,
                    defect_type=d.get("type", "Unknown"),
                    severity=severity_map.get(d.get("severity", "Low"), DefectSeverity.LOW),
                    description=d.get("description"),
                    ai_accuracy_pct=d.get("accuracy"),
                    length_mm=d.get("length_mm"),
                    depth_mm=d.get("depth_mm"),
                    width_mm=d.get("width_mm"),
                    count=d.get("count"),
                    position=d.get("position"),
                    die=d.get("die"),
                )
                db.add(defect)

            # 9. Update inspection status
            inspection.status = InspectionStatus.COMPLETED
            inspection.overall_result = ai_result.overall_status
            inspection.completed_at = datetime.utcnow()

        except json.JSONDecodeError as e:
            ai_result.status = "Failed"
            inspection.status = InspectionStatus.FAILED
            raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            ai_result.status = "Failed"
            inspection.status = InspectionStatus.FAILED
            raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

        await db.flush()
        return ai_result
