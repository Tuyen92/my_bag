# from logging import Logger
# from types import NoneType, FunctionType
# from xmltodict import parse, unparse

# class DhpdDataMap:
#     '''Serializer class for DHPD specific object values. Handles both
#     serialization and deserialization by using mapping lists as defined in the
#     mapping module.

#     When serializing data to XML, a preset XML template (as text) is expected,
#     serializer will not create extra fields and will raise exception if any of
#     the map fields are missing in the template.
#     '''
#     mapping = None  # List of tuples as described in mapping.py
#     log = None  # Logger instance to emit warnings

#     def __init__(self, mapping):
#         self.mapping = mapping
#         self.log = Logger('DhpdDataMap')

#     def map(self, model):
#         '''Map method expects dict-encoded Django model that matches mapping
#         definition. It will emit xmltodict subtree to be used for XML
#         generation.

#         This function assumes all default/fallback values are already
#         substituted!
#         '''

#         out_data = {}

#         for key, value in self.mapping.items():
#             # Let's trust type defined in the model and ignore that step
#             model_type, xml_type, null_value, transform = value

#             # Special case: there are some hardcoded objects which we do not
#             # store in our model but need to pass into XML. Use None type for
#             # the model to determine that.
#             if model_type is None:
#                 self.log.info(
#                     f'Skipping encoding of field {key}. '
#                     'Will encode hardcoded value {null_value}')
#                 out_data[key] = null_value

#             if xml_type is None:
#                 raise NotImplementedError(
#                     f'Unable to encode field {key}. Unknown XML type.')

#             # We do not expect container data for a serialized model, so noop

#             # Forbid serializing null values unless something better than
#             # None is specified
#             if model[key] is None and null_value is None:
#                 raise ValueError(f'No rule to cast None to XML node for {key}')

#             # Explicitly set null value as instructed and skip processing
#             if model[key] is None:
#                 out_data[key] = null_value
#                 continue

#             # Now, transform model data for XML output
#             # dicts are used for enums other 1:1 data mappings
#             if isinstance(transform, dict):
#                 in_data = transform[model[key]]

#             # Numbers are used for simple linear mathematic conversions.
#             elif isinstance(transform, float):
#                 in_data = model[key] * transform

#             # Functions are used for complex conversion logic, seconf arg tells
#             # is we are mapping value to XML or unmapping it back to model.
#             elif isinstance(transform, FunctionType):
#                 in_data = transform(model[key], True)

#             # Do nothing for None
#             elif isinstance(transform, NoneType):
#                 in_data = model[key]

#             else:
#                 raise ValueError('Unexpected transform object: {transform}')

#             out_data[key] = xml_type(in_data)

#         return out_data



#     def unmap(self, tree):
#         '''Unmap method expects xmltodict subtree with mapped items inside
#         the root element. It will produce python dictionary with normalized
#         data as per specified rules.

#         This assumes XML contains all of the required fields!
#         '''
#         out_data = {}

#         for key, value in self.mapping.items():
#             # Retrieve map values from external definitions
#             model_type, xml_type, null_value, transform = value

#             # Special case, if model type is undefined, do not store this value
#             # at all. When mapping the value from null_value column will be
#             # directly encoded into XML.
#             if model_type is None:
#                 self.log.warning(
#                     f'Skipping decoding of field {key}. '
#                     f'Will hardcode {null_value} when serializing.')
#                 continue

#             # Emit warning on unknown XML object type
#             if xml_type is None:
#                 raise NotImplementedError(
#                     f'Got known XML element with unknown type. '
#                     f'Data: {key}: {tree[key]}')
#                 continue

#             # And on NoneType, unless we expect that
#             if xml_type is not None and isinstance(tree[key], NoneType):
#                 raise ValueError('Null value is not expected for input data.')

#             # If our transform object is a dict, inverse it now.
#             if isinstance(transform, dict):
#                 transform = {v: k for k, v in transform.items()}

#             # First, serialize into known data type from XML, except for None,
#             # None is taken directly to be transformed later, if possible
#             if not isinstance(tree[key], NoneType):
#                 in_data = xml_type(tree[key])
#             else:
#                 in_data = None

#             # Now, transform input data for model
#             # dicts are used to map XML-specific string into model-specific enum
#             # We inversed dict before, so no need to do it now.
#             if isinstance(transform, dict):
#                 in_data = transform[in_data]

#             # Numbers are used for simple mathematic conversions. We calculate
#             # reverse value of the function for unmap method
#             elif isinstance(transform, float):
#                 in_data = in_data / transform

#             # Functions are used for complex conversion logic, second arg tells
#             # is we are mapping value to XML or unmapping it back to model.
#             elif isinstance(transform, FunctionType):
#                 in_data = transform(tree[key], False)

#             # Do nothing for None
#             elif isinstance(transform, NoneType):
#                 in_data = tree[key]

#             else:
#                 raise NotImplemented('Unexpected transform method: {transform}')

#             # Finally, cast and store output
#             out_data[key] = model_type(in_data)

#         return out_data


# class DhpdSerializer:
#     ''' Class to handle serialization and deserialization of XML documents used
#     within DHPD-Webclient application.

#     Following cases are supported:
#     1. Unserialize Input XML (as string) into xmltodict dictionary
#     2. Serialize Input data into XML from xmltodict dictionary
#     3. Unserialize Output XML (as string) into xmltodict dictionary
#     '''

#     @staticmethod
#     def unserialize_input(xml):
#         pass

#     @staticmethod
#     def serialize_input(data):
#         pass

#     @staticmethod
#     def unserialize_output(xml):
#         pass
