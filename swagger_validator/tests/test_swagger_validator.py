#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, division, absolute_import, print_function


import pytest


from swagger_validator import SwaggerValidator


SPECIFICATION = {
    "swaggerVersion": 1.2,
    "apiVersion": "1.0.0",
    "basePath": "/",
    "info": {
        "description": "This is Example API used for tests",
        "title": "Example API"
    },
    "apis": [],
    "models": {
        "Person": {
            "description": "Person details",
            "id": "Person",
            "properties": {
                "name": {
                    "description": "Person name",
                    "type": "string",
                    "enum": ["Tom", "Alice"],
                },
                "age": {
                    "description": "Person age",
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 80,
                }
            },
            "required": [
                "name",
                "age"
            ]
        }
    }
}

VALIDATE_MODEL_CASES = [
    ({'name': 'Tom', 'age': 30}, []),

    ({'name': 'Tom', 'age': '30'}, [{'code': 'type_invalid', 'path': ['Person', 'age']}]),
    ({'name': 44, 'age': 30}, [{'code': 'type_invalid', 'path': ['Person', 'name']}]),

    ({'name': 'Tom'}, [{'code': 'property_missing', 'path': ['Person', 'age']}]),
    ({'age': 30}, [{'code': 'property_missing', 'path': ['Person', 'name']}]),

    ({'name': 'Tom', 'age': 30, 'hobby': 'bike'}, [{'code': 'property_undeclared', 'path': ['Person', 'hobby']}]),

    ({'name': 'Tom', 'age': 90}, [{'code': 'type_constraint', 'path': ['Person', 'age', 'maximum']}]),
    ({'name': 'Tom', 'age': -5}, [{'code': 'type_constraint', 'path': ['Person', 'age', 'minimum']}]),

    ({'name': 'Bob', 'age': 30}, [{'code': 'type_constraint', 'path': ['Person', 'name', 'enum']}]),

    ({'age': '30', 'hobby': 'bike'}, [
        {'code': 'property_missing', 'path': ['Person', 'name']},
        {'code': 'property_undeclared', 'path': ['Person', 'hobby']},
        {'code': 'type_invalid', 'path': ['Person', 'age']},
    ]),
]


def format_errors(errors):
    return [
        {'code': error['code'], 'path': error.get('path', [])}
        for error in errors
    ]


@pytest.mark.parametrize(('doc', 'errors'), VALIDATE_MODEL_CASES)
def test_validate_model(doc, errors):
    validator = SwaggerValidator(SPECIFICATION)
    assert format_errors(validator.validate_model('Person', doc)) == errors


def test_validate_missing_model():
    doc = {'name': 'Tom', 'age': 30}
    errors = [{'code': 'model_missing', 'path': ['User']}]
    validator = SwaggerValidator(SPECIFICATION)
    assert format_errors(validator.validate_model('User', doc)) == errors
