"""
Serializers for FactCheck requests.
"""

from rest_framework import serializers

VALID_INPUT_TYPES = ["text", "url", "file", "news", "scan"]

class CreateFactCheckSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    type = serializers.ChoiceField(choices=VALID_INPUT_TYPES, default="text")
    metadata = serializers.DictField(required=False, default=dict)
