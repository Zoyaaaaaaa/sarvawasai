
import unittest
import sys
import os

# Add the parent directory to sys.path to import from app.routes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.schemes import LanguageDetector, HousingSchemeAdvisor, UserProfile

class TestHousingSchemes(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.detector = LanguageDetector()
        cls.advisor = HousingSchemeAdvisor(enable_tts=False)

    def test_language_detection_hindi(self):
        text = "मुझे आवास योजना के बारे में जानकारी चाहिए"
        lang_key, _ = self.detector.detect_language(text)
        self.assertEqual(lang_key, 'hindi')

    def test_language_detection_english(self):
        text = "I need information about housing schemes"
        lang_key, _ = self.detector.detect_language(text)
        self.assertEqual(lang_key, 'english')

    def test_user_profile(self):
        profile = UserProfile(income="500000", category="EWS", location="Delhi")
        self.assertEqual(profile.category, "EWS")
        profile.update(location="Mumbai")
        self.assertEqual(profile.location, "Mumbai")

    def test_advisor_chat(self):
        session_id = "test_session"
        user_profile = UserProfile(income="3L", category="General", location="Mumbai")
        response = self.advisor.chat("Hello", session_id, user_profile)
        self.assertIn('text', response)
        self.assertTrue(len(response['text']) > 0)

if __name__ == '__main__':
    unittest.main()
