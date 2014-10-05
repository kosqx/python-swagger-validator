#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, division, absolute_import, print_function


import re


from swagger_validator import five


class OperationLookup(object):
    def __init__(self, apis):
        self.table = []

        for endpoint in apis:
            for operation in endpoint['operations']:
                self.table.append((
                    operation['method'],
                    self._compile_path(endpoint['path']),
                    operation,
                ))

    @classmethod
    def _compile_path(cls, path):
        parts = re.split('\{(\w+)\}', path)
        regexp = ''.join([
            re.escape(part) if i % 2 == 0 else '(?P<' + part + '>[^/]*)'
            for i, part in enumerate(parts)
        ])
        return re.compile(regexp + '$')

    def get(self, method, path):
        for table_method, table_path, table_result in self.table:
            if method == table_method:
                match = table_path.match(path)
                if match:
                    return table_result, match.groupdict()

        return None, None


class SwaggerValidator(object):
    def __init__(self, spec):
        self.spec = spec
        self.lookup = OperationLookup(spec['apis'])

    SIMPLE_TYPES = {
        'bool': (bool, ()),
        'string': (five.string_types, ()),
        'integer': (five.integer_types, bool),
        'float': (five.integer_types + (float,), bool),
        'array': (list, ()),
    }

    def validate_type(self, type_spec, value):
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
        if type_name == 'array' and 'items' in type_spec:
            for item_index, item_value in enumerate(value):
                item_results = self.validate_type_or_model(type_spec['items'], item_value)
                for ir in item_results:
                    ir['path'] = ['items', str(item_index)] + ir.get('path', [])
                    result.append(ir)

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

            simple_result = self.validate_type(property_spec, model_instance[property_name])
            if simple_result is None:
                pass
            elif simple_result:
                for sr in simple_result:
                    sr['path'] = [model_name, property_name] + sr.get('path', [])
                    result.append(sr)

        return result

    def validate_type_or_model(self, type_spec, value):
        result = self.validate_type(type_spec, value)

        if result is not None:
            return result
        else:
            return self.validate_model(type_spec['type'], value)

    def validate_request(self, request):
        method = request['method'].upper()
        path = request['path']
        operation, path_parameters = self.lookup.get(method, path)

        if operation is None:
            return [
                {'code': 'operation_missing', 'path': [method, path]},
            ]

        # skipping verification - by design
        if 'parameters' not in operation:
            return []

        validation_results = []

        declared_query_params = set(
            parameter_spec['name']
            for parameter_spec in operation['parameters']
            if parameter_spec['paramType'] == 'query'
        )
        for query_param_name in request.get('query', {}):
            if query_param_name not in declared_query_params:
                validation_results.append(
                    {'code': 'parameter_undeclared', 'path': [method, path, 'query', query_param_name]},
                )

        for parameter_spec in operation['parameters']:
            param_type = parameter_spec['paramType']
            param_name = parameter_spec['name']

            if param_type == 'body':
                if param_name in request:
                    pass
                elif parameter_spec.get('required', False):
                    validation_results.append(
                        {'code': 'parameter_missing', 'path': [method, path, 'body', param_name]},
                    )
            elif param_type == 'header':
                if param_name in request.get('headers', {}):
                    pass
                elif parameter_spec.get('required', False):
                    validation_results.append(
                        {'code': 'parameter_missing', 'path': [method, path, 'header', param_name]},
                    )
            elif param_type == 'path':
                if param_name in path_parameters:
                    pass
                else:
                    # 'path' params are always required
                    validation_results.append(
                        {'code': 'parameter_missing', 'path': [method, path, 'path', param_name]},
                    )
            elif param_type == 'query':
                if param_name in request.get('query', {}):
                    pass
                elif parameter_spec.get('required', False):
                    validation_results.append(
                        {'code': 'parameter_missing', 'path': [method, path, 'query', param_name]},
                    )
            else:
                pass  # unsupported

        return validation_results
