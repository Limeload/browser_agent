"""
Planner Service
Manages context, disambiguation, workflow chaining, and safety loops
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
import structlog
from models.schemas import IntentResponse, ExecutionRequest, BrowserAction, ActionType, IntentType
from services.monitoring import MonitoringService

logger = structlog.get_logger()

class Planner:
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates = self._load_workflow_templates()
        self.safety_rules = self._load_safety_rules()
        
    async def initialize(self):
        """Initialize planner service"""
        logger.info("Initializing Planner service")
        
        try:
            # Initialize any required resources
            logger.info("Planner service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Planner service", error=str(e))
            raise
    
    def _load_workflow_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load predefined workflow templates"""
        return {
            "ecommerce_purchase": [
                {"action_type": "navigate", "url": "{product_url}"},
                {"action_type": "click", "selector": "button[data-testid='add-to-cart']"},
                {"action_type": "click", "selector": "a[href*='cart']"},
                {"action_type": "click", "selector": "button[data-testid='checkout']"},
                {"action_type": "type", "selector": "input[name='email']", "text": "{email}"},
                {"action_type": "type", "selector": "input[name='password']", "text": "{password}"},
                {"action_type": "click", "selector": "button[type='submit']"}
            ],
            "form_submission": [
                {"action_type": "navigate", "url": "{form_url}"},
                {"action_type": "type", "selector": "input[name='name']", "text": "{name}"},
                {"action_type": "type", "selector": "input[name='email']", "text": "{email}"},
                {"action_type": "type", "selector": "textarea[name='message']", "text": "{message}"},
                {"action_type": "click", "selector": "button[type='submit']"}
            ],
            "data_extraction": [
                {"action_type": "navigate", "url": "{target_url}"},
                {"action_type": "wait", "wait_time": 2.0},
                {"action_type": "extract_text", "selector": "{target_selector}"},
                {"action_type": "screenshot"}
            ]
        }
    
    def _load_safety_rules(self) -> Dict[str, Any]:
        """Load safety rules for browser automation"""
        return {
            "max_actions_per_session": 50,
            "dangerous_selectors": [
                "input[type='password']",
                "input[name*='password']",
                "input[name*='credit']",
                "input[name*='ssn']",
                "input[name*='social']"
            ],
            "confirmation_required": [
                "navigate",
                "click",
                "type"
            ],
            "rate_limits": {
                "actions_per_minute": 30,
                "navigations_per_minute": 10
            }
        }
    
    async def create_execution_plan(
        self, 
        intent_response: IntentResponse, 
        session_id: str
    ) -> ExecutionRequest:
        """Create execution plan from intent response"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Creating execution plan", 
                       session_id=session_id,
                       intent_type=intent_response.intent_type)
            
            # Get or create session context
            context = self._get_session_context(session_id)
            
            # Apply context management
            enhanced_actions = await self._apply_context_management(
                intent_response.parsed_actions, 
                context
            )
            
            # Apply disambiguation
            disambiguated_actions = await self._apply_disambiguation(
                enhanced_actions, 
                intent_response, 
                context
            )
            
            # Apply workflow chaining
            chained_actions = await self._apply_workflow_chaining(
                disambiguated_actions, 
                intent_response, 
                context
            )
            
            # Apply safety checks
            safe_actions = await self._apply_safety_checks(
                chained_actions, 
                session_id
            )
            
            # Convert to BrowserAction objects
            browser_actions = [
                BrowserAction(**action) for action in safe_actions
            ]
            
            # Update session context
            self._update_session_context(session_id, intent_response, browser_actions)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "planning_time",
                processing_time,
                {"session_id": session_id, "actions_count": len(browser_actions)}
            )
            
            execution_request = ExecutionRequest(
                session_id=session_id,
                actions=browser_actions,
                context=context,
                preferences=self._get_user_preferences(session_id)
            )
            
            logger.info("Execution plan created",
                       session_id=session_id,
                       actions_count=len(browser_actions),
                       processing_time=processing_time)
            
            return execution_request
            
        except Exception as e:
            logger.error("Planning failed", 
                        error=str(e), 
                        session_id=session_id)
            
            # Record error metric
            await self.monitoring_service.record_metric(
                "planning_errors",
                1,
                {"session_id": session_id, "error_type": type(e).__name__}
            )
            
            raise
    
    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create session context"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                "current_url": None,
                "previous_actions": [],
                "extracted_data": {},
                "user_preferences": {},
                "session_start": asyncio.get_event_loop().time(),
                "action_count": 0
            }
        return self.session_contexts[session_id]
    
    async def _apply_context_management(
        self, 
        actions: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply context management to actions"""
        enhanced_actions = []
        
        for action in actions:
            enhanced_action = action.copy()
            
            # Add context metadata
            enhanced_action["metadata"] = enhanced_action.get("metadata", {})
            enhanced_action["metadata"]["context"] = {
                "current_url": context.get("current_url"),
                "session_action_count": context.get("action_count", 0)
            }
            
            # Apply URL resolution for relative URLs
            if action.get("action_type") == "navigate" and action.get("url"):
                url = action["url"]
                if not url.startswith(("http://", "https://")):
                    # Try to resolve relative URL
                    current_url = context.get("current_url")
                    if current_url:
                        # Simple URL resolution (could be enhanced)
                        if url.startswith("/"):
                            base_url = "/".join(current_url.split("/")[:3])
                            enhanced_action["url"] = base_url + url
                        else:
                            enhanced_action["url"] = current_url + "/" + url
            
            enhanced_actions.append(enhanced_action)
        
        return enhanced_actions
    
    async def _apply_disambiguation(
        self, 
        actions: List[Dict[str, Any]], 
        intent_response: IntentResponse, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply disambiguation to actions"""
        disambiguated_actions = []
        
        for action in actions:
            disambiguated_action = action.copy()
            
            # Disambiguate selectors
            if "selector" in action:
                selector = action["selector"]
                
                # If selector is ambiguous, try to make it more specific
                if selector.startswith("text="):
                    # Convert text selector to more specific selector
                    text_value = selector[5:]  # Remove "text=" prefix
                    disambiguated_action["selector"] = f"text='{text_value}'"
                
                # Add fallback selectors
                disambiguated_action["fallback_selectors"] = self._generate_fallback_selectors(
                    selector, 
                    intent_response.intent_type
                )
            
            disambiguated_actions.append(disambiguated_action)
        
        return disambiguated_actions
    
    def _generate_fallback_selectors(self, selector: str, intent_type: IntentType) -> List[str]:
        """Generate fallback selectors for robustness"""
        fallbacks = []
        
        if intent_type == IntentType.CLICK_ACTION:
            # Add common button selectors
            fallbacks.extend([
                f"button:has-text('{selector}')",
                f"a:has-text('{selector}')",
                f"[role='button']:has-text('{selector}')"
            ])
        
        elif intent_type == IntentType.FORM_FILLING:
            # Add common input selectors
            fallbacks.extend([
                f"input[placeholder*='{selector}']",
                f"input[id*='{selector}']",
                f"textarea[name*='{selector}']"
            ])
        
        return fallbacks
    
    async def _apply_workflow_chaining(
        self, 
        actions: List[Dict[str, Any]], 
        intent_response: IntentResponse, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply workflow chaining and prefetch strategies"""
        chained_actions = []
        
        # Check if this matches a known workflow template
        workflow_name = self._identify_workflow(intent_response, context)
        
        if workflow_name and workflow_name in self.workflow_templates:
            # Use workflow template
            template_actions = self.workflow_templates[workflow_name]
            
            # Fill in template variables
            for template_action in template_actions:
                filled_action = self._fill_template_variables(
                    template_action, 
                    intent_response.entities, 
                    context
                )
                chained_actions.append(filled_action)
        else:
            # Use individual actions with prefetch strategies
            chained_actions = actions.copy()
            
            # Add prefetch actions
            prefetch_actions = await self._generate_prefetch_actions(
                actions, 
                intent_response, 
                context
            )
            chained_actions.extend(prefetch_actions)
        
        return chained_actions
    
    def _identify_workflow(self, intent_response: IntentResponse, context: Dict[str, Any]) -> Optional[str]:
        """Identify if intent matches a known workflow"""
        intent_type = intent_response.intent_type
        entities = intent_response.entities
        
        # Simple workflow identification logic
        if intent_type == IntentType.NAVIGATION:
            url = entities.get("url", "")
            if any(keyword in url.lower() for keyword in ["shop", "store", "buy", "cart"]):
                return "ecommerce_purchase"
        
        elif intent_type == IntentType.FORM_FILLING:
            if len(entities) >= 2:  # Has field and value
                return "form_submission"
        
        elif intent_type == IntentType.DATA_EXTRACTION:
            return "data_extraction"
        
        return None
    
    def _fill_template_variables(
        self, 
        template_action: Dict[str, Any], 
        entities: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill template variables in workflow actions"""
        filled_action = template_action.copy()
        
        # Replace template variables
        for key, value in filled_action.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                var_name = value[1:-1]  # Remove { and }
                
                # Try to get value from entities or context
                if var_name in entities:
                    filled_action[key] = entities[var_name]
                elif var_name in context:
                    filled_action[key] = context[var_name]
                else:
                    # Keep original if no replacement found
                    filled_action[key] = value
        
        return filled_action
    
    async def _generate_prefetch_actions(
        self, 
        actions: List[Dict[str, Any]], 
        intent_response: IntentResponse, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prefetch actions for better performance"""
        prefetch_actions = []
        
        # Add wait actions before critical operations
        for action in actions:
            if action.get("action_type") in ["click", "type"]:
                prefetch_actions.append({
                    "action_type": "wait",
                    "wait_time": 1.0,
                    "metadata": {"purpose": "prefetch_wait"}
                })
                break  # Only add one wait action
        
        return prefetch_actions
    
    async def _apply_safety_checks(
        self, 
        actions: List[Dict[str, Any]], 
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Apply safety checks to actions"""
        safe_actions = []
        context = self._get_session_context(session_id)
        
        for action in actions:
            # Check action count limits
            if context["action_count"] >= self.safety_rules["max_actions_per_session"]:
                logger.warning("Maximum actions per session reached", session_id=session_id)
                break
            
            # Check for dangerous selectors
            selector = action.get("selector", "")
            if any(dangerous in selector for dangerous in self.safety_rules["dangerous_selectors"]):
                logger.warning("Dangerous selector detected", 
                              selector=selector, 
                              session_id=session_id)
                # Add confirmation requirement
                action["metadata"] = action.get("metadata", {})
                action["metadata"]["requires_confirmation"] = True
            
            # Check rate limits
            action_type = action.get("action_type")
            if action_type in self.safety_rules["rate_limits"]:
                # Simple rate limiting (could be enhanced with time-based tracking)
                pass
            
            safe_actions.append(action)
            context["action_count"] += 1
        
        return safe_actions
    
    def _update_session_context(
        self, 
        session_id: str, 
        intent_response: IntentResponse, 
        actions: List[BrowserAction]
    ):
        """Update session context with new information"""
        context = self._get_session_context(session_id)
        
        # Update action history
        context["previous_actions"].extend([action.dict() for action in actions])
        
        # Update extracted data if any
        if intent_response.intent_type == IntentType.DATA_EXTRACTION:
            context["extracted_data"].update(intent_response.entities)
        
        # Update current URL if navigation action
        for action in actions:
            if action.action_type == ActionType.NAVIGATE and action.url:
                context["current_url"] = action.url
    
    def _get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences for the session"""
        context = self._get_session_context(session_id)
        return context.get("user_preferences", {})
    
    def is_healthy(self) -> bool:
        """Check if planner is healthy"""
        try:
            return len(self.session_contexts) >= 0  # Simple health check
        except Exception:
            return False
