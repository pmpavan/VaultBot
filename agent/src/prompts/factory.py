from typing import Type, Dict, Any, Optional
from .core import BasePrompt
from .vision import VisionAnalyzePrompt, VisionSystemPrompt

class PromptFactory:
    """
    Factory class to instantiate and manage prompts.
    """
    _registry: Dict[str, Type[BasePrompt]] = {
        "vision_analyze": VisionAnalyzePrompt,
        "vision_system": VisionSystemPrompt
    }

    @classmethod
    def register(cls, name: str, prompt_cls: Type[BasePrompt]):
        """
        Registers a new prompt class.
        """
        cls._registry[name] = prompt_cls

    @classmethod
    def create(cls, name: str, **kwargs) -> BasePrompt:
        """
        Creates an instance of the requested prompt.
        """
        if name not in cls._registry:
            raise ValueError(f"Prompt '{name}' is not registered.")
        
        prompt_cls = cls._registry[name]
        return prompt_cls(**kwargs)

    @classmethod
    def get_class(cls, name: str) -> Optional[Type[BasePrompt]]:
        """
        Returns the class for a given prompt name.
        """
        return cls._registry.get(name)
