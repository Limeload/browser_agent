"""
Intent Parser Service
Uses OpenAI GPT-4o for intent parsing with deterministic validation
"""

import asyncio
import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple
import structlog
import openai
from models.schemas import IntentResponse, IntentType, BrowserAction, ActionType
from services.monitoring import MonitoringService

logger = structlog.get_logger()

class IntentParser:
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.openai_client = None
        self.validation_rules = self._load_validation_rules()
        
    async def initialize(self):
        """Initialize OpenAI client"""
        logger.info("Initializing Intent Parser service")
        
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)
            
            logger.info("Intent Parser service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Intent Parser service", error=str(e))
            raise
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load deterministic validation rules"""
        return {
            "navigation": {
                "patterns": [
                    r"go to (.+)",
                    r"navigate to (.+)",
                    r"visit (.+)",
                    r"open (.+)",
                    r"browse to (.+)"
                ],
                "required_entities": ["url"]
            },
            "search": {
                "patterns": [
                    r"search for (.+)",
                    r"find (.+)",
                    r"look for (.+)",
                    r"google (.+)"
                ],
                "required_entities": ["query"]
            },
            "click_action": {
                "patterns": [
                    r"click (.+)",
                    r"press (.+)",
                    r"tap (.+)",
                    r"select (.+)"
                ],
                "required_entities": ["element"]
            },
            "form_filling": {
                "patterns": [
                    r"fill (.+) with (.+)",
                    r"enter (.+) in (.+)",
                    r"type (.+) in (.+)",
                    r"input (.+) into (.+)"
                ],
                "required_entities": ["field", "value"]
            },
            "scroll_action": {
                "patterns": [
                    r"scroll (.+)",
                    r"scroll to (.+)",
                    r"scroll down",
                    r"scroll up"
                ],
                "required_entities": []
            },
            "data_extraction": {
                "patterns": [
                    r"extract (.+)",
                    r"get (.+)",
                    r"find (.+)",
                    r"copy (.+)"
                ],
                "required_entities": ["data_type"]
            }
        }
    
    async def parse_intent(self, transcript: str, session_id: str) -> IntentResponse:
        """Parse intent from transcript using LLM + validation"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Parsing intent", 
                       session_id=session_id,
                       transcript_length=len(transcript))
            
            # Step 1: LLM-based parsing
            llm_result = await self._parse_with_llm(transcript)
            
            # Step 2: Deterministic validation
            validated_result = self._validate_intent(llm_result, transcript)
            
            # Step 3: Generate browser actions
            actions = await self._generate_actions(validated_result, transcript)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "intent_parsing_time",
                processing_time,
                {"session_id": session_id, "intent_type": validated_result["intent_type"]}
            )
            
            response = IntentResponse(
                session_id=session_id,
                intent_type=IntentType(validated_result["intent_type"]),
                confidence=validated_result["confidence"],
                entities=validated_result["entities"],
                raw_text=transcript,
                parsed_actions=actions,
                processing_time=processing_time
            )
            
            logger.info("Intent parsing completed",
                       session_id=session_id,
                       intent_type=validated_result["intent_type"],
                       confidence=validated_result["confidence"],
                       actions_count=len(actions))
            
            return response
            
        except Exception as e:
            logger.error("Intent parsing failed", 
                        error=str(e), 
                        session_id=session_id)
            
            # Record error metric
            await self.monitoring_service.record_metric(
                "intent_parsing_errors",
                1,
                {"session_id": session_id, "error_type": type(e).__name__}
            )
            
            # Return unknown intent on error
            return IntentResponse(
                session_id=session_id,
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=transcript,
                processing_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def _parse_with_llm(self, transcript: str) -> Dict[str, Any]:
        """Parse intent using OpenAI GPT-4o"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        system_prompt = """
        You are an expert intent parser for browser automation. 
        Parse the user's voice command into structured intent data.
        
        Available intent types:
        - navigation: Going to a specific URL or page
        - search: Searching for information
        - click_action: Clicking on elements
        - form_filling: Filling out forms
        - scroll_action: Scrolling on the page
        - data_extraction: Extracting data from pages
        
        Return JSON with:
        {
            "intent_type": "one of the above types",
            "confidence": 0.0-1.0,
            "entities": {
                "url": "for navigation",
                "query": "for search",
                "element": "for click actions",
                "field": "for form filling",
                "value": "for form filling",
                "data_type": "for data extraction"
            }
        }
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this command: {transcript}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON", content=content)
            return {"intent_type": "unknown", "confidence": 0.0, "entities": {}}
        except Exception as e:
            logger.error("LLM parsing failed", error=str(e))
            raise
    
    def _validate_intent(self, llm_result: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """Validate intent using deterministic rules"""
        intent_type = llm_result.get("intent_type", "unknown")
        confidence = llm_result.get("confidence", 0.0)
        entities = llm_result.get("entities", {})
        
        # Check if intent type exists in validation rules
        if intent_type not in self.validation_rules:
            logger.warning("Unknown intent type from LLM", intent_type=intent_type)
            return {
                "intent_type": "unknown",
                "confidence": 0.0,
                "entities": {}
            }
        
        # Apply pattern matching validation
        rules = self.validation_rules[intent_type]
        pattern_matched = False
        
        for pattern in rules["patterns"]:
            if re.search(pattern, transcript.lower()):
                pattern_matched = True
                break
        
        # Adjust confidence based on pattern matching
        if pattern_matched:
            confidence = min(confidence + 0.2, 1.0)
        else:
            confidence = max(confidence - 0.3, 0.0)
        
        # Validate required entities
        required_entities = rules.get("required_entities", [])
        missing_entities = []
        
        for entity in required_entities:
            if entity not in entities or not entities[entity]:
                missing_entities.append(entity)
        
        # Reduce confidence for missing entities
        if missing_entities:
            confidence = max(confidence - 0.2 * len(missing_entities), 0.0)
            logger.warning("Missing required entities", 
                          intent_type=intent_type,
                          missing=missing_entities)
        
        return {
            "intent_type": intent_type,
            "confidence": confidence,
            "entities": entities
        }
    
    async def _generate_actions(self, intent_data: Dict[str, Any], transcript: str) -> List[Dict[str, Any]]:
        """Generate browser actions from parsed intent"""
        intent_type = intent_data["intent_type"]
        entities = intent_data["entities"]
        actions = []
        
        if intent_type == "navigation":
            url = entities.get("url", "")
            if url:
                actions.append({
                    "action_type": "navigate",
                    "url": url,
                    "metadata": {"source": "intent_parser"}
                })
        
        elif intent_type == "search":
            query = entities.get("query", "")
            if query:
                actions.append({
                    "action_type": "type",
                    "selector": "input[name='q'], input[type='search'], #search",
                    "text": query,
                    "metadata": {"source": "intent_parser"}
                })
                actions.append({
                    "action_type": "click",
                    "selector": "button[type='submit'], input[type='submit']",
                    "metadata": {"source": "intent_parser"}
                })
        
        elif intent_type == "click_action":
            element = entities.get("element", "")
            if element:
                actions.append({
                    "action_type": "click",
                    "selector": f"text={element}",
                    "metadata": {"source": "intent_parser"}
                })
        
        elif intent_type == "form_filling":
            field = entities.get("field", "")
            value = entities.get("value", "")
            if field and value:
                actions.append({
                    "action_type": "type",
                    "selector": f"input[name='{field}'], input[placeholder*='{field}']",
                    "text": value,
                    "metadata": {"source": "intent_parser"}
                })
        
        elif intent_type == "scroll_action":
            direction = "down" if "down" in transcript.lower() else "up"
            actions.append({
                "action_type": "scroll",
                "metadata": {"direction": direction, "source": "intent_parser"}
            })
        
        elif intent_type == "data_extraction":
            data_type = entities.get("data_type", "")
            actions.append({
                "action_type": "extract_text",
                "metadata": {"data_type": data_type, "source": "intent_parser"}
            })
        
        return actions
    
    def is_healthy(self) -> bool:
        """Check if intent parser is healthy"""
        try:
            return self.openai_client is not None
        except Exception:
            return False
