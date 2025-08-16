"""Tests for functions, classes, and methods of the types submodule."""

import pytest
from pydantic import BaseModel, Field, ValidationError

from igem_registry_api.types import partial


def test_partial_model_creation() -> None:
    """Test that the `partial` function creates a partial model."""

    class OriginalModel(BaseModel):
        field1: int = Field(..., title="Field 1")
        field2: str = Field(..., title="Field 2")

    @partial
    class PartialModel(OriginalModel): ...

    # Ensure the partial model has the same fields as the original
    assert set(PartialModel.model_fields.keys()) == set(
        OriginalModel.model_fields.keys(),
    )

    # Ensure all fields in the partial model are optional
    assert PartialModel.model_fields["field1"].default is None
    assert PartialModel.model_fields["field2"].default is None

    # Test creating an instance of the partial model with no fields
    instance = PartialModel()  # pyright: ignore[reportCallIssue]
    assert instance.field1 is None
    assert instance.field2 is None

    # Test creating an instance of the partial model with some fields
    instance = PartialModel(field1=1)  # pyright: ignore[reportCallIssue]
    assert instance.field1 == 1
    assert instance.field2 is None

    # Test creating an instance of the partial model with all fields
    instance = PartialModel(field1=1, field2="test")
    assert instance.field1 == 1
    assert instance.field2 == "test"


def test_partial_model_validation() -> None:
    """Test that the `partial` function retains field validation."""

    class OriginalModel(BaseModel):
        field1: int = Field(..., ge=0, title="Field 1")
        field2: str = Field(..., min_length=3, title="Field 2")

    @partial
    class PartialModel(OriginalModel): ...

    # Test valid data
    instance = PartialModel(field1=1, field2="abc")
    assert instance.field1 == 1
    assert instance.field2 == "abc"

    # Test invalid data for field1
    with pytest.raises(ValidationError):
        PartialModel(field1=-1)  # pyright: ignore[reportCallIssue]

    # Test invalid data for field2
    with pytest.raises(ValidationError):
        PartialModel(field2="ab")  # pyright: ignore[reportCallIssue]
