import unittest
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ocr_scripts.pan_ocr import ExtractDetails

class TestPanOCR(unittest.TestCase):
    def setUp(self):
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_images_dir = os.path.join(current_dir, 'test_images')
        if not os.path.exists(self.test_images_dir):
            os.makedirs(self.test_images_dir)
        
        # Copy sample PAN card to test_images if it exists
        sample_pan = os.path.join(current_dir, 'pancard_try.jpeg')
        if os.path.exists(sample_pan):
            import shutil
            shutil.copy2(sample_pan, os.path.join(self.test_images_dir, 'old_format_pan.jpg'))
    
    def test_old_format_pan(self):
        """Test extraction from old format PAN card"""
        image_path = os.path.join(self.test_images_dir, 'old_format_pan.jpg')
        if not os.path.exists(image_path):
            self.skipTest("Test image not available")
        
        result = ExtractDetails(image_path)
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result['name'], str)
            self.assertIsInstance(result['father_name'], str)
            self.assertGreater(len(result['name']), 0)
            self.assertGreater(len(result['father_name']), 0)
    
    def test_new_format_pan(self):
        """Test extraction from new format PAN card"""
        image_path = os.path.join(self.test_images_dir, 'new_format_pan.jpg')
        if not os.path.exists(image_path):
            self.skipTest("Test image not available")
            
        result = ExtractDetails(image_path)
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result['name'], str)
            self.assertIsInstance(result['father_name'], str)
            self.assertGreater(len(result['name']), 0)
            self.assertGreater(len(result['father_name']), 0)
            if 'pan_number' in result:
                self.assertRegex(result['pan_number'], r'^[A-Z]{5}[0-9]{4}[A-Z]$')
            if 'dob' in result:
                self.assertRegex(result['dob'], r'^\d{2}[/-]\d{2}[/-]\d{4}$')
    
    def test_hindi_text_pan(self):
        """Test extraction with Hindi text present"""
        image_path = os.path.join(self.test_images_dir, 'hindi_pan.jpg')
        if not os.path.exists(image_path):
            self.skipTest("Test image not available")
            
        result = ExtractDetails(image_path)
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result['name'], str)
            self.assertIsInstance(result['father_name'], str)
    
    def test_poor_quality_image(self):
        """Test extraction from poor quality image"""
        image_path = os.path.join(self.test_images_dir, 'poor_quality_pan.jpg')
        if not os.path.exists(image_path):
            self.skipTest("Test image not available")
            
        result = ExtractDetails(image_path)
        self.assertIsNotNone(result)
        if result and 'pan_number' in result:
            self.assertRegex(result['pan_number'], r'^[A-Z]{5}[0-9]{4}[A-Z]$')
    
    def test_invalid_image(self):
        """Test handling of invalid image"""
        result = ExtractDetails('nonexistent.jpg')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 