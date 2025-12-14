"""
Tests for the Template class and multiple template directories.
"""
import unittest
import os
import tempfile
import shutil
from rupy import Rupy, Template


class TestTemplateClass(unittest.TestCase):
    """Test the Template class for standalone template rendering."""

    def setUp(self):
        """Set up test templates and app."""
        self.app = Rupy()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test templates
        with open(os.path.join(self.temp_dir, "greeting.tpl"), "w") as f:
            f.write("Hello, {{name}}! {{message}}")
        
        with open(os.path.join(self.temp_dir, "user_info.tpl"), "w") as f:
            f.write("<div>User: {{username}}, ID: {{user_id}}</div>")
        
        # Set template directory
        self.app.set_template_directory(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_template_basic_rendering(self):
        """Test basic template rendering with Template class."""
        template = Template(self.app, "greeting.tpl")
        result = template.render({
            "name": "Alice",
            "message": "Welcome to Rupy!"
        })
        self.assertEqual(result, "Hello, Alice! Welcome to Rupy!")

    def test_template_with_numbers(self):
        """Test template rendering with numeric values."""
        template = Template(self.app, "user_info.tpl")
        result = template.render({
            "username": "bob",
            "user_id": 12345
        })
        self.assertIn("bob", result)
        self.assertIn("12345", result)

    def test_template_not_found(self):
        """Test error handling when template file doesn't exist."""
        template = Template(self.app, "nonexistent.tpl")
        with self.assertRaises(RuntimeError) as context:
            template.render({"key": "value"})
        self.assertIn("Failed to read template file", str(context.exception))

    def test_template_invalid_context(self):
        """Test that non-dict context raises TypeError."""
        template = Template(self.app, "greeting.tpl")
        with self.assertRaises(TypeError):
            template.render("not a dict")

    def test_template_property(self):
        """Test template_name property."""
        template = Template(self.app, "greeting.tpl")
        self.assertEqual(template.template_name, "greeting.tpl")


class TestMultipleTemplateDirectories(unittest.TestCase):
    """Test support for multiple template directories."""

    def setUp(self):
        """Set up multiple template directories."""
        self.app = Rupy()
        
        # Create two temporary directories
        self.temp_dir1 = tempfile.mkdtemp()
        self.temp_dir2 = tempfile.mkdtemp()
        
        # Create templates in first directory
        with open(os.path.join(self.temp_dir1, "common.tpl"), "w") as f:
            f.write("Template from dir1: {{value}}")
        
        with open(os.path.join(self.temp_dir1, "unique1.tpl"), "w") as f:
            f.write("Unique to dir1: {{data}}")
        
        # Create templates in second directory
        with open(os.path.join(self.temp_dir2, "unique2.tpl"), "w") as f:
            f.write("Unique to dir2: {{info}}")
        
        # Set up template directories
        self.app.set_template_directory(self.temp_dir1)
        self.app.add_template_directory(self.temp_dir2)

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir1, ignore_errors=True)
        shutil.rmtree(self.temp_dir2, ignore_errors=True)

    def test_get_template_directories(self):
        """Test getting list of template directories."""
        dirs = self.app.get_template_directories()
        self.assertIsInstance(dirs, list)
        self.assertIn(self.temp_dir1, dirs)
        self.assertIn(self.temp_dir2, dirs)
        self.assertEqual(len(dirs), 2)

    def test_add_template_directory(self):
        """Test adding a template directory."""
        temp_dir3 = tempfile.mkdtemp()
        try:
            self.app.add_template_directory(temp_dir3)
            dirs = self.app.get_template_directories()
            self.assertIn(temp_dir3, dirs)
            self.assertEqual(len(dirs), 3)
        finally:
            shutil.rmtree(temp_dir3, ignore_errors=True)

    def test_remove_template_directory(self):
        """Test removing a template directory."""
        self.app.remove_template_directory(self.temp_dir2)
        dirs = self.app.get_template_directories()
        self.assertNotIn(self.temp_dir2, dirs)
        self.assertIn(self.temp_dir1, dirs)

    def test_template_search_first_directory(self):
        """Test that templates are found in the first directory."""
        template = Template(self.app, "common.tpl")
        result = template.render({"value": "test"})
        self.assertIn("Template from dir1", result)
        self.assertIn("test", result)

    def test_template_search_second_directory(self):
        """Test that templates are found in subsequent directories."""
        template = Template(self.app, "unique2.tpl")
        result = template.render({"info": "data"})
        self.assertIn("Unique to dir2", result)
        self.assertIn("data", result)

    def test_template_priority_order(self):
        """Test that first directory has priority when template exists in multiple dirs."""
        # Create same template in both directories
        with open(os.path.join(self.temp_dir2, "common.tpl"), "w") as f:
            f.write("Template from dir2: {{value}}")
        
        template = Template(self.app, "common.tpl")
        result = template.render({"value": "test"})
        # Should use the first directory's version
        self.assertIn("Template from dir1", result)
        self.assertNotIn("Template from dir2", result)

    def test_add_duplicate_directory(self):
        """Test that adding duplicate directory doesn't create duplicates."""
        initial_dirs = self.app.get_template_directories()
        initial_count = len(initial_dirs)
        
        # Try to add the same directory again
        self.app.add_template_directory(self.temp_dir1)
        
        dirs = self.app.get_template_directories()
        # Count should remain the same
        self.assertEqual(len(dirs), initial_count)


class TestTemplateDirectoryConfiguration(unittest.TestCase):
    """Test template directory configuration methods."""

    def test_default_template_directory(self):
        """Test that default template directory is './template'."""
        app = Rupy()
        default_dir = app.get_template_directory()
        self.assertEqual(default_dir, "./template")
        
        # Also check directories list
        dirs = app.get_template_directories()
        self.assertEqual(len(dirs), 1)
        self.assertEqual(dirs[0], "./template")

    def test_set_template_directory_replaces_list(self):
        """Test that set_template_directory replaces the entire list."""
        app = Rupy()
        
        # Add multiple directories (using relative paths for cross-platform compatibility)
        app.add_template_directory("./dir1")
        app.add_template_directory("./dir2")
        dirs = app.get_template_directories()
        self.assertGreater(len(dirs), 1)
        
        # Set new directory should replace all
        app.set_template_directory("./new_dir")
        dirs = app.get_template_directories()
        self.assertEqual(len(dirs), 1)
        self.assertEqual(dirs[0], "./new_dir")
        self.assertEqual(app.get_template_directory(), "./new_dir")


if __name__ == "__main__":
    unittest.main()
