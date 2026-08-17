from homeassistant.components.button import ButtonEntityDescription

BUTTONS: dict[str, tuple[ButtonEntityDescription, ...]] = {
    "IH": (
        ButtonEntityDescription(
            key="startProgram",
            name="Start Program",
            icon="mdi:pot-steam",
            translation_key="induction_hob",
        ),
    ),
    "REF": (
        ButtonEntityDescription(
            key="startProgram",
            name="Program Start",
            icon="mdi:play",
            translation_key="start_program",
        ),
        ButtonEntityDescription(
            key="stopProgram",
            name="Program Stop",
            icon="mdi:stop",
            translation_key="stop_program",
        ),
    ),
    "FRE": (
        ButtonEntityDescription(
            key="startProgram",
            name="Program Start",
            icon="mdi:play",
            translation_key="start_program",
        ),
        ButtonEntityDescription(
            key="stopProgram",
            name="Program Stop",
            icon="mdi:stop",
            translation_key="stop_program",
        ),
    ),
}
