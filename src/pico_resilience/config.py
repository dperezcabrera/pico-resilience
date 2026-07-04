"""Settings for the resilience interceptors (prefix ``resilience``, zero-config)."""

from dataclasses import dataclass

from pico_ioc import configured


@configured(target="self", prefix="resilience", mapping="tree")
@dataclass
class ResilienceSettings:
    """``enabled: false`` turns every interceptor into a pass-through."""

    enabled: bool = True
