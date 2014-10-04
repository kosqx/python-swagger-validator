#!/usr/bin/env python
# -*- coding: utf-8 -*-


DATA = {
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


class SwaggerValidator(object):
    def __init__(self, spec):
        self.spec = spec

    SIMPLE_TYPES = {
        'bool': (bool, ()),
        'string': (basestring, ()),
        'integer': ((int, long), bool),
        'float': ((int, long, float), bool),
    }

    def validate_simple_type(self, type_spec, value):
        type_name = type_spec.get('type', 'string')
        if type_name not in self.SIMPLE_TYPES:
            return None

        type_inc, type_exc = self.SIMPLE_TYPES[type_name]
        if not isinstance(value, type_inc) or isinstance(value, type_exc):
            return [{
                'code': 'type_invalid',
                'msg': 'expected %s got %r' % (type_name, value),
            }]

        result = []

        if type_name == 'string':
            if 'enum' in type_spec and value not in type_spec['enum']:
                result.append({
                    'code': 'type_constraint',
                    'path': ['enum'],
                    'msg': 'expected integer got %r' % value,
                })

        if type_name in ('integer', 'float'):
            if 'minimum' in type_spec and value < float(type_spec['minimum']):
                result.append({
                    'code': 'type_constraint',
                    'path': ['minimum'],
                    'msg': 'expected not less than %r got %r' % (type_spec['maximum'], value),
                })

            if 'maximum' in type_spec and value > float(type_spec['maximum']):
                result.append({
                    'code': 'type_constraint',
                    'path': ['maximum'],
                    'msg': 'expected not more than %r got %r' % (type_spec['maximum'], value),
                })

        return result


    def validate_model(self, model_name, model_instance):
        if model_name not in self.spec['models']:
            return [
                {'code': 'model_missing', 'path': [model_name]},
            ]

        result = []

        model_spec = self.spec['models'][model_name]

        keys = set(model_instance.keys())

        for required_property in model_spec.get('required', []):
            if required_property not in model_instance:
                result.append(
                    {'code': 'property_missing', 'path': [model_name, required_property]},
                )

        declared_properties = set(model_spec.get('properties', {}))

        for undeclared_property in sorted(keys - declared_properties):
            result.append(
                {'code': 'property_undeclared', 'path': [model_name, undeclared_property]},
            )

        for property_name, property_spec in sorted(model_spec.get('properties', {}).items()):
            if property_name not in model_instance:
                continue

            simple_result = self.validate_simple_type(property_spec, model_instance[property_name])
            if simple_result is None:
                pass
            elif simple_result:
                for sr in simple_result:
                    sr['path'] = [model_name, property_name] + sr.get('path', [])
                    result.append(sr)

        return result


def format_errors(errors):
    return [
        {'code': error['code'], 'path': error.get('path', [])}
        for error in errors
    ]


def simple_tests():
    validator = SwaggerValidator(DATA)

    assert format_errors(validator.validate_model('Person', {'name': 'Tom', 'age': 30})) == []

    assert format_errors(validator.validate_model('User', {'name': 'Tom', 'age': 30})) == [{'code': 'model_missing', 'path': ['User']}]

    assert format_errors(validator.validate_model('Person', {'name': 'Tom', 'age': '30'})) == [{'code': 'type_invalid', 'path': ['Person', 'age']}]
    assert format_errors(validator.validate_model('Person', {'name': 44, 'age': 30})) == [{'code': 'type_invalid', 'path': ['Person', 'name']}]
    
    assert format_errors(validator.validate_model('Person', {'name': 'Tom'})) == [{'code': 'property_missing', 'path': ['Person', 'age']}]
    assert format_errors(validator.validate_model('Person', {'age': 30})) == [{'code': 'property_missing', 'path': ['Person', 'name']}]

    assert format_errors(validator.validate_model('Person', {'name': 'Tom', 'age': 30, 'hobby': 'bike'})) == [{'code': 'property_undeclared', 'path': ['Person', 'hobby']}]

    assert format_errors(validator.validate_model('Person', {'name': 'Tom', 'age': 90})) == [{'code': 'type_constraint', 'path': ['Person', 'age', 'maximum']}]
    assert format_errors(validator.validate_model('Person', {'name': 'Tom', 'age': -5})) == [{'code': 'type_constraint', 'path': ['Person', 'age', 'minimum']}]

    assert format_errors(validator.validate_model('Person', {'name': 'Bob', 'age': 30})) == [{'code': 'type_constraint', 'path': ['Person', 'name', 'enum']}]

    assert format_errors(validator.validate_model('Person', {'age': '30', 'hobby': 'bike'})) == [
        {'code': 'property_missing', 'path': ['Person', 'name']},
        {'code': 'property_undeclared', 'path': ['Person', 'hobby']},
        {'code': 'type_invalid', 'path': ['Person', 'age']},
    ]


if __name__ == '__main__':
    simple_tests()

    validator = SwaggerValidator(DATA)
    for i in format_errors(validator.validate_model('Person', {'age': '30', 'hobby': 'bike'})):
        print i
