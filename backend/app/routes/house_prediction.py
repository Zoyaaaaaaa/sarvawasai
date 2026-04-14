from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Annotated
import logging
import os
from ..ml_pipeline.house_price.predictor import HousePredictor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/house-prediction", tags=["House Prediction"])

# Initialize predictor lazily
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        try:
            predictor = HousePredictor()
        except Exception as e:
            logging.error(f"Failed to load house prediction artifacts: {e}")
            raise HTTPException(status_code=503, detail="House prediction model not available")
    return predictor

def build_fallback_explanation(insights: Dict, predicted_price: float) -> str:
    """Return a deterministic explanation when LLM is unavailable."""
    location = insights.get('location', 'the selected location')
    area = insights.get('area', 0)
    bedrooms = insights.get('bedrooms', 0)
    amenity_score = insights.get('amenity_score', 0)

    return (
        f"Estimated value for a {bedrooms} BHK, {area} sq ft property in {location} is "
        f"approximately Rs. {predicted_price:,.0f}. "
        f"Pricing is influenced by location demand, unit size, and amenity score ({amenity_score}/13). "
        "This estimate should be treated as indicative and validated against current market listings."
    )


# Initialize LLM only if key is available
google_api_key = os.getenv("GOOGLE_API_KEY")
llm = None
agent = None
if google_api_key:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=google_api_key,
        )
    except Exception as e:
        logging.warning(f"House prediction LLM init failed, continuing without LLM: {e}")
        llm = None

# Global memory saver and last prediction context
memory = MemorySaver()
last_prediction_context = {}

# Tool for agent to access prediction context
def get_prediction_info(query: str) -> str:
    """Get information about the last property prediction."""
    if not last_prediction_context:
        return "No prediction available. Please run a prediction first."
    
    ctx = last_prediction_context
    return f"""Last Prediction:
- Price: ₹{ctx['price']:,.0f}
- Area: {ctx['area']} sq ft
- Location: {ctx['location']}
- Bedrooms: {ctx['bedrooms']} BHK
- Amenities: {ctx['amenity_score']}/13
- New/Resale: {'New' if ctx['new_resale'] == 1 else 'Resale'}
"""

# Create agent with memory when LLM is available
if llm is not None:
    try:
        agent = create_react_agent(
            llm,
            tools=[get_prediction_info],
            checkpointer=memory
        )
    except Exception as e:
        logging.warning(f"House prediction agent init failed, continuing without agent: {e}")
        agent = None

class HouseInput(BaseModel):
    Area: float
    Location: str
    No_of_Bedrooms: int
    New_Resale: int
    Gymnasium: Optional[int] = 0
    Lift_Available: Optional[int] = 0
    Car_Parking: Optional[int] = 0
    Maintenance_Staff: Optional[int] = 0
    Security_24x7: Optional[int] = 0
    Children_Play_Area: Optional[int] = 0
    Clubhouse: Optional[int] = 0
    Intercom: Optional[int] = 0
    Landscaped_Gardens: Optional[int] = 0
    Indoor_Games: Optional[int] = 0
    Gas_Connection: Optional[int] = 0
    Jogging_Track: Optional[int] = 0
    Swimming_Pool: Optional[int] = 0

class FollowUpQuery(BaseModel):
    question: str
    thread_id: Optional[str] = "default"

@router.post("/predict")
async def predict_house_price(data: HouseInput):
    predictor = get_predictor()
    
    input_dict = {
        'Area': data.Area,
        'Location': data.Location,
        'No. of Bedrooms': data.No_of_Bedrooms,
        'New/Resale': data.New_Resale,
        'Gymnasium': data.Gymnasium,
        'Lift Available': data.Lift_Available,
        'Car Parking': data.Car_Parking,
        'Maintenance Staff': data.Maintenance_Staff,
        '24x7 Security': data.Security_24x7,
        "Children's Play Area": data.Children_Play_Area,
        'Clubhouse': data.Clubhouse,
        'Intercom': data.Intercom,
        'Landscaped Gardens': data.Landscaped_Gardens,
        'Indoor Games': data.Indoor_Games,
        'Gas Connection': data.Gas_Connection,
        'Jogging Track': data.Jogging_Track,
        'Swimming Pool': data.Swimming_Pool
    }
    
    try:
        insights = predictor.predict(input_dict)
        predicted_price = insights['predicted_price']
        
        # Store context globally for agent tool
        global last_prediction_context
        last_prediction_context = {
            'price': predicted_price,
            'area': insights['area'],
            'location': insights['location'],
            'bedrooms': insights['bedrooms'],
            'amenity_score': insights['amenity_score'],
            'new_resale': data.New_Resale
        }
        
        # Use agent to generate explanation
        prompt = f"""You are a Mumbai real estate expert. Explain this prediction in 2-3 sentences:
Property: {insights['area']} sq ft, {insights['location']}, {insights['bedrooms']} BHK
Predicted Price: ₹{predicted_price:,.0f}
Amenities: {insights['amenity_score']}/13

Focus on location value and key pricing factors and explain the prediction in the maximum of 4 lines."""

        explanation = None
        if agent is not None:
            try:
                result = agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    {"configurable": {"thread_id": "prediction"}}
                )
                explanation = result["messages"][-1].content

                # Ensure explanation is a string (handle multimodal/structured content)
                if isinstance(explanation, list):
                    explanation = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in explanation])
            except Exception as llm_error:
                logging.warning(f"LLM explanation unavailable, using fallback: {llm_error}")

        if not explanation:
            explanation = build_fallback_explanation(insights, predicted_price)
        
        logging.info(f"PREDICTION: Location={data.Location}, Price={predicted_price}")
        
        return {
            "predicted_price": predicted_price,
            "formatted_price": f"₹{predicted_price:,.2f}",
            "insights": insights,
            "explanation": explanation,
            "stage": "Production with LangGraph Agent" if agent is not None else "Prediction with fallback explanation"
        }
        
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_follow_up(query: FollowUpQuery):
    """Handle follow-up questions with persistent memory"""
    
    if not last_prediction_context:
        raise HTTPException(
            status_code=400,
            detail="No prediction available. Run /predict first."
        )

    if agent is None:
        # Graceful response when LLM is not configured
        price = last_prediction_context.get('price', 0)
        location = last_prediction_context.get('location', 'selected location')
        return {
            "answer": (
                f"Follow-up AI assistant is currently unavailable. Last estimate for {location} is "
                f"Rs. {price:,.0f}. Please configure a valid GOOGLE_API_KEY to enable conversational follow-ups."
            ),
            "question": query.question,
            "thread_id": query.thread_id
        }
    
    try:
        # Agent will use memory from thread_id and can access prediction via tool
        result = agent.invoke(
            {"messages": [HumanMessage(content=f"""You are a Mumbai real estate expert. 
Answer this question about the property in 2-3 sentences max: {query.question}

Use the get_prediction_info tool to access property details if needed.""")]},
            {"configurable": {"thread_id": query.thread_id}}
        )
        
        answer = result["messages"][-1].content
        
        # Ensure answer is a string
        if isinstance(answer, list):
            answer = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in answer])
        
        return {
            "answer": answer,
            "question": query.question,
            "thread_id": query.thread_id
        }
        
    except Exception as e:
        logging.error(f"Follow-up error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-dictionary")
async def get_data_dictionary():
    return {
        "Price": "Target variable, price in INR",
        "Area": "Total area in square feet",
        "Location": "Neighborhood in Mumbai",
        "No. of Bedrooms": "Number of bedrooms (BHK)",
        "New/Resale": "0 for Resale, 1 for New construction",
        "Amenities": "Binary columns for amenities",
        "Amenity_Score": "Sum of all amenity flags (0-13)"
    }