from typing import Union, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.components.button import ButtonEntityDescription
    from homeassistant.components.fan import FanEntityDescription
    from homeassistant.components.light import LightEntityDescription
    from homeassistant.components.lock import LockEntityDescription
    from homeassistant.components.number import NumberEntityDescription
    from homeassistant.components.select import SelectEntityDescription
    from homeassistant.components.sensor import SensorEntityDescription
    from homeassistant.components.switch import SwitchEntityDescription

    from .button import HonButtonEntity, HonDataArchive, HonDeviceInfo
    from .descriptions.binary_sensor import HonBinarySensorEntityDescription
    from .descriptions.climate import (
        HonACClimateEntityDescription,
        HonClimateEntityDescription,
    )
    from .descriptions.number import (
        HonConfigNumberEntityDescription,
        HonNumberEntityDescription,
    )
    from .descriptions.select import (
        HonConfigSelectEntityDescription,
        HonSelectEntityDescription,
    )
    from .descriptions.sensor import (
        HonSensorEntityDescription,
        HonConfigSensorEntityDescription,
    )
    from .descriptions.switch import (
        HonControlSwitchEntityDescription,
        HonSwitchEntityDescription,
        HonConfigSwitchEntityDescription,
    )

HonButtonType = Union[
    "HonButtonEntity",
    "HonDataArchive",
    "HonDeviceInfo",
]

HonEntityDescription = Union[
    "HonBinarySensorEntityDescription",
    "HonControlSwitchEntityDescription",
    "HonSwitchEntityDescription",
    "HonConfigSwitchEntityDescription",
    "HonSensorEntityDescription",
    "HonConfigSelectEntityDescription",
    "HonConfigNumberEntityDescription",
    "HonACClimateEntityDescription",
    "HonClimateEntityDescription",
    "HonNumberEntityDescription",
    "HonSelectEntityDescription",
    "HonConfigSensorEntityDescription",
    "FanEntityDescription",
    "LightEntityDescription",
    "LockEntityDescription",
    "ButtonEntityDescription",
    "SwitchEntityDescription",
    "SensorEntityDescription",
    "SelectEntityDescription",
    "NumberEntityDescription",
]

HonOptionEntityDescription = Union[
    "HonConfigSelectEntityDescription",
    "HonSelectEntityDescription",
    "HonConfigSensorEntityDescription",
    "HonSensorEntityDescription",
]

T = TypeVar(
    "T",
    "HonBinarySensorEntityDescription",
    "HonControlSwitchEntityDescription",
    "HonSwitchEntityDescription",
    "HonConfigSwitchEntityDescription",
    "HonSensorEntityDescription",
    "HonConfigSelectEntityDescription",
    "HonConfigNumberEntityDescription",
    "HonACClimateEntityDescription",
    "HonClimateEntityDescription",
    "HonNumberEntityDescription",
    "HonSelectEntityDescription",
    "HonConfigSensorEntityDescription",
    "FanEntityDescription",
    "LightEntityDescription",
    "LockEntityDescription",
    "ButtonEntityDescription",
    "SwitchEntityDescription",
    "SensorEntityDescription",
    "SelectEntityDescription",
    "NumberEntityDescription",
)
