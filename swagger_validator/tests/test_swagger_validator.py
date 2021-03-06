#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, division, absolute_import, print_function


import copy


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
                    "type": "Person",
                    "parameters": [
                        {
                            "name": "body",
                            "paramType": "body",
                            "required": True,
                            "type": "Person",
                        },
                        {
                            "name": "X-VERSION",
                            "paramType": "header",
                            "required": True,
                            "type": "integer",
                        },
                        {
                            "name": "note_id",
                            "paramType": "path",
                            "type": "integer",
                        },
                        {
                            "name": "force",
                            "paramType": "query",
                            "type": "integer",
                            "required": True,
                        },
                        {
                            "name": "hint",
                            "paramType": "query",
                            "type": "integer",
                            "required": False,
                        },
                    ],
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
                },
                "hobbies": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "pets": {
                    "type": "array",
                    "items": {
                        "type": "Pet",
                    },
                },
            },
            "required": [
                "name",
                "age"
            ],
        },
        "Pet": {
            "id": "Pet",
            "properties": {
                "species": {
                    "type": "string",
                },
                "name": {
                    "type": "string",
                },
            },
        },
    },
}


def format_errors(errors):
    return [
        {'code': error['code'], 'path': error.get('path', [])}
        for error in errors
    ]


MERGE_CASES = [
    ({}, []),

    (
        {
            'models': {
                'Pet': {}
            }
        },
        [{'code': 'merge_model_conflict', 'path': ['Pet']}]
    ),
    (
        {
            'models': {
                "Pet": {
                    "id": "Pet",
                    "properties": {
                        "species": {
                            "type": "string",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                },
            },
        },
        []
    ),

    (
        {
            "apis": [
                {
                    "operations": [
                        {
                            "method": "GET",
                            "nickname": "merge_test_get",
                        },
                    ],
                    "path": "/merge/test/"
                },
            ],
        },
        []
    ),
    (
        {
            "apis": [
                {
                    "operations": [
                        {
                            "method": "GET",
                            "nickname": "merge_test_get",
                        },
                    ],
                    "path": "/info/"
                },
            ],
        },
        [{'code': 'merge_apis_conflict', 'path': ['/info/']}]
    ),
]


@pytest.mark.parametrize(('spec', 'errors'), MERGE_CASES)
def test_merge(spec, errors):
    validator = SwaggerValidator(copy.deepcopy(SPECIFICATION))
    assert validator.merge(spec) == errors


def test_merge_api():
    validator = SwaggerValidator(copy.deepcopy(SPECIFICATION))
    request = {'method': 'GET', 'path': '/merge/test/'}

    assert validator.validate_request(request) == [{'code': 'operation_missing', 'path': ['GET', '/merge/test/']}]
    validator.merge({
        "apis": [
            {
                "operations": [
                    {
                        "method": "GET",
                        "nickname": "merge_test_get",
                    },
                ],
                "path": "/merge/test/"
            },
        ],
    })
    assert validator.validate_request(request) == []


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

    ({'name': 'Tom', 'age': 30, 'hobbies': []}, []),
    ({'name': 'Tom', 'age': 30, 'hobbies': ['fishing']}, []),
    ({'name': 'Tom', 'age': 30, 'pets': []}, []),
    ({'name': 'Tom', 'age': 30, 'pets': [{'species': 'cat', 'name': 'Purr'}]}, []),

    ({'name': 'Tom', 'age': 30, 'pets': [{'species': 8472, 'name': 'Purr'}]}, [
        {'code': 'type_invalid', 'path': ['Person', 'pets', '0', 'Pet', 'species']}
    ]),
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


VALIDATE_TYPE_CASES = [
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        0,
        [],
    ),
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        30,
        [],
    ),
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        80,
        [],
    ),
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        -30,
        [{'code': 'type_constraint', 'path': ['minimum']}],
    ),
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        100,
        [{'code': 'type_constraint', 'path': ['maximum']}],
    ),
    (
        {"type": "string", "enum": ["cat", "dog"]},
        "cat",
        [],
    ),
    (
        {"type": "string", "enum": ["cat", "dog"]},
        "fish",
        [{'code': 'type_constraint', 'path': ['enum']}],
    ),

    # array
    (
        {"type": "array"},
        ["foo", "bar"],
        [],
    ),
    (
        {"type": "array"},
        [1, 2],
        [],
    ),
    (
        {"type": "array", "items": {"type": "string"}},
        ["foo", "bar"],
        [],
    ),
    (
        {"type": "array", "items": {"type": "integer"}},
        [1, 2, 1],
        [],
    ),
    (
        {"type": "array", "items": {"type": "integer"}},
        ["foo", "bar"],
        [
            {'code': 'type_invalid', 'path': ['0']},
            {'code': 'type_invalid', 'path': ['1']},
        ],
    ),
    (
        {"type": "array", "items": {"type": "string"}},
        [1],
        [{'code': 'type_invalid', 'path': ['0']}],
    ),

    # array of models
    (
        {"type": "array", "items": {"type": "Person"}},
        [{"name": "Alice", "age": 25}, {"name": "Tom", "age": 30}],
        [],
    ),
    (
        {"type": "array", "items": {"type": "Person"}},
        [{"name": "Alice", "age": 25}, {"name": "Tom", "age": '30'}],
        [{'code': 'type_invalid', 'path': ['1', 'Person', 'age']}],
    ),

]


@pytest.mark.parametrize(('spec', 'value', 'errors'), VALIDATE_TYPE_CASES)
def test_validate_type(spec, value, errors):
    validator = SwaggerValidator(SPECIFICATION)
    assert format_errors(validator.validate_type(spec, value)) == errors


VALIDATE_TYPE_OR_MODEL_CASES = [
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        30,
        [],
    ),
    (
        {"type": "integer", "minimum": 0, "maximum": 80},
        -30,
        [{'code': 'type_constraint', 'path': ['minimum']}],
    ),

    (
        {"type": "Person"},
        {"name": "Alice", "age": 25},
        [],
    ),
    (
        {"type": "Person"},
        {},
        [
            {'code': 'property_missing', 'path': ['Person', 'name']},
            {'code': 'property_missing', 'path': ['Person', 'age']},
        ],
    ),
]


@pytest.mark.parametrize(('spec', 'value', 'errors'), VALIDATE_TYPE_OR_MODEL_CASES)
def test_validate_type_or_model(spec, value, errors):
    validator = SwaggerValidator(SPECIFICATION)
    assert format_errors(validator.validate_type_or_model(spec, value)) == errors


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

    ('GET', '/ignore/me', False, None),
    ('GET', '/note/123/foo', None, None),
    ('GET', '/note/123/ignore', False, None),
]


@pytest.mark.parametrize(
    ('method', 'path', 'nickname', 'params'),
    OPERATION_LOOKUP_CASES
)
def test_operation_lookup(method, path, nickname, params):
    lookup = OperationLookup(
        SPECIFICATION['apis'],
        ignore_endpoints=[r'/ignore/.*', r'/note/\d+/ignore'],
    )
    operation, path_params = lookup.get(method, path)
    if operation is False:
        assert nickname is False
    elif operation is None:
        assert nickname is None
    else:
        assert operation.get('nickname') == nickname
        assert path_params == params


VALIDATE_REQUEST_CASES = [
    ({'method': 'GET', 'path': '/note/123/'}, []),
    ({'method': 'GET', 'path': '/ignore/me/'}, []),
    ({'method': 'POST', 'path': '/note/123/'}, [{'code': 'operation_missing', 'path': ['POST', '/note/123/']}]),
    ({'method': 'GET', 'path': '/missing'}, [{'code': 'operation_missing', 'path': ['GET', '/missing']}]),

    (
        {
            'method': 'PUT',
            'path': '/note/123/',
            'query': {
                "foo": "bar",
            }
        },
        [
            {'code': 'parameter_undeclared', 'path': ['PUT', '/note/123/', 'query', 'foo']},
            {'code': 'parameter_missing', 'path': ['PUT', '/note/123/', 'body']},
            {'code': 'parameter_missing', 'path': ['PUT', '/note/123/', 'header', 'X-VERSION']},
            {'code': 'parameter_missing', 'path': ['PUT', '/note/123/', 'query', 'force']},
        ]
    ),

    (
        {
            'method': 'PUT',
            'path': '/note/123/',
            'body': {},
            'headers': {
                'X-VERSION': 'abc',
            },
            'query': {
                "force": "xyz",
            },
        },
        [
            {'code': 'property_missing', 'path': ['PUT', '/note/123/', 'body', 'Person', 'name']},
            {'code': 'property_missing', 'path': ['PUT', '/note/123/', 'body', 'Person', 'age']},
            {'code': 'type_convert', 'path': ['PUT', '/note/123/', 'header', 'X-VERSION']},
            {'code': 'type_convert', 'path': ['PUT', '/note/123/', 'query', 'force']},
        ]
    ),

    (
        {
            'method': 'PUT',
            'path': '/note/123/',
            'body': {"name": "Alice", "age": 25},
            'headers': {
                'X-VERSION': '123',
            },
            'query': {
                "force": "1",
            },
        },
        []
    ),
]


# for some reason pytest treats 'request' in a special way, which breaks test
@pytest.mark.parametrize(('request_', 'errors'), VALIDATE_REQUEST_CASES)
def test_validate_request(request_, errors):
    validator = SwaggerValidator(
        SPECIFICATION,
        ignore_endpoints=[r'/ignore/.*', r'/note/\d+/ignore'],
    )
    assert validator.validate_request(request_) == errors


VALIDATE_RESPONSE_CASES = [
    ({'method': 'GET', 'path': '/note/123/'}, []),
    ({'method': 'GET', 'path': '/ignore/me/'}, []),
    ({'method': 'POST', 'path': '/note/123/'}, [{'code': 'operation_missing', 'path': ['POST', '/note/123/']}]),
    ({'method': 'GET', 'path': '/missing'}, [{'code': 'operation_missing', 'path': ['GET', '/missing']}]),

    (
        {'method': 'PUT', 'path': '/note/123/', 'data': {}},
        [
            {'code': 'property_missing', 'path': ['PUT', '/note/123/', 'data', 'Person', 'name']},
            {'code': 'property_missing', 'path': ['PUT', '/note/123/', 'data', 'Person', 'age']}
        ]
    ),

    (
        {'method': 'PUT', 'path': '/note/123/', 'data': {"name": "Alice", "age": 25}},
        []
    ),
]


# for some reason pytest treats 'request' in a special way, which breaks test
@pytest.mark.parametrize(('response_', 'errors'), VALIDATE_RESPONSE_CASES)
def test_validate_response(response_, errors):
    validator = SwaggerValidator(
        SPECIFICATION,
        ignore_endpoints=[r'/ignore/.*', r'/note/\d+/ignore'],
    )
    assert validator.validate_response(response_) == errors
