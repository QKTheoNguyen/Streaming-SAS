import unittest
from evaluation.runner import EvaluationRunner
from evaluation.metrics import calculate_intelligibility, calculate_privacy, calculate_speaker_similarity, calculate_naturalness

class TestEvaluationRunner(unittest.TestCase):

    def test_run_evaluation(self):
        """
        Test that the EvaluationRunner can be instantiated and run without errors.
        """
        # The config loading is currently mocked, so the path is a dummy
        runner = EvaluationRunner(config_path="dummy_config.yaml")
        result = runner.run()
        self.assertTrue(result)

class TestMetrics(unittest.TestCase):

    def test_calculate_intelligibility(self):
        """
        Test that calculate_intelligibility returns a float.
        """
        original_text = "hello world"
        processed_text = "hello wurld"
        wer = calculate_intelligibility(original_text, processed_text)
        self.assertIsInstance(wer, float)

    def test_calculate_privacy(self):
        """
        Test that calculate_privacy returns a float.
        """
        original_audio = b"original audio"
        processed_audio = b"processed audio"
        privacy = calculate_privacy(original_audio, processed_audio)
        self.assertIsInstance(privacy, float)

    def test_calculate_speaker_similarity(self):
        """
        Test that calculate_speaker_similarity returns a float.
        """
        target_voice = b"target voice"
        converted_voice = b"converted voice"
        similarity = calculate_speaker_similarity(target_voice, converted_voice)
        self.assertIsInstance(similarity, float)

    def test_calculate_naturalness(self):
        """
        Test that calculate_naturalness returns a float.
        """
        converted_voice = b"converted voice"
        naturalness = calculate_naturalness(converted_voice)
        self.assertIsInstance(naturalness, float)

if __name__ == '__main__':
    unittest.main()
