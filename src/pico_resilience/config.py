"""Settings for the resilience interceptors (prefix ``resilience``, zero-config)."""

from dataclasses import dataclass

from pico_ioc import configured


@configured(target="self", prefix="resilience", mapping="tree")
@dataclass
class ResilienceSettings:
    """``enabled: false`` turns every interceptor into a pass-through.
    ``hot_reload`` keeps ``enabled`` live across ``container.refresh_config()``
    and requires an EventBus; set it to false to opt out explicitly."""

    enabled: bool = True
    hot_reload: bool = True
