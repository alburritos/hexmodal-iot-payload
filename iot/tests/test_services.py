from django.test import SimpleTestCase

from iot.models import Payload
from iot.services import decode_payload_data, evaluate_payload_status


class DecodePayloadDataTests(SimpleTestCase):
    def test_decodes_passing_value(self):
        hex_value, int_value = decode_payload_data("AQ==")
        self.assertEqual(hex_value, "01")
        self.assertEqual(int_value, 1)

    def test_decodes_failing_value(self):
        hex_value, int_value = decode_payload_data("Ag==")
        self.assertEqual(hex_value, "02")
        self.assertEqual(int_value, 2)

    def test_rejects_invalid_base64(self):
        with self.assertRaises(ValueError):
            decode_payload_data("not-valid-base64!")


class EvaluatePayloadStatusTests(SimpleTestCase):
    def test_value_one_is_passing(self):
        self.assertEqual(evaluate_payload_status(1), Payload.Status.PASSING)

    def test_other_values_are_failing(self):
        self.assertEqual(evaluate_payload_status(0), Payload.Status.FAILING)
        self.assertEqual(evaluate_payload_status(2), Payload.Status.FAILING)
