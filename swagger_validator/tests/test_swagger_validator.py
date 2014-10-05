#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, division, absolute_import, print_function


import pytest


from swagger_validator import SwaggerValidator
from swagger_validator.core import OperationLookup


SPECIFICATION = {
    "swaggerVersion": 1.2,
    "apiVersion": "1.0.0",
    "basePath": "/",
    "info": {
        "description": "This is Example API used for tests",
        "title": "Example API"
    },
    "apis": [
        {
            "operations": [
                {
                    "method": "GET",
                    "nickname": "notes_get",
                },
                {
                    "method": "POST",
                    "nickname": "notes_post",
                },
            ],
            "path": "/notes/"
        },
        {
            "operations": [
                {
                    "method": "GET",
                    "nickname": "note_get",
                },
                {
                    "method": "PUT",
                    "nickname": "note_put",
                },
                {
                    "method": "DELETE",
                    "nickname": "note_delete",
                },
            ],
            "path": "/note/{note_id}/"
        },
        {
            "operations": [
                {
                    "method": "GET",
                    "nickname": "info_get",
                },
            ],
            "path": "/info/"
        },
    ],
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


OPERATION_LOOKUP_CASES = [
    ('GET', '/foo/', None, None),

    ('GET', '/info/', 'info_get', {}),
    ('GET', '/foo/info/', None, None),
    ('GET', '/info/bar/', None, None),

    ('GET', '/notes/', 'notes_get', {}),
    ('POST', '/notes/', 'notes_post', {}),

    ('GET', '/note/123/', 'note_get', {'note_id': '123'}),
    ('PUT', '/note/123/', 'note_put', {'note_id': '123'}),
    ('DELETE', '/note/123/', 'note_delete', {'note_id': '123'}),

    ('GET', '/note//', 'note_get', {'note_id': ''}),
    ('GET', '/note/123', None, None),
]


@pytest.mark.parametrize(
    ('method', 'path', 'nickname', 'params'),
    OPERATION_LOOKUP_CASES
)
def test_operation_lookup(method, path, nickname, params):
    lookup = OperationLookup(SPECIFICATION['apis'])
    operation, path_params = lookup.get(method, path)
    if operation is None:
        assert nickname is None
    else:
        assert operation.get('nickname') == nickname
        assert path_params == params


VALIDATE_REQUEST_CASES = [
    ({'method': 'GET', 'path': '/note/123/'}, []),
    ({'method': 'POST', 'path': '/note/123/'}, [{'code': 'operation_missing', 'path': ['POST', '/note/123/']}]),
    ({'method': 'GET', 'path': '/missing'}, [{'code': 'operation_missing', 'path': ['GET', '/missing']}]),
]


# for some reason pytest treats 'request' in a special way, which breaks test
@pytest.mark.parametrize(('request_', 'errors'), VALIDATE_REQUEST_CASES)
def test_validate_request(request_, errors):
    validator = SwaggerValidator(SPECIFICATION)
    assert validator.validate_request(request_) == errors
