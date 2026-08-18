# Mixed unit and integration tests in one suite
# Problem: test_publish_event_to_kafka makes a real outbound Kafka call (integration test)
# should not be in the unit test suite

import pytest
from unittest.mock import MagicMock
import kafka

class TestEventPublisher:
    @pytest.fixture
    def publisher(self):
        """Event publisher with stubbed Kafka producer."""
        return EventPublisher(
            producer=MagicMock(),
            logger=MagicMock()
        )

    def test_publish_creates_message_dict(self, publisher):
        """When publish_event is called, the message dict includes timestamp."""
        result = publisher.publish_event({"type": "order", "id": 123})
        assert "timestamp" in result
        assert result["type"] == "order"

    def test_publish_event_to_kafka(self, publisher):
        """VIOLATION: This is an integration test, not a unit test.
        It publishes a real message to a live Kafka cluster, violating test isolation."""
        # Real Kafka connection — should be removed or moved to integration suite
        real_kafka = kafka.KafkaProducer(bootstrap_servers=['localhost:9092'])
        real_kafka.send('events-topic', {'type': 'order', 'id': 456})
        real_kafka.flush()
        # Assertion checks real Kafka, not the EventPublisher behaviour
        # This defeats the purpose of unit testing

    def test_logger_is_called_on_publish(self, publisher):
        """When publish_event is called, the logger is invoked."""
        publisher.publish_event({"type": "user", "id": 789})
        publisher.logger.info.assert_called()
