"""
Mock LLM provider for testing and development.
Returns predictable responses for testing purposes.
"""

import logging
import time
from typing import Dict, Any
from .base_provider import BaseLLMProvider
from i18n import _


class MockLLMProvider(BaseLLMProvider):
    """Mock provider that returns predefined responses."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.response_delay = self.config.get('response_delay', 0.5)  # Simulate network delay
        self.responses = {
            'continue_scene': self._generate_continue_scene_response,
            'default': self._generate_default_response
        }
    
    def initialize(self) -> bool:
        """Initialize mock provider."""
        self.logger.info("Initializing mock LLM provider")
        self._initialized = True
        return True
    
    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response based on prompt content."""
        if not self._initialized:
            self.initialize()
        
        # Simulate processing time
        time.sleep(self.response_delay)
        
        # Determine response type based on prompt content
        response_type = self._detect_task_type(prompt)
        generator = self.responses.get(response_type, self.responses['default'])
        
        response = generator(prompt, **kwargs)
        
        self.logger.debug(f"Generated mock response for {response_type}: {response[:50]}...")
        return response
    
    def _detect_task_type(self, prompt: str) -> str:
        """Detect task type from prompt content."""
        prompt_lower = prompt.lower()
        
        if 'continue' in prompt_lower and 'scene' in prompt_lower:
            return 'continue_scene'
        
        return 'default'
    
    def _generate_continue_scene_response(self, prompt: str, **kwargs) -> str:
        """Generate mock response for continue scene task."""
        # Detect language from prompt or use Polish as default for Pisarz
        is_polish = self._detect_polish_language(prompt)
        
        if is_polish:
            responses = [
                "Maria spojrzała przez okno na padający deszcz. Krople spływały po szybie, "
                "tworząc małe strumyczki, które wydawały się płynąć w rytm jej myśli. "
                "Wiedziała, że musi podjąć decyzję, ale słowa Jana wciąż brzmiały w jej uszach.",
                
                "Stary zegar na ścianie wybił północ. W domu panowała cisza, przerywana jedynie "
                "delikatnym szelestem kartek przewracanych przez wiatr wpadający przez uchylone okno. "
                "To był moment, na który czekała całe życie.",
                
                "Korytarz wydawał się nieskończenie długi. Każdy krok odbijał się echem od kamiennych "
                "ścian, tworząc symfonię niepokoju. Drzwi na końcu były już blisko, ale im bardziej "
                "się zbliżała, tym bardziej rosło jej wahanie."
            ]
        else:
            responses = [
                "Sarah gazed through the window at the falling rain. Droplets traced paths down the glass, "
                "forming small streams that seemed to flow in rhythm with her thoughts. "
                "She knew she had to make a decision, but John's words still echoed in her ears.",
                
                "The old clock on the wall struck midnight. The house was silent, broken only by "
                "the gentle rustling of pages turned by wind coming through the slightly open window. "
                "This was the moment she had been waiting for her entire life.",
                
                "The corridor seemed infinitely long. Each step echoed off the stone walls, "
                "creating a symphony of unease. The door at the end was already close, but the closer "
                "she got, the more her hesitation grew."
            ]
        
        import random
        return random.choice(responses)
    
    def _detect_polish_language(self, prompt: str) -> bool:
        """Detect if prompt suggests Polish language context."""
        polish_indicators = [
            'scena', 'tekst', 'projekt', 'kontekst', 'przez', 'które', 'była', 'jego', 'jej',
            'się', 'że', 'na', 'do', 'z', 'w', 'o', 'za', 'pod', 'nad', 'między',
            'pisanie', 'oparciu', 'scenę', 'naturalne', 'kreatywne'
        ]
        
        english_indicators = [
            'continue', 'writing', 'scene', 'based', 'context', 'naturally', 'creatively',
            'current', 'text', 'summary', 'project', 'the', 'this', 'and', 'was', 'her', 'his'
        ]
        
        prompt_lower = prompt.lower()
        polish_count = sum(1 for word in polish_indicators if word in prompt_lower)
        english_count = sum(1 for word in english_indicators if word in prompt_lower)
        
        # If significantly more Polish than English indicators, assume Polish
        if polish_count > english_count:
            return True
        elif english_count > polish_count:
            return False
        else:
            # Default to Polish for Pisarz (Polish writing app)
            return True
    
    def _generate_default_response(self, prompt: str, **kwargs) -> str:
        """Generate default mock response."""
        is_polish = self._detect_polish_language(prompt)
        
        if is_polish:
            return ("To jest przykładowa odpowiedź z mock providera. "
                    "W rzeczywistej implementacji tutaj byłaby odpowiedź z prawdziwego modelu AI. "
                    "Prompt miał długość: {} znaków.".format(len(prompt)))
        else:
            return ("This is a sample response from the mock provider. "
                    "In a real implementation, this would be a response from an actual AI model. "
                    "The prompt was {} characters long.".format(len(prompt)))
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get mock provider information."""
        info = super().get_provider_info()
        info.update({
            'type': 'mock',
            'response_delay': self.response_delay,
            'available_responses': list(self.responses.keys())
        })
        return info