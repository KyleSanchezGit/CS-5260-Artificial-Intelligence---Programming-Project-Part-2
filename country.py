# country.py
from dataclasses import dataclass, field
from typing import Dict, Any
import copy

from resources import ResourceBundle  # assumes ResourceBundle defined elsewhere

@dataclass
class Country:
    """
    Represents a virtual country with a name and a bundle of resources.
    Provides operations to test availability, apply transforms/transfers, and clone itself.
    """
    name: str
    resources: ResourceBundle = field(default_factory=ResourceBundle)

    def has_resources(self, required: ResourceBundle) -> bool:
        """
        Return True if this country's resources cover 'required' bundle.
        """
        return self.resources.has(required)

    def apply_transform(self, transform: Any, scale: int = 1) -> None:
        """
        Apply a TRANSFORM operation to this country.
        'transform' must provide 'inputs' and 'outputs' as ResourceBundle.
        Raises ValueError if inputs are insufficient.
        """
        inputs = transform.scaled_inputs(scale)
        outputs = transform.scaled_outputs(scale)
        if not self.has_resources(inputs):
            raise ValueError(
                f"{self.name} lacks resources for transform {transform.name}"
            )
        # subtract inputs, add outputs
        self.resources.add(inputs, sign=-1)
        self.resources.add(outputs, sign=+1)

    def apply_transfer(self,
                       target: "Country",
                       bundle: ResourceBundle) -> None:
        """
        Transfer resources from self to target.
        Raises ValueError if self lacks the resources to give.
        """
        if not self.has_resources(bundle):
            raise ValueError(
                f"{self.name} cannot transfer {bundle.amounts} to {target.name}"
            )
        self.resources.add(bundle, sign=-1)
        target.resources.add(bundle, sign=+1)

    def clone(self) -> "Country":
        """
        Return a deep copy of this Country, including its nested ResourceBundle.
        """
        return copy.deepcopy(self)

    def __post_init__(self) -> None:
        """
        Ensure the resources field is always a ResourceBundle.
        """
        if not isinstance(self.resources, ResourceBundle):
            raise ValueError("resources must be a ResourceBundle instance")
