from typing import Iterable

from pydantic import create_model

__all__ = ("Serializer",)

ALL = ("__all__",)
EMPTY = tuple()


class Serializer:
    """
    Class, which can get Pydantic serializers (BaseModel classes) to your
    SQLAlchemy tables.

    Can be used in 2 types:
        - as decorator:
                @Serializer().add
                class Model(Base):
                    ...
            it automatically adds attribute `Serializer` to your SQLAlchemy model.

        - as method of class:
                class Model(Base):
                    ...
                Serializer().from_orm(Model)
            it returns BaseModel serializer, which you can use in other places.

    In initialization, you can get parameters:
        - include_fields - fields, which should be in Pydantic BaseModel
        - exclude_fields - fields, which shouldn't be in Pydantic BaseModel

        If none of these parameters was set, Serializer would add all fields
        from SQLAlchemy table (exclude relationship, especially)

        Set both of these parameters raise AttributeError.
    """

    def __init__(self,
                 include_fields: Iterable[str] = ALL,
                 exclude_fields: Iterable[str] = EMPTY):
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields

    def _check_fields(self, cls):
        if not self.include_fields == ALL and not self.exclude_fields == EMPTY:
            raise AttributeError(f"both of parameters `include_fields` and `exclude_fields`"
                                 f"is filled, check only one or nothing")
        for attr in {*self.include_fields, *self.exclude_fields}:
            if all((
                    attr in self.include_fields,
                    attr in self.exclude_fields,
            )):
                raise AttributeError(f"field `{attr}` set in include_fields and "
                                     f"exclude_fields in one time, check it")
            if attr in ALL:
                pass
            elif attr not in cls.__dict__.keys():
                raise AttributeError(f"Table {cls.__tablename__} doesn't have field {attr}")

    def _get_model(self, cls):
        fields = {}
        table = cls.metadata.tables[cls.__tablename__]
        for column in table.columns:
            name = column.name
            if any((
                    self.include_fields == ALL and name not in self.exclude_fields,
                    self.exclude_fields == EMPTY and name in self.include_fields
            )):
                if column.default is None:
                    default = ...
                else:
                    default = column.default.arg
                fields[name] = (column.type.python_type, default)

        model = create_model(
            "ModelSerializer",
            **fields
        )
        return model

    def add(self, cls):
        """
        Add attribute `Serializer` to Table, which associated same Pydantic model with Table
        It is class-decorator function, don't place parameters to this function
        """
        model_serializer = self.from_orm(cls)
        setattr(cls, "Serializer", model_serializer)
        return cls

    def from_orm(self, cls):
        """
        Return Pydantic model, which associated with SQLAlchemy table-class.

        :param cls: SQLAlchemy table-class
        :return: Pydantic model (BaseModel)
        """
        self._check_fields(cls)
        return self._get_model(cls)
