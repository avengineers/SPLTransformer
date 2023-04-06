from dataclasses import dataclass


@dataclass
class Variant:
    flavor: str
    subsystem: str

    @classmethod
    def from_str(cls, variant: str):
        elements = variant.replace("\\", "/").split("/")
        if len(elements) != 2:
            raise ValueError(
                f"Invalid variant {variant}. The correct variant format is <flavor>/<subsystem>."
            )
        return cls(*elements)

    def __str__(self):
        return self.to_string()

    def to_string(self, delimiter: str = "/") -> str:
        return f"{self.flavor}{delimiter}{self.subsystem}"
